package main

import (
	"log"
	"sort"
	"strconv"
	"sync"
	"time"

	"agromesh/gen/go/agropb"
)

// minOfflineTimeout evita marcar como offline uma fonte com intervalo muito curto
// por causa de um único datagrama UDP perdido.
const minOfflineTimeout = 6 * time.Second

type sourceEntry struct {
	info        *agropb.SourceInfo
	lastSeen    time.Time
	lastMetrics map[string]float64
	online      bool
}

// Registry é a visão do Gateway sobre a topologia: quem existe, quem está vivo
// e qual foi a última leitura. Toda mudança de topologia é avisada via onChange.
type Registry struct {
	mu       sync.Mutex
	sources  map[string]*sourceEntry
	onChange func(*agropb.SourceList)
}

func NewRegistry(onChange func(*agropb.SourceList)) *Registry {
	return &Registry{sources: map[string]*sourceEntry{}, onChange: onChange}
}

// Announce registra (ou atualiza) uma fonte que respondeu à descoberta.
func (r *Registry) Announce(info *agropb.SourceInfo) {
	r.mu.Lock()
	e := r.entryLocked(info.SourceId)
	e.info = info
	e.online = true
	e.lastSeen = time.Now()
	snap := r.snapshotLocked()
	r.mu.Unlock()
	log.Printf("[discovery] %s (%s) em %s:%d talhão=%s", info.SourceId, info.Kind, info.Ip, info.GrpcPort, info.FieldId)
	r.onChange(snap)
}

// Observe atualiza a última leitura e avisa quando uma fonte offline volta a enviar.
func (r *Registry) Observe(rd *agropb.Reading) {
	r.mu.Lock()
	e := r.entryLocked(rd.SourceId)
	if e.info == nil {
		// Leitura antes do anúncio (ex.: Gateway reiniciado): registra o mínimo
		// até a próxima rodada de descoberta completar os dados.
		e.info = &agropb.SourceInfo{SourceId: rd.SourceId, Kind: rd.Kind, FieldId: rd.FieldId, Active: true}
	}
	revived := !e.online
	e.online = true
	e.lastSeen = time.Now()
	e.lastMetrics = rd.Metrics
	var snap *agropb.SourceList
	if revived {
		snap = r.snapshotLocked()
	}
	r.mu.Unlock()
	if revived {
		log.Printf("[registry] %s online", rd.SourceId)
		r.onChange(snap)
	}
}

// ApplyValveState reflete no registro o estado devolvido pela válvula via gRPC.
func (r *Registry) ApplyValveState(st *agropb.ValveState) {
	r.mu.Lock()
	e, ok := r.sources[st.SourceId]
	if !ok || e.info == nil {
		r.mu.Unlock()
		return
	}
	e.info.Active = st.Active
	e.info.IntervalS = st.IntervalS
	e.info.Attributes = map[string]string{
		"open":     strconv.FormatBool(st.Open),
		"flow_lpm": strconv.FormatFloat(st.FlowLpm, 'f', 1, 64),
	}
	snap := r.snapshotLocked()
	r.mu.Unlock()
	r.onChange(snap)
}

// Lookup devolve uma cópia das informações de uma fonte.
func (r *Registry) Lookup(id string) (*agropb.SourceInfo, bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	e, ok := r.sources[id]
	if !ok || e.info == nil {
		return nil, false
	}
	return e.info, true
}

// Reap marca como offline as fontes que pararam de enviar dados.
func (r *Registry) Reap(now time.Time) {
	r.mu.Lock()
	changed := false
	for id, e := range r.sources {
		if e.online && now.Sub(e.lastSeen) > offlineTimeout(e.info) {
			e.online = false
			changed = true
			log.Printf("[registry] %s OFFLINE (sem dados há %s)", id, now.Sub(e.lastSeen).Round(time.Second))
		}
	}
	var snap *agropb.SourceList
	if changed {
		snap = r.snapshotLocked()
	}
	r.mu.Unlock()
	if changed {
		r.onChange(snap)
	}
}

func (r *Registry) Snapshot() *agropb.SourceList {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.snapshotLocked()
}

func (r *Registry) entryLocked(id string) *sourceEntry {
	e, ok := r.sources[id]
	if !ok {
		e = &sourceEntry{lastMetrics: map[string]float64{}}
		r.sources[id] = e
	}
	return e
}

func (r *Registry) snapshotLocked() *agropb.SourceList {
	list := &agropb.SourceList{}
	for _, e := range r.sources {
		list.Sources = append(list.Sources, &agropb.SourceStatus{
			Info:        e.info,
			Online:      e.online,
			LastSeenMs:  e.lastSeen.UnixMilli(),
			LastMetrics: e.lastMetrics,
		})
	}
	sort.Slice(list.Sources, func(i, j int) bool {
		return list.Sources[i].Info.SourceId < list.Sources[j].Info.SourceId
	})
	return list
}

func offlineTimeout(info *agropb.SourceInfo) time.Duration {
	t := 3 * time.Duration(info.GetIntervalS()) * time.Second
	if t < minOfflineTimeout {
		return minOfflineTimeout
	}
	return t
}
