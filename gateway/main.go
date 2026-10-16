// Gateway do AgroMesh: descobre fontes por multicast, ingere telemetria UDP,
// persiste em SQLite, comanda válvulas via gRPC e atende clientes via TCP.
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/protobuf/proto"

	"agromesh/gen/go/agropb"
	"agromesh/internal/netx"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()
	if err := run(ctx); err != nil {
		log.Fatal(err)
	}
}

func run(ctx context.Context) error {
	udpPort := netx.EnvInt("GATEWAY_UDP_PORT", 9100)
	tcpPort := netx.EnvInt("GATEWAY_TCP_PORT", 9200)
	group := netx.Env("MCAST_ADDR", "239.255.10.1:9999")
	discoveryEvery := time.Duration(netx.EnvInt("DISCOVERY_INTERVAL_S", 15)) * time.Second

	store, err := OpenStore(netx.Env("DB_PATH", "agromesh.db"))
	if err != nil {
		return err
	}
	defer store.Close()

	hub := NewHub()
	registry := NewRegistry(func(list *agropb.SourceList) { hub.Publish(sourcesMessage(0, list)) })
	controller := NewController()
	defer controller.Close()

	udpConn, err := net.ListenUDP("udp4", &net.UDPAddr{Port: udpPort})
	if err != nil {
		return fmt.Errorf("udp: %w", err)
	}
	defer udpConn.Close()
	ln, err := net.Listen("tcp", fmt.Sprintf(":%d", tcpPort))
	if err != nil {
		return fmt.Errorf("tcp: %w", err)
	}
	defer ln.Close()

	ip := netx.LocalIP()
	log.Printf("gateway em %s | UDP :%d | TCP :%d | multicast %s", ip, udpPort, tcpPort, group)

	go ingest(udpConn, registry, store, hub)
	go (&TCPServer{registry: registry, store: store, controller: controller, hub: hub}).Serve(ln)
	go reapLoop(ctx, registry)
	go discoveryLoop(ctx, group, &agropb.DiscoveryRequest{GatewayIp: ip, GatewayUdpPort: uint32(udpPort)}, discoveryEvery)

	<-ctx.Done()
	log.Print("encerrando gateway")
	return nil
}

// discoveryLoop envia a requisição de descoberta ao iniciar e periodicamente,
// para que fontes que subirem depois (ou reiniciarem) também sejam encontradas.
func discoveryLoop(ctx context.Context, group string, req *agropb.DiscoveryRequest, every time.Duration) {
	addr, err := net.ResolveUDPAddr("udp4", group)
	if err != nil {
		log.Fatalf("multicast: %v", err)
	}
	conn, err := net.DialUDP("udp4", nil, addr)
	if err != nil {
		log.Fatalf("multicast: %v", err)
	}
	defer conn.Close()
	payload, _ := proto.Marshal(req)
	ticker := time.NewTicker(every)
	defer ticker.Stop()
	for {
		if _, err := conn.Write(payload); err != nil {
			log.Printf("[discovery] envio falhou: %v", err)
		} else {
			log.Printf("[discovery] requisição multicast enviada para %s", group)
		}
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
		}
	}
}

// ingest lê datagramas de anúncio e leitura no único socket UDP do Gateway.
func ingest(conn *net.UDPConn, registry *Registry, store *Store, hub *Hub) {
	buf := make([]byte, 64*1024)
	for {
		n, from, err := conn.ReadFromUDP(buf)
		if err != nil {
			return
		}
		pkt := &agropb.UdpPacket{}
		if err := proto.Unmarshal(buf[:n], pkt); err != nil {
			log.Printf("[udp] pacote inválido de %s: %v", from, err)
			continue
		}
		switch p := pkt.Payload.(type) {
		case *agropb.UdpPacket_Announcement:
			if p.Announcement.Ip == "" {
				p.Announcement.Ip = from.IP.String()
			}
			registry.Announce(p.Announcement)
		case *agropb.UdpPacket_Reading:
			handleReading(p.Reading, registry, store, hub)
		}
	}
}

func handleReading(r *agropb.Reading, registry *Registry, store *Store, hub *Hub) {
	registry.Observe(r)
	if err := store.SaveReading(r); err != nil {
		log.Printf("[sqlite] %v", err)
	}
	if r.IsAlert {
		log.Printf("[ALERTA] %s/%s: %s", r.FieldId, r.SourceId, r.AlertMessage)
	}
	hub.Publish(&agropb.ServerMessage{Body: &agropb.ServerMessage_Reading{Reading: r}})
}

func reapLoop(ctx context.Context, registry *Registry) {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case now := <-ticker.C:
			registry.Reap(now)
		}
	}
}
