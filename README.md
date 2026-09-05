# Holter AF Burden Analyzer

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** ESC Guidelines for AF (2020), Task Force ESC/NASPE on HRV (1996)

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

Clinical calculations for Holter monitor analysis:

- **AF Burden** - Time in AF / total monitoring time (%)
- **RR Interval Analysis** - Mean RR, SDNN, RMSSD, pNN50
- **Heart Rate Statistics** - Min, max, mean, resting HR
- **Pause Detection** - Significant (>2000ms), pathological (>3000ms)
- **Tachycardia Burden** - % time HR >100 bpm
- **Bradycardia Burden** - % time HR <50 bpm
- **Irregularity Index** - Coefficient of variation of RR intervals
- **Distributed Component Audit** - Multi-worker task evaluation with HMAC-SHA256 audit trail
- **FastAPI REST API** - OpenAPI 3.1 endpoints with Prometheus metrics

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/holter-af-burden-analyzer.git
cd holter-af-burden-analyzer

# Install dependencies
pip install -e ".[dev]"
```

---

## Usage

### Clinical Analysis CLI

```bash
# RR interval / HRV analysis
python cli.py rr --rr "800,810,790,805,795,800"

# Heart rate statistics
python cli.py hr --rr "800,810,790,805,795,800"

# Pause detection
python cli.py pauses --rr "800,800,2500,800,3500,800"

# Tachycardia/bradycardia/AF burden
python cli.py burden --rr "800,810,790,805,795,800" --tachy-threshold 100 --brady-threshold 50

# Irregularity index
python cli.py irregularity --rr "800,650,900,700,850,600,950,750"

# Comprehensive Holter analysis
python cli.py comprehensive --rr "800,810,790,805,795,800"

# Output JSON (add --json to any command)
python cli.py rr --rr "800,810,790" --json
```

### Distributed Component Audit CLI

```bash
# Run an audit task
python cli.py audit --task-id "TASK-001" --primary-metric 12.5 --status-descriptor "NOMINAL"

# Query the supervisory assistant
python cli.py chat "Explain AF burden significance"

# Verify HMAC audit trail integrity
python cli.py verify-audit

# Start the REST API server
python cli.py serve --host 0.0.0.0 --port 8000
```

### REST API Server

```bash
# Start the FastAPI server
python cli.py serve

# Or with Docker
docker compose up --build
```

Endpoints:
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /api/audit` - Dispatch audit task
- `POST /api/chat` - Supervisory chat
- `GET /api/audit/logs` - Audit trail

### Stress Testing Simulator

```bash
# Run simulation (default: 100 iterations)
python simulator.py --iterations 1000 --seed 42
```

---

## API Reference

### Core Clinical Functions

| Function | Description |
|:---------|:------------|
| `rr_to_hr(rr_ms)` | Convert RR interval (ms) to heart rate (bpm) |
| `hr_to_rr(hr_bpm)` | Convert heart rate (bpm) to RR interval (ms) |
| `calculate_mean_rr(rr)` | Mean RR interval (ms) |
| `calculate_sdnn(rr)` | SDNN - Standard Deviation of NN intervals |
| `calculate_rmssd(rr)` | RMSSD - Root Mean Square of Successive Differences |
| `calculate_pnn50(rr)` | pNN50 - % of successive RR intervals differing >50ms |
| `calculate_heart_rate_stats(rr)` | Heart rate statistics (min, max, mean, resting) |
| `detect_pauses(rr)` | Pause detection (>2000ms significant, >3000ms pathological) |
| `calculate_tachycardia_burden(rr, threshold)` | Tachycardia burden (% time HR > threshold) |
| `calculate_bradycardia_burden(rr, threshold)` | Bradycardia burden (% time HR < threshold) |
| `calculate_irregularity_index(rr)` | Irregularity index (coefficient of variation) |
| `calculate_af_burden(rr, annotations)` | AF burden calculation |
| `comprehensive_holter_analysis(rr)` | Comprehensive Holter analysis |

---

## Testing

```bash
# Run all tests
pytest -v

# Run specific test files
pytest test_holter_af.py -v
pytest tests/ -v
```

### Test Coverage

- **test_holter_af.py** - Core clinical calculation tests (44 tests)
- **tests/test_holter_af_burden_analyzer.py** - Agent, worker, and audit tests
- **tests/test_enrichment.py** - Enrichment suite tests

---

## Security

- **Zero-PHI Outbound Guard** - AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **HMAC-SHA256 Audit Trail** - Chained, cryptographically signed logs
- **Non-root Docker container** - Runs as unprivileged user

### Environment Variables

| Variable | Description | Required |
|:---------|:------------|:---------|
| `AUDIT_SECRET_KEY` | HMAC-SHA256 signing key (generate: `python -c "import secrets; print(secrets.token_hex(32))"`) | Recommended |
| `MODEL_PROVIDER` | LLM provider: mock, ollama, claude, openai | No (default: mock) |

Copy `.env.example` to `.env` and set your values. Never commit `.env`.

---

## Project Structure

```
holter-af-burden-analyzer/
├── cli.py                    # Command-line interface
├── holter_af.py              # Core clinical calculations
├── enrichment.py             # Enrichment feature engines
├── simulator.py              # Stress testing simulator
├── pyproject.toml            # Package configuration
├── Dockerfile                # Container build
├── docker-compose.yml        # Container orchestration
├── web/
│   └── index.html            # Operations console UI
├── agents/
│   ├── api.py                # FastAPI REST server
│   ├── base.py               # Security, PHI guard, audit trail
│   ├── models.py             # Pydantic data models
│   ├── supervisor.py         # Multi-worker orchestrator
│   ├── workers.py            # Specialized worker agents
│   ├── llm_factory.py        # LLM provider factory
│   ├── learning.py           # Bayesian calibration engine
│   ├── metrics.py            # Prometheus metrics collector
│   └── streamer.py           # WebSocket telemetry streamer
├── tests/
│   ├── test_holter_af_burden_analyzer.py
│   └── test_enrichment.py
├── test_holter_af.py         # Core calculation tests
└── .github/workflows/ci.yml  # CI/CD pipeline
```

---

## References

- ESC Guidelines for Atrial Fibrillation (2020)
- Task Force of ESC/NASPE on HRV (1996)
- Camm AJ et al. Guidelines for AF Management

---

## License

MIT License. See [LICENSE](LICENSE).
