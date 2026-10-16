// Package netx reúne a leitura de configuração e a descoberta do IP local do gateway.
package netx

import (
	"net"
	"os"
	"strconv"
)

// Env devolve a variável de ambiente ou o valor padrão.
func Env(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

// EnvInt devolve a variável de ambiente como inteiro ou o valor padrão.
func EnvInt(key string, def int) int {
	n, err := strconv.Atoi(os.Getenv(key))
	if err != nil {
		return def
	}
	return n
}

// LocalIP descobre o IP pelo qual este host é alcançável. Um "dial" UDP não
// envia pacotes; ele só pede ao kernel a rota, o que revela a interface certa.
func LocalIP() string {
	if v := os.Getenv("ADVERTISE_IP"); v != "" {
		return v
	}
	conn, err := net.Dial("udp4", "8.8.8.8:80")
	if err != nil {
		return "127.0.0.1"
	}
	defer conn.Close()
	return conn.LocalAddr().(*net.UDPAddr).IP.String()
}
