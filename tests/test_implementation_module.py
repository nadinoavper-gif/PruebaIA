from xau_system.implementation import ImplementationModule


def test_default_payload_shape():
    p = ImplementationModule.default_signal_payload()
    assert "votes" in p
    assert "d1_probs" in p
    assert len(p["votes"]) >= 2


def test_smoke_test_core_ok():
    out = ImplementationModule.smoke_test_core(price=2300)
    assert out.ok is True
    assert "Señal=" in out.detail
