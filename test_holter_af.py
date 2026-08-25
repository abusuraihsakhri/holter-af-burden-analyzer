#!/usr/bin/env python3
"""
Tests for Holter Monitor AF Burden Analyzer.
"""
import math
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from holter_af import (
    rr_to_hr,
    hr_to_rr,
    calculate_mean_rr,
    calculate_sdnn,
    calculate_rmssd,
    calculate_pnn50,
    calculate_heart_rate_stats,
    detect_pauses,
    calculate_tachycardia_burden,
    calculate_bradycardia_burden,
    calculate_irregularity_index,
    calculate_af_burden,
    comprehensive_holter_analysis,
)


# Regular sinus rhythm RR intervals (around 75 bpm, ~800ms)
SINUS_RR = [800, 810, 790, 805, 795, 800, 810, 790, 805, 795,
            800, 810, 790, 805, 795, 800, 810, 790, 805, 795]

# Irregular (AF-like) RR intervals
AF_RR = [600, 900, 500, 1000, 700, 850, 550, 950, 650, 800,
         450, 1100, 700, 600, 900, 500, 1000, 750, 850, 550]


# =============================================================================
# HR/RR Conversion Tests
# =============================================================================

def test_rr_to_hr():
    """800ms -> 75 bpm."""
    assert abs(rr_to_hr(800) - 75.0) < 0.1


def test_rr_to_hr_tachycardia():
    """500ms -> 120 bpm."""
    assert abs(rr_to_hr(500) - 120.0) < 0.1


def test_hr_to_rr():
    """75 bpm -> 800ms."""
    assert abs(hr_to_rr(75) - 800.0) < 0.1


def test_hr_rr_roundtrip():
    for hr in [50, 60, 75, 100, 120]:
        rr = hr_to_rr(hr)
        assert abs(rr_to_hr(rr) - hr) < 0.1


# =============================================================================
# Mean RR Tests
# =============================================================================

def test_mean_rr_uniform():
    """All 800ms -> mean 800ms."""
    rr = [800] * 10
    assert abs(calculate_mean_rr(rr) - 800.0) < 0.01


def test_mean_rr_varied():
    rr = [700, 800, 900]
    assert abs(calculate_mean_rr(rr) - 800.0) < 0.01


# =============================================================================
# SDNN Tests
# =============================================================================

def test_sdnn_uniform():
    """All same RR -> SDNN 0."""
    rr = [800] * 20
    assert calculate_sdnn(rr) < 0.01


def test_sdnn_varied():
    """Varied RR -> SDNN > 0."""
    sdnn = calculate_sdnn(SINUS_RR)
    assert sdnn > 0
    assert sdnn < 50  # Should be small for sinus rhythm


def test_sdnn_af():
    """AF rhythm should have high SDNN."""
    sdnn_af = calculate_sdnn(AF_RR)
    sdnn_sinus = calculate_sdnn(SINUS_RR)
    assert sdnn_af > sdnn_sinus


def test_sdnn_minimum_data():
    """Need at least 2 intervals."""
    try:
        calculate_sdnn([800])
        assert False
    except ValueError:
        pass


# =============================================================================
# RMSSD Tests
# =============================================================================

def test_rmssd_uniform():
    """All same RR -> RMSSD 0."""
    rr = [800] * 20
    assert calculate_rmssd(rr) < 0.01


def test_rmssd_varied():
    """Varied RR -> RMSSD > 0."""
    rmssd = calculate_rmssd(SINUS_RR)
    assert rmssd > 0


def test_rmssd_af_higher():
    """AF rhythm should have higher RMSSD."""
    rmssd_af = calculate_rmssd(AF_RR)
    rmssd_sinus = calculate_rmssd(SINUS_RR)
    assert rmssd_af > rmssd_sinus


# =============================================================================
# pNN50 Tests
# =============================================================================

def test_pnn50_uniform():
    """All same RR -> pNN50 0."""
    rr = [800] * 20
    assert calculate_pnn50(rr) < 0.01


def test_pnn50_with_variability():
    """RR with >50ms differences should give pNN50 > 0."""
    rr = [800, 900, 700, 850, 750]
    pnn50 = calculate_pnn50(rr)
    assert pnn50 > 0


def test_pnn50_range():
    """pNN50 should be 0-100%."""
    pnn50 = calculate_pnn50(AF_RR)
    assert 0 <= pnn50 <= 100


# =============================================================================
# Heart Rate Stats Tests
# =============================================================================

def test_hr_stats_basic():
    stats = calculate_heart_rate_stats(SINUS_RR)
    assert "min_hr" in stats
    assert "max_hr" in stats
    assert "mean_hr" in stats
    assert "resting_hr" in stats
    assert stats["min_hr"] <= stats["mean_hr"] <= stats["max_hr"]


def test_hr_stats_num_beats():
    stats = calculate_heart_rate_stats(SINUS_RR)
    assert stats["num_beats"] == len(SINUS_RR)


def test_hr_stats_resting():
    """Resting HR should be <= min HR."""
    stats = calculate_heart_rate_stats(SINUS_RR)
    assert stats["resting_hr"] <= stats["min_hr"] + 1  # small tolerance


# =============================================================================
# Pause Detection Tests
# =============================================================================

def test_no_pauses():
    pauses = detect_pauses(SINUS_RR)
    assert pauses["num_significant"] == 0
    assert pauses["num_pathological"] == 0


def test_significant_pause():
    rr = [800, 800, 2500, 800, 800]
    pauses = detect_pauses(rr)
    assert pauses["num_significant"] == 1
    assert pauses["num_pathological"] == 0


def test_pathological_pause():
    rr = [800, 800, 3500, 800, 800]
    pauses = detect_pauses(rr)
    assert pauses["num_pathological"] == 1


def test_mixed_pauses():
    rr = [800, 2200, 800, 3500, 800]
    pauses = detect_pauses(rr)
    assert pauses["num_significant"] == 1
    assert pauses["num_pathological"] == 1


def test_longest_pause():
    rr = [800, 2200, 800, 3500, 800]
    pauses = detect_pauses(rr)
    assert pauses["longest_pause_ms"] == 3500


# =============================================================================
# Tachycardia/Bradycardia Burden Tests
# =============================================================================

def test_tachycardia_burden_none():
    """Regular 75 bpm -> no tachycardia."""
    tachy = calculate_tachycardia_burden(SINUS_RR)
    assert tachy["beat_percentage"] == 0


def test_tachycardia_burden_present():
    """Fast RR intervals -> tachycardia."""
    rr = [400, 450, 500, 400, 450]  # 120-150 bpm
    tachy = calculate_tachycardia_burden(rr)
    assert tachy["beat_percentage"] == 100.0


def test_bradycardia_burden_none():
    """Regular 75 bpm -> no bradycardia."""
    brady = calculate_bradycardia_burden(SINUS_RR)
    assert brady["beat_percentage"] == 0


def test_bradycardia_burden_present():
    """Slow RR intervals -> bradycardia."""
    rr = [1500, 1600, 1400, 1500, 1600]  # ~40 bpm
    brady = calculate_bradycardia_burden(rr)
    assert brady["beat_percentage"] == 100.0


# =============================================================================
# Irregularity Index Tests
# =============================================================================

def test_irregularity_regular():
    """Sinus rhythm -> low irregularity."""
    result = calculate_irregularity_index(SINUS_RR)
    assert result["irregular"] is False
    assert result["irregularity_index"] < 0.15


def test_irregularity_af():
    """AF rhythm -> high irregularity."""
    result = calculate_irregularity_index(AF_RR)
    assert result["irregular"] is True
    assert result["irregularity_index"] > 0.15


def test_irregularity_uniform():
    """All same RR -> CV = 0."""
    rr = [800] * 20
    result = calculate_irregularity_index(rr)
    assert result["irregularity_index"] < 0.01


# =============================================================================
# AF Burden Tests
# =============================================================================

def test_af_burden_no_af():
    """Sinus rhythm -> low/zero AF burden."""
    af = calculate_af_burden(SINUS_RR)
    assert af["af_burden_percent"] < 5  # Should be very low


def test_af_burden_with_annotations():
    """With explicit AF annotations."""
    annotations = [True] * 5 + [False] * 15
    rr = [800] * 20
    af = calculate_af_burden(rr, af_annotations=annotations)
    assert abs(af["af_burden_percent"] - 25.0) < 1


def test_af_burden_all_af():
    """All beats annotated as AF -> 100% burden."""
    annotations = [True] * 20
    rr = [800] * 20
    af = calculate_af_burden(rr, af_annotations=annotations)
    assert abs(af["af_burden_percent"] - 100.0) < 0.1


def test_af_burden_monitoring_hours():
    """Check monitoring hours calculation."""
    rr = [1000] * 3600  # 1 hour of 1-second intervals
    af = calculate_af_burden(rr)
    assert abs(af["monitoring_hours"] - 1.0) < 0.01


# =============================================================================
# Comprehensive Analysis Tests
# =============================================================================

def test_comprehensive_sinus():
    """Sinus rhythm comprehensive analysis."""
    result = comprehensive_holter_analysis(SINUS_RR)
    assert "parameters" in result
    assert "heart_rate" in result["parameters"]
    assert "hrv" in result["parameters"]
    assert "pauses" in result["parameters"]
    assert "af_burden" in result["parameters"]


def test_comprehensive_summary():
    """Summary should be a non-empty string."""
    result = comprehensive_holter_analysis(SINUS_RR)
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0


def test_comprehensive_with_pauses():
    """Pauses should generate warnings."""
    rr = [800] * 10 + [3500] + [800] * 10
    result = comprehensive_holter_analysis(rr)
    assert len(result["warnings"]) > 0


# =============================================================================
# CLI Tests
# =============================================================================

def test_cli_rr():
    from cli import main
    rc = main(["rr", "--rr", "800,820,790,810,850,780,800,830,790,810"])
    assert rc == 0


def test_cli_hr():
    from cli import main
    rc = main(["hr", "--rr", "800,820,790,810,850,780,800,830,790,810"])
    assert rc == 0


def test_cli_pauses():
    from cli import main
    rc = main(["pauses", "--rr", "800,820,2500,810,3200,780,800"])
    assert rc == 0


def test_cli_burden():
    from cli import main
    rc = main(["burden", "--rr", "800,820,790,810,850,780,800,830,790,810"])
    assert rc == 0


def test_cli_irregularity():
    from cli import main
    rc = main(["irregularity", "--rr", "800,650,900,700,850,600,950,750"])
    assert rc == 0


def test_cli_comprehensive():
    from cli import main
    rc = main(["comprehensive", "--rr", "800,820,790,810,850,780,800,830,790,810"])
    assert rc == 0
