package main

import (
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"sync"

	"google.golang.org/protobuf/proto"
)

// TCP é um fluxo de bytes sem fronteiras; cada mensagem Protobuf vai precedida
// por 4 bytes big-endian com o seu tamanho.
const maxFrameSize = 4 << 20

func readFrame(r io.Reader, msg proto.Message) error {
	var header [4]byte
	if _, err := io.ReadFull(r, header[:]); err != nil {
		return err
	}
	size := binary.BigEndian.Uint32(header[:])
	if size > maxFrameSize {
		return fmt.Errorf("frame grande demais: %d bytes", size)
	}
	buf := make([]byte, size)
	if _, err := io.ReadFull(r, buf); err != nil {
		return err
	}
	return proto.Unmarshal(buf, msg)
}

// frameWriter serializa escritas: respostas e mensagens de assinatura
// compartilham a mesma conexão e não podem se intercalar no meio de um frame.
type frameWriter struct {
	mu   sync.Mutex
	conn net.Conn
}

func (w *frameWriter) Write(msg proto.Message) error {
	payload, err := proto.Marshal(msg)
	if err != nil {
		return err
	}
	frame := make([]byte, 4+len(payload))
	binary.BigEndian.PutUint32(frame, uint32(len(payload)))
	copy(frame[4:], payload)
	w.mu.Lock()
	defer w.mu.Unlock()
	_, err = w.conn.Write(frame)
	return err
}
