"""Regression coverage for safety-critical calculations and API validation."""
import math
import pytest

from holter_af import (
    calculate_mean_rr, calculate_sdnn, calculate_sdann, calculate_af_burden,
    calculate_heart_rate_stats, comprehensive_holter_analysis, detect_pauses,
    rr_to_hr, hr_to_rr, calculate_tachycardia_burden,
)
from agents.base import AuditTrail
from fastapi.testclient import TestClient
from agents.api import app


@pytest.mark.parametrize("invalid", [0, -100, math.nan, math.inf, -math.inf])
def test_invalid_rr_samples_fail_all_entrypoints(invalid):
    for fn in (calculate_mean_rr, calculate_sdnn, calculate_sdann, detect_pauses):
        with pytest.raises(ValueError):
            fn([800, invalid])
    with pytest.raises(ValueError):
        comprehensive_holter_analysis([800, invalid])
    with pytest.raises(ValueError):
        rr_to_hr(invalid)
    with pytest.raises(ValueError):
        hr_to_rr(invalid)


def test_invalid_threshold_fails_closed():
    with pytest.raises(ValueError):
        calculate_tachycardia_burden([800, 810], -1)


def test_mean_hr_weighted_by_time():
    result = calculate_heart_rate_stats([500, 1500])
    assert result["mean_hr"] == 60.0  # 2 beats over 2 seconds


def test_annotations_are_time_weighted_and_typed():
    result = calculate_af_burden([500, 1500], [True, False])
    assert result["af_burden_percent"] == 25.0
    assert result["af_burden_is_estimate"] is False
    with pytest.raises(ValueError):
        calculate_af_burden([500, 1500], [1, 0])


def test_rr_screening_is_not_presented_as_confirmed_af():
    result = calculate_af_burden([500, 800, 1200, 500, 1100, 600])
    assert result["af_burden_is_estimate"] is True
    assert "not an ECG-confirmed" in result["interpretation"]
    report = comprehensive_holter_analysis([500, 800, 1200, 500, 1100, 600])
    assert any("not a diagnosis" in x for x in report["warnings"])


def test_integrity_checks_signatures_not_just_chain_links():
    ledger = AuditTrail(secret_key="test-only-not-production")
    ledger.log("actor", "tier", "ok", {"case": "anonymous"})
    assert ledger.verify_integrity()
    public_copy = ledger.get_trail()
    public_copy[0]["actor"] = "modified external copy"
    assert ledger.verify_integrity()
    ledger.logs[0]["actor"] = "tampered"
    assert not ledger.verify_integrity()


def test_api_analyze_and_reject_invalid_samples():
    client = TestClient(app)
    response = client.post("/api/analyze", json={"rr_intervals_ms": [500, 1500],
                                                  "af_annotations": [True, False]})
    assert response.status_code == 200
    assert response.json()["parameters"]["af_burden"]["af_burden_percent"] == 25.0

    response = client.post("/api/analyze", json={"rr_intervals_ms": [800, 0]})
    assert response.status_code == 422

    response = client.get("/")
    assert response.status_code == 200
    assert "Holter AF Burden Analyzer" in response.text


def test_api_rejects_identifiers_matching_phi_patterns():
    response = TestClient(app).post("/api/audit", json={
        "task_id": "T-1", "target_identifier": "MRN 123456",
        "primary_metric": 2.0
    })
    assert response.status_code == 422
