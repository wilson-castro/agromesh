package main

import (
	"errors"
	"io"
	"log"
	"net"

	"agromesh/gen/go/agropb"
)

// TCPServer atende Cliente CLI e Dashboard. É o único ponto de entrada externo:
// nenhum cliente fala diretamente com as fontes.
type TCPServer struct {
	registry   *Registry
	store      *Store
	controller *Controller
	hub        *Hub
}

func (s *TCPServer) Serve(ln net.Listener) {
	for {
		conn, err := ln.Accept()
		if err != nil {
			if errors.Is(err, net.ErrClosed) {
				return
			}
			log.Printf("[tcp] accept: %v", err)
			continue
		}
		go s.handle(conn)
	}
}

func (s *TCPServer) handle(conn net.Conn) {
	defer conn.Close()
	log.Printf("[tcp] cliente conectado: %s", conn.RemoteAddr())
	w := &frameWriter{conn: conn}
	var sub *subscriber
	defer func() {
		if sub != nil {
			s.hub.Unsubscribe(sub)
		}
		log.Printf("[tcp] cliente desconectado: %s", conn.RemoteAddr())
	}()
	for {
		req := &agropb.ClientRequest{}
		if err := readFrame(conn, req); err != nil {
			if !errors.Is(err, io.EOF) {
				log.Printf("[tcp] leitura: %v", err)
			}
			return
		}
		if req.GetSubscribe() != nil {
			if sub == nil {
				sub = s.hub.Subscribe()
				go pump(sub, w, conn)
			}
			// O assinante recebe a topologia atual de imediato.
			if err := w.Write(sourcesMessage(req.RequestId, s.registry.Snapshot())); err != nil {
				return
			}
			continue
		}
		if err := w.Write(s.dispatch(req)); err != nil {
			return
		}
	}
}

// pump empurra eventos do Hub para a conexão até ela fechar.
func pump(sub *subscriber, w *frameWriter, conn net.Conn) {
	for msg := range sub.ch {
		if err := w.Write(msg); err != nil {
			conn.Close()
			return
		}
	}
}

func (s *TCPServer) dispatch(req *agropb.ClientRequest) *agropb.ServerMessage {
	switch body := req.Body.(type) {
	case *agropb.ClientRequest_ListSources:
		return sourcesMessage(req.RequestId, s.registry.Snapshot())
	case *agropb.ClientRequest_Command:
		return s.command(req.RequestId, body.Command)
	case *agropb.ClientRequest_Query:
		res, err := s.store.Query(body.Query)
		if err != nil {
			return errorMessage(req.RequestId, err.Error())
		}
		return &agropb.ServerMessage{RequestId: req.RequestId, Body: &agropb.ServerMessage_QueryResult{QueryResult: res}}
	}
	return errorMessage(req.RequestId, "requisição vazia ou desconhecida")
}

func (s *TCPServer) command(id uint64, cmd *agropb.CommandRequest) *agropb.ServerMessage {
	info, ok := s.registry.Lookup(cmd.SourceId)
	if !ok {
		return errorMessage(id, "fonte não encontrada: "+cmd.SourceId)
	}
	state, err := s.controller.Configure(info, cmd.Command)
	result := &agropb.CommandResult{Ok: err == nil, State: state}
	if err != nil {
		result.Message = err.Error()
		log.Printf("[comando] %s: %v", cmd.SourceId, err)
	} else {
		result.Message = "comando aplicado"
		log.Printf("[grpc] %s <- %v", cmd.SourceId, cmd.Command)
		s.registry.ApplyValveState(state)
	}
	return &agropb.ServerMessage{RequestId: id, Body: &agropb.ServerMessage_CommandResult{CommandResult: result}}
}

func sourcesMessage(id uint64, list *agropb.SourceList) *agropb.ServerMessage {
	return &agropb.ServerMessage{RequestId: id, Body: &agropb.ServerMessage_Sources{Sources: list}}
}

func errorMessage(id uint64, msg string) *agropb.ServerMessage {
	return &agropb.ServerMessage{RequestId: id, Body: &agropb.ServerMessage_Error{Error: msg}}
}
