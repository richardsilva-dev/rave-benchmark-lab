from solo_baseline.telemetry import Telemetry

def test_telemetry_does_not_contain_secret_fields():
    data=Telemetry().to_dict()
    assert "api_key" not in data and "authorization" not in data and data["cost_estimated_usd"] is None
