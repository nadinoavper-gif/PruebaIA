from xau_system.ui.dashboard import dashboard_html


def test_dashboard_contains_key_sections():
    html = dashboard_html()
    assert "Panel IA XAU/USD" in html
    assert "Generar señal" in html
    assert "/training/start" in html
    assert "/tradingview/analysis" in html
