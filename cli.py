#!/usr/bin/env python3
"""
CLI for Holter Monitor AF Burden Analyzer.

Provides commands for AF burden calculation, RR interval analysis,
heart rate statistics, pause detection, and HRV metrics.
"""
import argparse
import csv
import json
import sys

from holter_af import (
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
    rr_to_hr,
    hr_to_rr,
)

from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger


def parse_rr_input(rr_str: str) -> list:
    """Parse RR intervals from comma-separated string or file."""
    try:
        return [float(x.strip()) for x in rr_str.split(",") if x.strip()]
    except ValueError:
        return []


def cmd_rr_analysis(args):
    """Analyze RR intervals for HRV metrics."""
    rr = parse_rr_input(args.rr)
    if not rr:
        print("Error: no valid RR intervals provided", file=sys.stderr)
        return 1

    mean_rr = calculate_mean_rr(rr)
    sdnn = calculate_sdnn(rr)
    rmssd = calculate_rmssd(rr)
    pnn50 = calculate_pnn50(rr)

    print("=" * 60)
    print("  RR INTERVAL / HRV ANALYSIS")
    print("=" * 60)
    print(f"  Number of intervals: {len(rr)}")
    print(f"  Mean RR:             {mean_rr:.1f} ms")
    print(f"  SDNN:                {sdnn:.1f} ms")
    print(f"  RMSSD:               {rmssd:.1f} ms")
    print(f"  pNN50:               {pnn50:.1f}%")

    if sdnn < 50:
        print("  ** Low SDNN - reduced HRV (increased risk)")
    if rmssd < 20:
        print("  ** Low RMSSD - reduced parasympathetic activity")

    if args.json:
        result = {
            "mean_rr_ms": round(mean_rr, 1),
            "sdnn_ms": round(sdnn, 1),
            "rmssd_ms": round(rmssd, 1),
            "pnn50_percent": round(pnn50, 1),
        }
        print("\n" + json.dumps(result, indent=2))
    return 0


def cmd_hr_stats(args):
    """Calculate heart rate statistics."""
    rr = parse_rr_input(args.rr)
    if not rr:
        print("Error: no valid RR intervals provided", file=sys.stderr)
        return 1

    stats = calculate_heart_rate_stats(rr)

    print("=" * 60)
    print("  HEART RATE STATISTICS")
    print("=" * 60)
    print(f"  Total beats:  {stats['num_beats']}")
    print(f"  Min HR:       {stats['min_hr']} bpm")
    print(f"  Max HR:       {stats['max_hr']} bpm")
    print(f"  Mean HR:      {stats['mean_hr']} bpm")
    print(f"  Resting HR:   {stats['resting_hr']} bpm")

    if args.json:
        print("\n" + json.dumps(stats, indent=2))
    return 0


def cmd_pauses(args):
    """Detect pauses in RR intervals."""
    rr = parse_rr_input(args.rr)
    if not rr:
        print("Error: no valid RR intervals provided", file=sys.stderr)
        return 1

    pauses = detect_pauses(rr)

    print("=" * 60)
    print("  PAUSE DETECTION")
    print("=" * 60)
    print(f"  Longest pause:       {pauses['longest_pause_ms']:.0f} ms")
    print(f"  Significant pauses:  {pauses['num_significant']} (>2000 ms)")
    print(f"  Pathological pauses: {pauses['num_pathological']} (>3000 ms)")

    if pauses["pathological_pauses"]:
        print("\n  PATHOLOGICAL PAUSES:")
        for p in pauses["pathological_pauses"][:5]:
            print(f"    Beat {p['index']}: {p['duration_ms']:.0f} ms")

    if pauses["significant_pauses"]:
        print("\n  SIGNIFICANT PAUSES:")
        for p in pauses["significant_pauses"][:5]:
            print(f"    Beat {p['index']}: {p['duration_ms']:.0f} ms")

    if args.json:
        print("\n" + json.dumps(pauses, indent=2))
    return 0


def cmd_burden(args):
    """Calculate tachycardia/bradycardia/AF burden."""
    rr = parse_rr_input(args.rr)
    if not rr:
        print("Error: no valid RR intervals provided", file=sys.stderr)
        return 1

    tachy = calculate_tachycardia_burden(rr, args.tachy_threshold)
    brady = calculate_bradycardia_burden(rr, args.brady_threshold)
    irregularity = calculate_irregularity_index(rr)
    af = calculate_af_burden(rr)

    print("=" * 60)
    print("  BURDEN ANALYSIS")
    print("=" * 60)
    print(f"\n  Tachycardia (HR >{tachy['threshold_bpm']} bpm):")
    print(f"    Beat burden: {tachy['beat_percentage']:.1f}%")
    print(f"    Time burden: {tachy['time_percentage']:.1f}%")

    print(f"\n  Bradycardia (HR <{brady['threshold_bpm']} bpm):")
    print(f"    Beat burden: {brady['beat_percentage']:.1f}%")
    print(f"    Time burden: {brady['time_percentage']:.1f}%")

    print(f"\n  Irregularity Index (CV): {irregularity['irregularity_index']:.4f}")
    print(f"    {irregularity['interpretation']}")

    print(f"\n  AF Burden: {af['af_burden_percent']:.2f}%")
    print(f"    AF time: {af['af_hours']:.2f} hours / {af['monitoring_hours']:.2f} hours")

    if args.json:
        result = {
            "tachycardia": tachy,
            "bradycardia": brady,
            "irregularity": irregularity,
            "af_burden": af,
        }
        print("\n" + json.dumps(result, indent=2))
    return 0


def cmd_irregularity(args):
    """Calculate irregularity index."""
    rr = parse_rr_input(args.rr)
    if not rr:
        print("Error: no valid RR intervals provided", file=sys.stderr)
        return 1

    result = calculate_irregularity_index(rr)

    print("=" * 60)
    print("  IRREGULARITY INDEX")
    print("=" * 60)
    print(f"  Mean RR:            {result['mean_rr_ms']} ms")
    print(f"  SDNN:               {result['sdnn_ms']} ms")
    print(f"  CV (irregularity):  {result['irregularity_index']:.4f}")
    print(f"  Irregular:          {'Yes' if result['irregular'] else 'No'}")
    print(f"  Interpretation:     {result['interpretation']}")

    if args.json:
        print("\n" + json.dumps(result, indent=2))
    return 0


def cmd_comprehensive(args):
    """Run comprehensive Holter analysis."""
    rr = parse_rr_input(args.rr)
    if not rr:
        print("Error: no valid RR intervals provided", file=sys.stderr)
        return 1

    result = comprehensive_holter_analysis(rr)

    print("=" * 60)
    print("  COMPREHENSIVE HOLTER ANALYSIS")
    print("=" * 60)

    hr = result["parameters"]["heart_rate"]
    print(f"\n  Heart Rate:")
    print(f"    Min: {hr['min_hr']} bpm | Max: {hr['max_hr']} bpm | Mean: {hr['mean_hr']} bpm")
    print(f"    Resting: {hr['resting_hr']} bpm | Beats: {hr['num_beats']}")

    hrv = result["parameters"]["hrv"]
    print(f"\n  HRV Metrics:")
    print(f"    Mean RR: {hrv['mean_rr_ms']} ms | SDNN: {hrv['sdnn_ms']} ms")
    print(f"    RMSSD: {hrv['rmssd_ms']} ms | pNN50: {hrv['pnn50_percent']}%")

    pauses = result["parameters"]["pauses"]
    print(f"\n  Pauses: {pauses['num_significant']} significant, {pauses['num_pathological']} pathological")

    tachy = result["parameters"]["tachycardia_burden"]
    brady = result["parameters"]["bradycardia_burden"]
    print(f"\n  Tachycardia burden: {tachy['time_percentage']:.1f}%")
    print(f"  Bradycardia burden: {brady['time_percentage']:.1f}%")

    irreg = result["parameters"]["irregularity"]
    print(f"\n  Irregularity index: {irreg['irregularity_index']:.4f} ({irreg['interpretation']})")

    af = result["parameters"]["af_burden"]
    print(f"\n  AF burden: {af['af_burden_percent']:.2f}%")

    if result["findings"]:
        print("\n  FINDINGS:")
        for f in result["findings"]:
            print(f"    - {f}")

    if result["warnings"]:
        print("\n  WARNINGS:")
        for w in result["warnings"]:
            print(f"    !! {w}")

    print(f"\n  SUMMARY: {result['summary']}")

    if args.json:
        print("\n" + json.dumps(result, indent=2))
    return 0


def cmd_audit(args):
    """Run a distributed component audit task."""
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id=args.task_id,
        target_identifier=args.target_id or "CLI-TARGET",
        primary_metric=args.primary_metric,
        secondary_metric=args.secondary_metric,
        status_descriptor=args.status_descriptor,
        is_critical_flag=args.is_critical,
    )
    dossier = supervisor.process_task(payload)

    print("=" * 60)
    print("  DISTRIBUTED COMPONENT AUDIT")
    print("=" * 60)
    print(f"  Dossier ID:      {dossier.dossier_id}")
    print(f"  Task ID:         {dossier.task_id}")
    print(f"  Target:          {dossier.target_identifier}")
    print(f"  Overall Urgency: {dossier.overall_urgency.value}")
    print(f"  Integrity:       {dossier.integrity_status.value}")
    print(f"  Total Alerts:    {dossier.total_alerts}")
    print(f"  Critical Alerts: {dossier.critical_alerts_count}")
    print(f"  Audit Hash:      {dossier.audit_hash}")
    print(f"  Summary:         {dossier.consensus_summary}")

    if dossier.alerts:
        print("\n  ALERTS:")
        for a in dossier.alerts:
            print(f"    [{a.urgency.value}] {a.summary}")
            print(f"      Remediation: {a.actionable_remediation}")

    if args.json:
        print("\n" + json.dumps(dossier.to_dict(), indent=2, default=str))
    return 0


def cmd_chat(args):
    """Query the air-gapped supervisory assistant."""
    supervisor = SystemSupervisor(model_provider="mock")
    query = " ".join(args.query)
    response = supervisor.query_supervisory_chat(query)
    print(response)
    return 0


def cmd_verify_audit(args):
    """Verify the cryptographic integrity of the HMAC audit trail."""
    verified = AuditLogger.verify_integrity()
    trail_len = len(AuditLogger.get_trail())
    print("=" * 60)
    print("  HMAC-SHA256 AUDIT TRAIL VERIFICATION")
    print("=" * 60)
    print(f"  Audit Blocks: {trail_len}")
    print(f"  Integrity:    {'VERIFIED' if verified else 'COMPROMISED'}")
    if args.json:
        print("\n" + json.dumps({"verified": verified, "blocks": trail_len}, indent=2))
    return 0 if verified else 1


def cmd_serve(args):
    """Start the FastAPI REST API server."""
    try:
        import uvicorn
        from agents.api import app
    except ImportError as e:
        print(f"Error: missing dependencies for serve command: {e}", file=sys.stderr)
        print("Install with: pip install fastapi uvicorn", file=sys.stderr)
        return 1

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="holter-af",
        description="Holter Monitor AF Burden Analyzer",
    )
    parser.add_argument("--json", action="store_true", help="Also output JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # RR analysis
    p_rr = subparsers.add_parser("rr", help="RR interval / HRV analysis")
    p_rr.add_argument("--rr", required=True, help="Comma-separated RR intervals in ms")

    # HR stats
    p_hr = subparsers.add_parser("hr", help="Heart rate statistics")
    p_hr.add_argument("--rr", required=True, help="Comma-separated RR intervals in ms")

    # Pauses
    p_pause = subparsers.add_parser("pauses", help="Detect pauses")
    p_pause.add_argument("--rr", required=True, help="Comma-separated RR intervals in ms")

    # Burden
    p_burden = subparsers.add_parser("burden", help="Tachy/brady/AF burden")
    p_burden.add_argument("--rr", required=True, help="Comma-separated RR intervals in ms")
    p_burden.add_argument("--tachy-threshold", type=float, default=100, help="Tachycardia HR threshold")
    p_burden.add_argument("--brady-threshold", type=float, default=50, help="Bradycardia HR threshold")

    # Irregularity
    p_irreg = subparsers.add_parser("irregularity", help="Irregularity index")
    p_irreg.add_argument("--rr", required=True, help="Comma-separated RR intervals in ms")

    # Comprehensive
    p_comp = subparsers.add_parser("comprehensive", help="Comprehensive Holter analysis")
    p_comp.add_argument("--rr", required=True, help="Comma-separated RR intervals in ms")

    # Distributed Component Audit
    p_audit = subparsers.add_parser("audit", help="Run a distributed component audit task")
    p_audit.add_argument("--task-id", required=True, help="Unique task identifier")
    p_audit.add_argument("--target-id", default="CLI-TARGET", help="Target identifier")
    p_audit.add_argument("--primary-metric", type=float, default=10.0, help="Primary measurement value")
    p_audit.add_argument("--secondary-metric", type=float, default=2.0, help="Secondary measurement value")
    p_audit.add_argument("--status-descriptor", default="NOMINAL", help="Status descriptor")
    p_audit.add_argument("--is-critical", action="store_true", help="Flag as critical priority")

    # Air-gapped supervisory chat
    p_chat = subparsers.add_parser("chat", help="Query the air-gapped supervisory assistant")
    p_chat.add_argument("query", nargs="+", help="Query text for the assistant")

    # Verify HMAC audit trail
    p_verify = subparsers.add_parser("verify-audit", help="Verify HMAC-SHA256 audit trail integrity")

    # Serve REST API
    p_serve = subparsers.add_parser("serve", help="Start the FastAPI REST API server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")

    args = parser.parse_args(argv)

    commands = {
        "rr": cmd_rr_analysis,
        "hr": cmd_hr_stats,
        "pauses": cmd_pauses,
        "burden": cmd_burden,
        "irregularity": cmd_irregularity,
        "comprehensive": cmd_comprehensive,
        "audit": cmd_audit,
        "chat": cmd_chat,
        "verify-audit": cmd_verify_audit,
        "serve": cmd_serve,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
