from common.pb import pb
from sources.valve.main import ValveModel


def test_apply_changes_only_present_fields() -> None:
    model = ValveModel(source_id="v", field_id="a", flow_lpm=20, interval_s=2)
    model.apply(pb.ValveCommand(open=True))
    assert model.open and model.flow_lpm == 20 and model.interval_s == 2

    model.apply(pb.ValveCommand(flow_lpm=35, interval_s=5))
    assert model.open and model.flow_lpm == 35 and model.interval_s == 5


def test_inactive_valve_has_no_flow() -> None:
    model = ValveModel(source_id="v", field_id="a", open=True, flow_lpm=20)
    model.apply(pb.ValveCommand(active=False))
    assert model.current_flow() == 0.0
