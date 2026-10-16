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

func TestApplyValveStateKeepsPublishedInfoUnchanged(t *testing.T) {
	r := NewRegistry(func(*agropb.SourceList) {})
	r.Announce(&agropb.SourceInfo{SourceId: "valvula-a", Active: true, IntervalS: 2})
	before, _ := r.Lookup("valvula-a")

	r.ApplyValveState(&agropb.ValveState{SourceId: "valvula-a", Active: false, IntervalS: 5, Open: true})

	after, _ := r.Lookup("valvula-a")
	if !before.Active || before.IntervalS != 2 {
		t.Fatalf("snapshot anterior foi alterado: %+v", before)
	}
	if after.Active || after.IntervalS != 5 || after.Attributes["open"] != "true" {
		t.Fatalf("estado novo não aplicado: %+v", after)
	}
}
