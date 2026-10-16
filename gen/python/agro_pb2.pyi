from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SourceKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SOURCE_KIND_UNSPECIFIED: _ClassVar[SourceKind]
    SOIL_SENSOR: _ClassVar[SourceKind]
    WEATHER_STATION: _ClassVar[SourceKind]
    IRRIGATION_VALVE: _ClassVar[SourceKind]

class QueryKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    QUERY_KIND_UNSPECIFIED: _ClassVar[QueryKind]
    DRIEST_FIELD: _ClassVar[QueryKind]
    WATER_USAGE: _ClassVar[QueryKind]
    TEMPERATURE_STATS: _ClassVar[QueryKind]
    ALERTS_PER_FIELD: _ClassVar[QueryKind]
SOURCE_KIND_UNSPECIFIED: SourceKind
SOIL_SENSOR: SourceKind
WEATHER_STATION: SourceKind
IRRIGATION_VALVE: SourceKind
QUERY_KIND_UNSPECIFIED: QueryKind
DRIEST_FIELD: QueryKind
WATER_USAGE: QueryKind
TEMPERATURE_STATS: QueryKind
ALERTS_PER_FIELD: QueryKind

class DiscoveryRequest(_message.Message):
    __slots__ = ("gateway_ip", "gateway_udp_port")
    GATEWAY_IP_FIELD_NUMBER: _ClassVar[int]
    GATEWAY_UDP_PORT_FIELD_NUMBER: _ClassVar[int]
    gateway_ip: str
    gateway_udp_port: int
    def __init__(self, gateway_ip: _Optional[str] = ..., gateway_udp_port: _Optional[int] = ...) -> None: ...

class SourceInfo(_message.Message):
    __slots__ = ("source_id", "kind", "field_id", "ip", "grpc_port", "active", "interval_s", "attributes")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    FIELD_ID_FIELD_NUMBER: _ClassVar[int]
    IP_FIELD_NUMBER: _ClassVar[int]
    GRPC_PORT_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_S_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    kind: SourceKind
    field_id: str
    ip: str
    grpc_port: int
    active: bool
    interval_s: int
    attributes: _containers.ScalarMap[str, str]
    def __init__(self, source_id: _Optional[str] = ..., kind: _Optional[_Union[SourceKind, str]] = ..., field_id: _Optional[str] = ..., ip: _Optional[str] = ..., grpc_port: _Optional[int] = ..., active: bool = ..., interval_s: _Optional[int] = ..., attributes: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Reading(_message.Message):
    __slots__ = ("source_id", "kind", "field_id", "timestamp_ms", "metrics", "is_alert", "alert_message")
    class MetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    FIELD_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    IS_ALERT_FIELD_NUMBER: _ClassVar[int]
    ALERT_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    kind: SourceKind
    field_id: str
    timestamp_ms: int
    metrics: _containers.ScalarMap[str, float]
    is_alert: bool
    alert_message: str
    def __init__(self, source_id: _Optional[str] = ..., kind: _Optional[_Union[SourceKind, str]] = ..., field_id: _Optional[str] = ..., timestamp_ms: _Optional[int] = ..., metrics: _Optional[_Mapping[str, float]] = ..., is_alert: bool = ..., alert_message: _Optional[str] = ...) -> None: ...

class UdpPacket(_message.Message):
    __slots__ = ("announcement", "reading")
    ANNOUNCEMENT_FIELD_NUMBER: _ClassVar[int]
    READING_FIELD_NUMBER: _ClassVar[int]
    announcement: SourceInfo
    reading: Reading
    def __init__(self, announcement: _Optional[_Union[SourceInfo, _Mapping]] = ..., reading: _Optional[_Union[Reading, _Mapping]] = ...) -> None: ...

class ValveStateRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ValveCommand(_message.Message):
    __slots__ = ("active", "open", "flow_lpm", "interval_s")
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    OPEN_FIELD_NUMBER: _ClassVar[int]
    FLOW_LPM_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_S_FIELD_NUMBER: _ClassVar[int]
    active: bool
    open: bool
    flow_lpm: float
    interval_s: int
    def __init__(self, active: bool = ..., open: bool = ..., flow_lpm: _Optional[float] = ..., interval_s: _Optional[int] = ...) -> None: ...

class ValveState(_message.Message):
    __slots__ = ("source_id", "field_id", "active", "open", "flow_lpm", "interval_s", "liters_total")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_ID_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    OPEN_FIELD_NUMBER: _ClassVar[int]
    FLOW_LPM_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_S_FIELD_NUMBER: _ClassVar[int]
    LITERS_TOTAL_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    field_id: str
    active: bool
    open: bool
    flow_lpm: float
    interval_s: int
    liters_total: float
    def __init__(self, source_id: _Optional[str] = ..., field_id: _Optional[str] = ..., active: bool = ..., open: bool = ..., flow_lpm: _Optional[float] = ..., interval_s: _Optional[int] = ..., liters_total: _Optional[float] = ...) -> None: ...

class ListSourcesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SubscribeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CommandRequest(_message.Message):
    __slots__ = ("source_id", "command")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    source_id: str
    command: ValveCommand
    def __init__(self, source_id: _Optional[str] = ..., command: _Optional[_Union[ValveCommand, _Mapping]] = ...) -> None: ...

class QueryRequest(_message.Message):
    __slots__ = ("kind", "window_minutes")
    KIND_FIELD_NUMBER: _ClassVar[int]
    WINDOW_MINUTES_FIELD_NUMBER: _ClassVar[int]
    kind: QueryKind
    window_minutes: int
    def __init__(self, kind: _Optional[_Union[QueryKind, str]] = ..., window_minutes: _Optional[int] = ...) -> None: ...

class ClientRequest(_message.Message):
    __slots__ = ("request_id", "list_sources", "command", "query", "subscribe")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    LIST_SOURCES_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_FIELD_NUMBER: _ClassVar[int]
    request_id: int
    list_sources: ListSourcesRequest
    command: CommandRequest
    query: QueryRequest
    subscribe: SubscribeRequest
    def __init__(self, request_id: _Optional[int] = ..., list_sources: _Optional[_Union[ListSourcesRequest, _Mapping]] = ..., command: _Optional[_Union[CommandRequest, _Mapping]] = ..., query: _Optional[_Union[QueryRequest, _Mapping]] = ..., subscribe: _Optional[_Union[SubscribeRequest, _Mapping]] = ...) -> None: ...

class SourceStatus(_message.Message):
    __slots__ = ("info", "online", "last_seen_ms", "last_metrics")
    class LastMetricsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    INFO_FIELD_NUMBER: _ClassVar[int]
    ONLINE_FIELD_NUMBER: _ClassVar[int]
    LAST_SEEN_MS_FIELD_NUMBER: _ClassVar[int]
    LAST_METRICS_FIELD_NUMBER: _ClassVar[int]
    info: SourceInfo
    online: bool
    last_seen_ms: int
    last_metrics: _containers.ScalarMap[str, float]
    def __init__(self, info: _Optional[_Union[SourceInfo, _Mapping]] = ..., online: bool = ..., last_seen_ms: _Optional[int] = ..., last_metrics: _Optional[_Mapping[str, float]] = ...) -> None: ...

class SourceList(_message.Message):
    __slots__ = ("sources",)
    SOURCES_FIELD_NUMBER: _ClassVar[int]
    sources: _containers.RepeatedCompositeFieldContainer[SourceStatus]
    def __init__(self, sources: _Optional[_Iterable[_Union[SourceStatus, _Mapping]]] = ...) -> None: ...

class CommandResult(_message.Message):
    __slots__ = ("ok", "message", "state")
    OK_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    message: str
    state: ValveState
    def __init__(self, ok: bool = ..., message: _Optional[str] = ..., state: _Optional[_Union[ValveState, _Mapping]] = ...) -> None: ...

class QueryRow(_message.Message):
    __slots__ = ("label", "values")
    class ValuesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    LABEL_FIELD_NUMBER: _ClassVar[int]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    label: str
    values: _containers.ScalarMap[str, float]
    def __init__(self, label: _Optional[str] = ..., values: _Optional[_Mapping[str, float]] = ...) -> None: ...

class QueryResult(_message.Message):
    __slots__ = ("kind", "summary", "rows")
    KIND_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    kind: QueryKind
    summary: str
    rows: _containers.RepeatedCompositeFieldContainer[QueryRow]
    def __init__(self, kind: _Optional[_Union[QueryKind, str]] = ..., summary: _Optional[str] = ..., rows: _Optional[_Iterable[_Union[QueryRow, _Mapping]]] = ...) -> None: ...

class ServerMessage(_message.Message):
    __slots__ = ("request_id", "sources", "command_result", "query_result", "reading", "error")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCES_FIELD_NUMBER: _ClassVar[int]
    COMMAND_RESULT_FIELD_NUMBER: _ClassVar[int]
    QUERY_RESULT_FIELD_NUMBER: _ClassVar[int]
    READING_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    request_id: int
    sources: SourceList
    command_result: CommandResult
    query_result: QueryResult
    reading: Reading
    error: str
    def __init__(self, request_id: _Optional[int] = ..., sources: _Optional[_Union[SourceList, _Mapping]] = ..., command_result: _Optional[_Union[CommandResult, _Mapping]] = ..., query_result: _Optional[_Union[QueryResult, _Mapping]] = ..., reading: _Optional[_Union[Reading, _Mapping]] = ..., error: _Optional[str] = ...) -> None: ...
