package main

import (
	"sync"

	"agromesh/gen/go/agropb"
)

// subscriberBuffer limita a memória por assinante lento; ao lotar, mensagens
// são descartadas em vez de travar a ingestão UDP.
const subscriberBuffer = 256

type subscriber struct {
	ch chan *agropb.ServerMessage
}

// Hub distribui leituras e mudanças de topologia para as conexões TCP
// assinantes (dashboard, `client watch`).
type Hub struct {
	mu   sync.Mutex
	subs map[*subscriber]struct{}
}

func NewHub() *Hub {
	return &Hub{subs: map[*subscriber]struct{}{}}
}

func (h *Hub) Subscribe() *subscriber {
	s := &subscriber{ch: make(chan *agropb.ServerMessage, subscriberBuffer)}
	h.mu.Lock()
	h.subs[s] = struct{}{}
	h.mu.Unlock()
	return s
}

func (h *Hub) Unsubscribe(s *subscriber) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if _, ok := h.subs[s]; ok {
		delete(h.subs, s)
		close(s.ch)
	}
}

func (h *Hub) Publish(msg *agropb.ServerMessage) {
	h.mu.Lock()
	defer h.mu.Unlock()
	for s := range h.subs {
		select {
		case s.ch <- msg:
		default:
		}
	}
}
