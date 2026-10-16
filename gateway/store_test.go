package main

import (
	"math"
	"path/filepath"
	"testing"
	"time"

	"agromesh/gen/go/agropb"
)

func openTestStore(t *testing.T) *Store {
	t.Helper()
	s, err := OpenStore(filepath.Join(t.TempDir(), "test.db"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { s.Close() })
	return s
}

func save(t *testing.T, s *Store, r *agropb.Reading) {
	t.Helper()
	r.TimestampMs = time.Now().UnixMilli()
	if err := s.SaveReading(r); err != nil {
		t.Fatal(err)
	}
}

func soil(field string, moisture float64, alert bool) *agropb.Reading {
	return &agropb.Reading{SourceId: "solo-" + field, Kind: agropb.SourceKind_SOIL_SENSOR, FieldId: field,
		Metrics: map[string]float64{"moisture_pct": moisture}, IsAlert: alert, AlertMessage: "seco"}
}

func TestDriestFieldAndAlerts(t *testing.T) {
	s := openTestStore(t)
	save(t, s, soil("a", 40, false))
	save(t, s, soil("b", 20, true))
	save(t, s, soil("b", 24, false))

	res, err := s.Query(&agropb.QueryRequest{Kind: agropb.QueryKind_DRIEST_FIELD, WindowMinutes: 5})
	if err != nil {
		t.Fatal(err)
	}
	if res.Rows[0].Label != "b" || res.Rows[0].Values["umidade_media_pct"] != 22 {
		t.Fatalf("talhão mais seco errado: %+v", res.Rows[0])
	}

	res, err = s.Query(&agropb.QueryRequest{Kind: agropb.QueryKind_ALERTS_PER_FIELD, WindowMinutes: 5})
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Rows) != 1 || res.Rows[0].Values["alertas"] != 1 {
		t.Fatalf("contagem de alertas errada: %+v", res.Rows)
	}
}

func TestWaterUsageUsesCounterDelta(t *testing.T) {
	s := openTestStore(t)
	for _, liters := range []float64{100, 130, 160} {
		save(t, s, &agropb.Reading{SourceId: "valvula-a", Kind: agropb.SourceKind_IRRIGATION_VALVE, FieldId: "a",
			Metrics: map[string]float64{"liters_total": liters}})
	}
	res, err := s.Query(&agropb.QueryRequest{Kind: agropb.QueryKind_WATER_USAGE, WindowMinutes: 5})
	if err != nil {
		t.Fatal(err)
	}
	if got := res.Rows[0].Values["litros"]; got != 60 {
		t.Fatalf("consumo = %v, esperado 60", got)
	}
}

func TestTemperatureStats(t *testing.T) {
	s := openTestStore(t)
	for _, temp := range []float64{20, 30} {
		save(t, s, &agropb.Reading{SourceId: "estacao", Kind: agropb.SourceKind_WEATHER_STATION, FieldId: "sede",
			Metrics: map[string]float64{"temperature_c": temp}})
	}
	res, err := s.Query(&agropb.QueryRequest{Kind: agropb.QueryKind_TEMPERATURE_STATS, WindowMinutes: 5})
	if err != nil {
		t.Fatal(err)
	}
	v := res.Rows[0].Values
	if v["media_c"] != 25 || math.Abs(v["desvio_padrao_c"]-5) > 1e-9 {
		t.Fatalf("estatísticas erradas: %+v", v)
	}
}
