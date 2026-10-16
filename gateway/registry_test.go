package main

import (
	"testing"
	"time"

	"agromesh/gen/go/agropb"
)

func TestReapMarksSilentSourceOffline(t *testing.T) {
	changes := 0
	r := NewRegistry(func(*agropb.SourceList) { changes++ })
	r.Announce(&agropb.SourceInfo{SourceId: "valvula-a", IntervalS: 2})

	r.Reap(time.Now().Add(3 * time.Second))
	if !r.Snapshot().Sources[0].Online {
		t.Fatal("fonte não deveria cair antes do timeout mínimo")
	}
	r.Reap(time.Now().Add(10 * time.Second))
	if r.Snapshot().Sources[0].Online {
		t.Fatal("fonte silenciosa deveria estar offline")
	}
	r.Observe(&agropb.Reading{SourceId: "valvula-a"})
	if !r.Snapshot().Sources[0].Online || changes != 3 {
		t.Fatalf("fonte deveria voltar online (mudanças=%d)", changes)
	}
}
