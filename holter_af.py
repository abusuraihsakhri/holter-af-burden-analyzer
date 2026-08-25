#!/usr/bin/env python3
"""
Holter Monitor AF Burden Analyzer

Real clinical calculations for Holter monitor analysis including:
- AF burden calculation (time in AF / total monitoring time)
- RR interval analysis (Mean RR, SDNN, RMSSD, pNN50)
- Heart rate statistics (min, max, mean, resting HR)
- Pause detection (significant >2000ms, pathological >3000ms)
- Tachycardia burden (% time HR >100 bpm)
- Bradycardia burden (% time HR <50 bpm)
- Irregularity index (coefficient of variation of RR intervals)

References:
- ESC Guidelines for Atrial Fibrillation (2020)
- Task Force of ESC/NASPE on HRV (1996)
- Camm AJ et al. Guidelines for AF Management

Author: Medical Calculator Project
License: MIT
"""

import math
from typing import Dict, Any, List, Optional, Tuple


# =============================================================================
# THRESHOLDS AND CONSTANTS
# =============================================================================

PAUSE_SIGNIFICANT_MS = 2000  # RR > 2000ms is significant
PAUSE_PATHOLOGICAL_MS = 3000  # RR > 3000ms is pathological
TACHYCARDIA_HR_THRESHOLD = 100  # bpm
BRADYCARDIA_HR_THRESHOLD = 50  # bpm
AF_IRREGULARITY_THRESHOLD = 0.15  # CV > 0.15 suggests irregularity


# =============================================================================
# CORE RR INTERVAL ANALYSIS
# =============================================================================

def rr_to_hr(rr_ms: float) -> float:
    """Convert RR interval in ms to heart rate in bpm."""
    if rr_ms <= 0:
        raise ValueError("RR interval must be positive")
    return 60000.0 / rr_ms


def hr_to_rr(hr_bpm: float) -> float:
    """Convert heart rate in bpm to RR interval in ms."""
    if hr_bpm <= 0:
        raise ValueError("Heart rate must be positive")
    return 60000.0 / hr_bpm


def calculate_mean_rr(rr_intervals_ms: List[float]) -> float:
    """Calculate mean RR interval in ms."""
    if not rr_intervals_ms:
        raise ValueError("RR intervals list cannot be empty")
    return sum(rr_intervals_ms) / len(rr_intervals_ms)


def calculate_sdnn(rr_intervals_ms: List[float]) -> float:
    """
    Calculate SDNN - Standard Deviation of NN (RR) intervals.
    
    SDNN reflects all cyclic components responsible for variability
    in the period of recording. It is the gold standard for HRV.
    
    Normal SDNN (24h Holter): >50 ms (low risk), <50 ms (high risk)
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
    
    Returns:
        SDNN in milliseconds
    """
    if len(rr_intervals_ms) < 2:
        raise ValueError("Need at least 2 RR intervals for SDNN")
    n = len(rr_intervals_ms)
    mean = sum(rr_intervals_ms) / n
    variance = sum((x - mean) ** 2 for x in rr_intervals_ms) / (n - 1)
    return math.sqrt(variance)


def calculate_sdann(rr_intervals_ms: List[float], segment_minutes: int = 5) -> float:
    """
    Calculate SDANN - Standard deviation of 5-minute mean NN intervals.
    
    Reflects long-term HRV components.
    Normal SDANN (24h): >100 ms
    
    Args:
        rr_intervals_ms: List of RR intervals in ms
        segment_minutes: Segment duration in minutes (default 5)
    
    Returns:
        SDANN in milliseconds
    """
    if not rr_intervals_ms:
        raise ValueError("RR intervals list cannot be empty")
    
    # Group RR intervals into 5-minute segments
    segment_ms = segment_minutes * 60 * 1000
    segments = []
    current_segment = []
    current_sum = 0
    
    for rr in rr_intervals_ms:
        current_segment.append(rr)
        current_sum += rr
        if current_sum >= segment_ms:
            segments.append(sum(current_segment) / len(current_segment))
            current_segment = []
            current_sum = 0
    
    # Include last partial segment if it has data
    if current_segment:
        segments.append(sum(current_segment) / len(current_segment))
    
    if len(segments) < 2:
        return 0.0
    
    mean_seg = sum(segments) / len(segments)
    variance = sum((x - mean_seg) ** 2 for x in segments) / (len(segments) - 1)
    return math.sqrt(variance)


def calculate_rmssd(rr_intervals_ms: List[float]) -> float:
    """
    Calculate RMSSD - Root Mean Square of Successive Differences.
    
    RMSSD reflects parasympathetic (vagal) modulation of heart rate.
    It is the primary time-domain measure of short-term HRV.
    
    Normal RMSSD: >20 ms (healthy adults)
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
    
    Returns:
        RMSSD in milliseconds
    """
    if len(rr_intervals_ms) < 2:
        raise ValueError("Need at least 2 RR intervals for RMSSD")
    
    successive_diffs = []
    for i in range(1, len(rr_intervals_ms)):
        diff = rr_intervals_ms[i] - rr_intervals_ms[i - 1]
        successive_diffs.append(diff ** 2)
    
    return math.sqrt(sum(successive_diffs) / len(successive_diffs))


def calculate_pnn50(rr_intervals_ms: List[float]) -> float:
    """
    Calculate pNN50 - Percentage of successive RR intervals differing >50ms.
    
    pNN50 reflects parasympathetic activity and correlates with RMSSD.
    
    Normal pNN50: >5% (healthy young adults), decreases with age
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
    
    Returns:
        pNN50 as percentage (0-100)
    """
    if len(rr_intervals_ms) < 2:
        raise ValueError("Need at least 2 RR intervals for pNN50")
    
    count_gt_50 = 0
    total_pairs = len(rr_intervals_ms) - 1
    
    for i in range(1, len(rr_intervals_ms)):
        if abs(rr_intervals_ms[i] - rr_intervals_ms[i - 1]) > 50:
            count_gt_50 += 1
    
    return (count_gt_50 / total_pairs) * 100.0


def calculate_heart_rate_stats(rr_intervals_ms: List[float]) -> Dict[str, Any]:
    """
    Calculate heart rate statistics from RR intervals.
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
    
    Returns:
        Dictionary with HR statistics
    """
    if not rr_intervals_ms:
        raise ValueError("RR intervals list cannot be empty")
    
    hrs = [rr_to_hr(rr) for rr in rr_intervals_ms if rr > 0]
    
    if not hrs:
        raise ValueError("No valid RR intervals")
    
    # Resting HR: use the lowest sustained HR (minimum 10-beat average)
    resting_hr = min(hrs)  # Simplified: use minimum instantaneous HR
    
    # For a more accurate resting HR, compute rolling averages
    if len(hrs) >= 10:
        rolling_avgs = []
        for i in range(len(hrs) - 9):
            rolling_avgs.append(sum(hrs[i:i + 10]) / 10.0)
        resting_hr = min(rolling_avgs)
    
    return {
        "min_hr": round(min(hrs), 1),
        "max_hr": round(max(hrs), 1),
        "mean_hr": round(sum(hrs) / len(hrs), 1),
        "resting_hr": round(resting_hr, 1),
        "num_beats": len(hrs),
    }


def detect_pauses(rr_intervals_ms: List[float]) -> Dict[str, Any]:
    """
    Detect pauses in RR intervals.
    
    Significant pause: RR > 2000 ms
    Pathological pause: RR > 3000 ms
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
    
    Returns:
        Dictionary with pause information
    """
    significant_pauses = []
    pathological_pauses = []
    
    for i, rr in enumerate(rr_intervals_ms):
        if rr > PAUSE_PATHOLOGICAL_MS:
            pathological_pauses.append({"index": i, "duration_ms": rr, "type": "pathological"})
        elif rr > PAUSE_SIGNIFICANT_MS:
            significant_pauses.append({"index": i, "duration_ms": rr, "type": "significant"})
    
    return {
        "significant_pauses": significant_pauses,
        "pathological_pauses": pathological_pauses,
        "num_significant": len(significant_pauses),
        "num_pathological": len(pathological_pauses),
        "longest_pause_ms": max(rr_intervals_ms) if rr_intervals_ms else 0,
    }


def calculate_tachycardia_burden(rr_intervals_ms: List[float], threshold_bpm: float = 100) -> Dict[str, Any]:
    """
    Calculate tachycardia burden (% of time HR > threshold).
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
        threshold_bpm: HR threshold for tachycardia (default 100 bpm)
    
    Returns:
        Dictionary with tachycardia burden
    """
    if not rr_intervals_ms:
        raise ValueError("RR intervals list cannot be empty")
    
    threshold_rr = hr_to_rr(threshold_bpm)
    tachy_count = sum(1 for rr in rr_intervals_ms if rr < threshold_rr)
    total = len(rr_intervals_ms)
    
    # Also calculate time-weighted burden
    total_time_ms = sum(rr_intervals_ms)
    tachy_time_ms = sum(rr for rr in rr_intervals_ms if rr < threshold_rr)
    
    return {
        "threshold_bpm": threshold_bpm,
        "beats_in_tachycardia": tachy_count,
        "total_beats": total,
        "beat_percentage": round((tachy_count / total) * 100, 2),
        "time_percentage": round((tachy_time_ms / total_time_ms) * 100, 2) if total_time_ms > 0 else 0,
    }


def calculate_bradycardia_burden(rr_intervals_ms: List[float], threshold_bpm: float = 50) -> Dict[str, Any]:
    """
    Calculate bradycardia burden (% of time HR < threshold).
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
        threshold_bpm: HR threshold for bradycardia (default 50 bpm)
    
    Returns:
        Dictionary with bradycardia burden
    """
    if not rr_intervals_ms:
        raise ValueError("RR intervals list cannot be empty")
    
    threshold_rr = hr_to_rr(threshold_bpm)
    brady_count = sum(1 for rr in rr_intervals_ms if rr > threshold_rr)
    total = len(rr_intervals_ms)
    
    total_time_ms = sum(rr_intervals_ms)
    brady_time_ms = sum(rr for rr in rr_intervals_ms if rr > threshold_rr)
    
    return {
        "threshold_bpm": threshold_bpm,
        "beats_in_bradycardia": brady_count,
        "total_beats": total,
        "beat_percentage": round((brady_count / total) * 100, 2),
        "time_percentage": round((brady_time_ms / total_time_ms) * 100, 2) if total_time_ms > 0 else 0,
    }


def calculate_irregularity_index(rr_intervals_ms: List[float]) -> Dict[str, Any]:
    """
    Calculate irregularity index (coefficient of variation of RR intervals).
    
    CV = SDNN / Mean RR
    
    A high irregularity index (CV > 0.15) suggests atrial fibrillation
    or other irregular rhythm.
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
    
    Returns:
        Dictionary with irregularity index
    """
    if len(rr_intervals_ms) < 2:
        raise ValueError("Need at least 2 RR intervals")
    
    mean_rr = calculate_mean_rr(rr_intervals_ms)
    sdnn = calculate_sdnn(rr_intervals_ms)
    cv = sdnn / mean_rr if mean_rr > 0 else 0
    
    return {
        "mean_rr_ms": round(mean_rr, 1),
        "sdnn_ms": round(sdnn, 1),
        "irregularity_index": round(cv, 4),
        "irregular": cv > AF_IRREGULARITY_THRESHOLD,
        "interpretation": (
            "Irregular rhythm consistent with atrial fibrillation"
            if cv > AF_IRREGULARITY_THRESHOLD
            else "Regular rhythm"
        ),
    }


def calculate_af_burden(
    rr_intervals_ms: List[float],
    af_annotations: Optional[List[bool]] = None,
    af_rr_threshold_cv: float = 0.15,
) -> Dict[str, Any]:
    """
    Calculate AF burden from RR intervals.
    
    If af_annotations are provided (beat-by-beat AF flags), uses them directly.
    Otherwise, estimates AF from RR irregularity (CV > threshold).
    
    AF burden = Time in AF / Total monitoring time x 100%
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
        af_annotations: Optional list of booleans (True = beat in AF)
        af_rr_threshold_cv: CV threshold for AF detection (default 0.15)
    
    Returns:
        Dictionary with AF burden analysis
    """
    if not rr_intervals_ms:
        raise ValueError("RR intervals list cannot be empty")
    
    total_time_ms = sum(rr_intervals_ms)
    total_beats = len(rr_intervals_ms)
    
    if af_annotations is not None:
        if len(af_annotations) != len(rr_intervals_ms):
            raise ValueError("af_annotations must have same length as rr_intervals_ms")
        
        af_time_ms = sum(
            rr for rr, is_af in zip(rr_intervals_ms, af_annotations) if is_af
        )
        af_beats = sum(1 for is_af in af_annotations if is_af)
        detection_method = "annotation"
    else:
        # Estimate AF using sliding window irregularity
        window_size = 30  # Use 30-beat windows
        af_beats = 0
        af_time_ms = 0
        
        for i in range(total_beats):
            # Check local irregularity using surrounding window
            start = max(0, i - window_size // 2)
            end = min(total_beats, i + window_size // 2)
            window = rr_intervals_ms[start:end]
            
            if len(window) >= 5:
                local_mean = sum(window) / len(window)
                local_var = sum((x - local_mean) ** 2 for x in window) / (len(window) - 1)
                local_cv = math.sqrt(local_var) / local_mean if local_mean > 0 else 0
                
                if local_cv > af_rr_threshold_cv:
                    af_beats += 1
                    af_time_ms += rr_intervals_ms[i]
        
        detection_method = "irregularity_estimation"
    
    burden_pct = (af_time_ms / total_time_ms * 100.0) if total_time_ms > 0 else 0
    
    return {
        "af_burden_percent": round(burden_pct, 2),
        "af_time_ms": af_time_ms,
        "total_time_ms": total_time_ms,
        "af_beats": af_beats,
        "total_beats": total_beats,
        "detection_method": detection_method,
        "monitoring_hours": round(total_time_ms / 3600000, 2),
        "af_hours": round(af_time_ms / 3600000, 2),
    }


def comprehensive_holter_analysis(
    rr_intervals_ms: List[float],
    af_annotations: Optional[List[bool]] = None,
) -> Dict[str, Any]:
    """
    Comprehensive Holter monitor analysis.
    
    Args:
        rr_intervals_ms: List of RR intervals in milliseconds
        af_annotations: Optional beat-by-beat AF annotations
    
    Returns:
        Comprehensive analysis dictionary
    """
    if not rr_intervals_ms:
        raise ValueError("RR intervals list cannot be empty")
    
    result = {"parameters": {}, "findings": [], "warnings": []}
    
    # Heart rate stats
    hr_stats = calculate_heart_rate_stats(rr_intervals_ms)
    result["parameters"]["heart_rate"] = hr_stats
    
    if hr_stats["max_hr"] > 150:
        result["warnings"].append(f"Maximum HR {hr_stats['max_hr']} bpm - consider SVT or rapid AF")
    if hr_stats["min_hr"] < 40:
        result["warnings"].append(f"Minimum HR {hr_stats['min_hr']} bpm - significant bradycardia")
    
    # HRV metrics
    mean_rr = calculate_mean_rr(rr_intervals_ms)
    sdnn = calculate_sdnn(rr_intervals_ms)
    rmssd = calculate_rmssd(rr_intervals_ms)
    pnn50 = calculate_pnn50(rr_intervals_ms)
    
    result["parameters"]["hrv"] = {
        "mean_rr_ms": round(mean_rr, 1),
        "sdnn_ms": round(sdnn, 1),
        "rmssd_ms": round(rmssd, 1),
        "pnn50_percent": round(pnn50, 1),
    }
    
    if sdnn < 50:
        result["warnings"].append(f"Low SDNN ({sdnn:.1f} ms) - reduced HRV, increased risk")
    
    # Pauses
    pauses = detect_pauses(rr_intervals_ms)
    result["parameters"]["pauses"] = pauses
    
    if pauses["num_pathological"] > 0:
        result["warnings"].append(
            f"{pauses['num_pathological']} pathological pause(s) detected (>{PAUSE_PATHOLOGICAL_MS}ms)"
        )
    if pauses["num_significant"] > 0:
        result["findings"].append(f"{pauses['num_significant']} significant pause(s) (>{PAUSE_SIGNIFICANT_MS}ms)")
    
    # Tachycardia/bradycardia burden
    tachy = calculate_tachycardia_burden(rr_intervals_ms)
    brady = calculate_bradycardia_burden(rr_intervals_ms)
    result["parameters"]["tachycardia_burden"] = tachy
    result["parameters"]["bradycardia_burden"] = brady
    
    if tachy["time_percentage"] > 10:
        result["findings"].append(f"Tachycardia burden: {tachy['time_percentage']:.1f}%")
    if brady["time_percentage"] > 5:
        result["findings"].append(f"Bradycardia burden: {brady['time_percentage']:.1f}%")
    
    # Irregularity index
    irregularity = calculate_irregularity_index(rr_intervals_ms)
    result["parameters"]["irregularity"] = irregularity
    
    if irregularity["irregular"]:
        result["findings"].append("Irregular rhythm detected (CV > 0.15)")
    
    # AF burden
    af = calculate_af_burden(rr_intervals_ms, af_annotations)
    result["parameters"]["af_burden"] = af
    
    if af["af_burden_percent"] > 0:
        result["findings"].append(f"AF burden: {af['af_burden_percent']:.1f}%")
    
    result["summary"] = "; ".join(result["findings"]) if result["findings"] else "No significant abnormalities detected"
    
    return result
