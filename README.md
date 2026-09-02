# Holter AF Burden Analyzer

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

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

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`rr_to_hr()`**: Convert RR interval in ms to heart rate in bpm.
- **`hr_to_rr()`**: Convert heart rate in bpm to RR interval in ms.
- **`calculate_mean_rr()`**: Calculate mean RR interval in ms.
- **`calculate_sdnn()`**: Calculate SDNN - Standard Deviation of NN (RR) intervals.

SDNN reflects all cyclic components responsible for variability
in the period of recording. It is the gold standard for HRV.

Normal SDNN (24h Holter): >50 ms (low risk), <50 ms (high risk)

Args:
    rr_intervals_ms: List of RR intervals in milliseconds

Returns:
    SDNN in milliseconds
- **`calculate_sdann()`**: Calculate SDANN - Standard deviation of 5-minute mean NN intervals.

Reflects long-term HRV components.
Normal SDANN (24h): >100 ms

Args:
    rr_intervals_ms: List of RR intervals in ms
    segment_minutes: Segment duration in minutes (default 5)

Returns:
    SDANN in milliseconds

---

## 📐 Mathematical Formulation & Logic

```text
  """Calculate mean RR interval in ms."""
  Calculate SDNN - Standard Deviation of NN (RR) intervals.
  Calculate SDANN - Standard deviation of 5-minute mean NN intervals.
  Calculate RMSSD - Root Mean Square of Successive Differences.
  Calculate pNN50 - Percentage of successive RR intervals differing >50ms.
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --json <value> --rr <value> --tachy-threshold <value> --brady-threshold <value>
```

### Parameter Reference
- `--json`: Specifies input measurement or parameter value.
- `--rr`: Specifies input measurement or parameter value.
- `--tachy-threshold`: Specifies input measurement or parameter value.
- `--brady-threshold`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `query` | Parameter / observation metric | Required |
| `name` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t holter-af-burden-analyzer .
docker run -p 8000:8000 holter-af-burden-analyzer
```
