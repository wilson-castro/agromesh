package main

import (
	"context"
	"fmt"
	"net"
	"strconv"
	"sync"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"agromesh/gen/go/agropb"
)

const commandTimeout = 3 * time.Second

// Controller encaminha comandos às fontes controláveis via gRPC, reaproveitando
// uma conexão por endereço (o gRPC reconecta sozinho se a fonte cair e voltar).
type Controller struct {
	mu    sync.Mutex
	conns map[string]*grpc.ClientConn
}

func NewController() *Controller {
	return &Controller{conns: map[string]*grpc.ClientConn{}}
}

func (c *Controller) Configure(info *agropb.SourceInfo, cmd *agropb.ValveCommand) (*agropb.ValveState, error) {
	if info.Kind != agropb.SourceKind_IRRIGATION_VALVE || info.GrpcPort == 0 {
		return nil, fmt.Errorf("%s não é uma fonte controlável", info.SourceId)
	}
	conn, err := c.conn(net.JoinHostPort(info.Ip, strconv.Itoa(int(info.GrpcPort))))
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), commandTimeout)
	defer cancel()
	state, err := agropb.NewIrrigationValveClient(conn).Configure(ctx, cmd)
	if err != nil {
		return nil, fmt.Errorf("gRPC %s: %w", info.SourceId, err)
	}
	return state, nil
}

func (c *Controller) conn(addr string) (*grpc.ClientConn, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if conn, ok := c.conns[addr]; ok {
		return conn, nil
	}
	conn, err := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}
	c.conns[addr] = conn
	return conn, nil
}

func (c *Controller) Close() {
	c.mu.Lock()
	defer c.mu.Unlock()
	for _, conn := range c.conns {
		conn.Close()
	}
}
