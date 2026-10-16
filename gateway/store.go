package main

import (
	"database/sql"
	"fmt"
	"math"
	"time"

	"agromesh/gen/go/agropb"
	_ "modernc.org/sqlite" // driver SQLite em Go puro: dispensa cgo no container
)

const schema = `
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS readings (
	ts_ms     INTEGER NOT NULL,
	source_id TEXT    NOT NULL,
	kind      INTEGER NOT NULL,
	field_id  TEXT    NOT NULL,
	metric    TEXT    NOT NULL,
	value     REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_readings_kind_metric_ts ON readings (kind, metric, ts_ms);
CREATE TABLE IF NOT EXISTS alerts (
	ts_ms     INTEGER NOT NULL,
	source_id TEXT    NOT NULL,
	field_id  TEXT    NOT NULL,
	message   TEXT    NOT NULL
);
`

// Store persiste o histórico em formato "longo" (uma linha por métrica), o que
// permite agregar qualquer grandeza com o mesmo SQL.
type Store struct {
	db *sql.DB
}

func OpenStore(path string) (*Store, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	// SQLite serializa escritas; uma conexão evita "database is locked".
	db.SetMaxOpenConns(1)
	if _, err := db.Exec(schema); err != nil {
		return nil, fmt.Errorf("schema: %w", err)
	}
	return &Store{db: db}, nil
}

func (s *Store) Close() error { return s.db.Close() }

func (s *Store) SaveReading(r *agropb.Reading) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	for metric, value := range r.Metrics {
		if _, err := tx.Exec(`INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?)`,
			r.TimestampMs, r.SourceId, int32(r.Kind), r.FieldId, metric, value); err != nil {
			return err
		}
	}
	if r.IsAlert {
		if _, err := tx.Exec(`INSERT INTO alerts VALUES (?, ?, ?, ?)`,
			r.TimestampMs, r.SourceId, r.FieldId, r.AlertMessage); err != nil {
			return err
		}
	}
	return tx.Commit()
}

// Query executa uma das consultas analíticas sobre a janela pedida.
func (s *Store) Query(q *agropb.QueryRequest) (*agropb.QueryResult, error) {
	window := q.WindowMinutes
	if window == 0 {
		window = 60
	}
	since := time.Now().Add(-time.Duration(window) * time.Minute).UnixMilli()
	switch q.Kind {
	case agropb.QueryKind_DRIEST_FIELD:
		return s.driestField(since, window)
	case agropb.QueryKind_WATER_USAGE:
		return s.waterUsage(since, window)
	case agropb.QueryKind_TEMPERATURE_STATS:
		return s.temperatureStats(since, window)
	case agropb.QueryKind_ALERTS_PER_FIELD:
		return s.alertsPerField(since, window)
	}
	return nil, fmt.Errorf("consulta desconhecida: %v", q.Kind)
}

func (s *Store) driestField(since int64, window uint32) (*agropb.QueryResult, error) {
	rows, err := s.db.Query(`
		SELECT field_id, AVG(value), MIN(value), COUNT(*) FROM readings
		WHERE kind = ? AND metric = 'moisture_pct' AND ts_ms >= ?
		GROUP BY field_id ORDER BY AVG(value) ASC`, int32(agropb.SourceKind_SOIL_SENSOR), since)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	res := &agropb.QueryResult{Kind: agropb.QueryKind_DRIEST_FIELD}
	for rows.Next() {
		var field string
		var avg, min, n float64
		if err := rows.Scan(&field, &avg, &min, &n); err != nil {
			return nil, err
		}
		res.Rows = append(res.Rows, row(field, "umidade_media_pct", avg, "umidade_min_pct", min, "amostras", n))
	}
	res.Summary = "sem leituras de umidade na janela"
	if len(res.Rows) > 0 {
		r := res.Rows[0]
		res.Summary = fmt.Sprintf("Talhão mais seco nos últimos %d min: %s (média %.1f%%)", window, r.Label, r.Values["umidade_media_pct"])
	}
	return res, rows.Err()
}

func (s *Store) waterUsage(since int64, window uint32) (*agropb.QueryResult, error) {
	// liters_total é um contador acumulado na válvula; o consumo na janela é a
	// diferença entre o maior e o menor valor visto por válvula.
	rows, err := s.db.Query(`
		SELECT field_id, SUM(used) FROM (
			SELECT field_id, MAX(value) - MIN(value) AS used FROM readings
			WHERE kind = ? AND metric = 'liters_total' AND ts_ms >= ?
			GROUP BY source_id, field_id)
		GROUP BY field_id ORDER BY 2 DESC`, int32(agropb.SourceKind_IRRIGATION_VALVE), since)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	res := &agropb.QueryResult{Kind: agropb.QueryKind_WATER_USAGE}
	total := 0.0
	for rows.Next() {
		var field string
		var used float64
		if err := rows.Scan(&field, &used); err != nil {
			return nil, err
		}
		total += used
		res.Rows = append(res.Rows, row(field, "litros", used))
	}
	res.Summary = fmt.Sprintf("Consumo de água nos últimos %d min: %.1f L no total", window, total)
	return res, rows.Err()
}

func (s *Store) temperatureStats(since int64, window uint32) (*agropb.QueryResult, error) {
	// SQLite não tem STDDEV; usamos Var(X) = E[X²] - E[X]².
	rows, err := s.db.Query(`
		SELECT source_id, COUNT(*), AVG(value), AVG(value * value), MIN(value), MAX(value) FROM readings
		WHERE kind = ? AND metric = 'temperature_c' AND ts_ms >= ?
		GROUP BY source_id`, int32(agropb.SourceKind_WEATHER_STATION), since)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	res := &agropb.QueryResult{Kind: agropb.QueryKind_TEMPERATURE_STATS, Summary: "sem leituras de temperatura na janela"}
	for rows.Next() {
		var src string
		var n, avg, avgSq, min, max float64
		if err := rows.Scan(&src, &n, &avg, &avgSq, &min, &max); err != nil {
			return nil, err
		}
		std := math.Sqrt(math.Max(0, avgSq-avg*avg))
		res.Rows = append(res.Rows, row(src, "media_c", avg, "desvio_padrao_c", std, "min_c", min, "max_c", max, "amostras", n))
		res.Summary = fmt.Sprintf("Temperatura do ar nos últimos %d min: %.1f °C ± %.2f", window, avg, std)
	}
	return res, rows.Err()
}

func (s *Store) alertsPerField(since int64, window uint32) (*agropb.QueryResult, error) {
	rows, err := s.db.Query(`
		SELECT field_id, COUNT(*) FROM alerts WHERE ts_ms >= ?
		GROUP BY field_id ORDER BY 2 DESC`, since)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	res := &agropb.QueryResult{Kind: agropb.QueryKind_ALERTS_PER_FIELD}
	total := 0.0
	for rows.Next() {
		var field string
		var n float64
		if err := rows.Scan(&field, &n); err != nil {
			return nil, err
		}
		total += n
		res.Rows = append(res.Rows, row(field, "alertas", n))
	}
	res.Summary = fmt.Sprintf("%.0f alertas de solo seco nos últimos %d min", total, window)
	return res, rows.Err()
}

// row monta uma linha de resultado a partir de pares (nome, valor).
func row(label string, kv ...any) *agropb.QueryRow {
	r := &agropb.QueryRow{Label: label, Values: map[string]float64{}}
	for i := 0; i+1 < len(kv); i += 2 {
		r.Values[kv[i].(string)] = kv[i+1].(float64)
	}
	return r
}
