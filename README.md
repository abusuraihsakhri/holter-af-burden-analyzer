# Holter AF Burden Analyzer

A research-oriented RR-interval and atrial-fibrillation burden calculator. The project includes a browser-only application, Python calculation functions, a CLI, and an optional FastAPI server.

## Browser application

Open the local application by serving the `web/` directory over HTTP, or use the GitHub Pages deployment if it has been enabled for this repository. The browser implementation runs locally without transmitting input files to an API.

1. Paste a list of **RR intervals in milliseconds**, then select **Analyze recording**.
2. Or select a CSV file with an `rr_ms` column and an optional `af` column. Supply **1** or **0** per interval for AF flags confirmed against the ECG. See [sample.csv](sample.csv) for a *synthetic* example.
3. Review time-weighted AF/irregularity, tachycardia and bradycardia time percentages; HR and RR statistics; and long RR intervals.
4. Export JSON or CSV summary locally.

A CSV file takes precedence over the text box. Files are processed with browser JavaScript and are not uploaded. Supported uploads are at most 5 MB. The browser app does not require Python, Pyodide, a login, or remote APIs. Recent desktop/mobile browsers supporting JavaScript ES modules are required.

## Interpretation and limitations

- With **ECG-reviewed AF annotations**, AF burden equals the sum of marked RR durations divided by total analyzed RR duration. Annotation correctness and artefact exclusion remain the operator's responsibility.
- **Without annotations**, the calculator reports an RR-variability *screening estimate* using local coefficient of variation. This is **not** a diagnosis or confirmed AF burden. Ectopy, artefact, and other irregular rhythms can change the result.
- Mean heart rate is time-weighted. SDNN, RMSSD, and pNN50 are computed from the input RR series, **not automatically filtered NN intervals**. Interpret clinical HRV only after appropriate beat classification, cleaning, and duration standardization.
- A long RR interval is not by itself evidence of a pathologic pause. ECG review is essential.
- No anticoagulation, stroke-risk, or rate/rhythm treatment recommendations are provided. **Not validated for clinical decision-making.**

See the [2024 ESC atrial fibrillation guidelines](https://www.escardio.org/guidelines/clinical-practice-guidelines/all-esc-practice-guidelines/atrial-fibrillation) for ECG diagnostic requirements and AF-burden terminology.

## Python CLI and API

Requires **Python 3.10+**.

```bash
git clone https://github.com/abusuraihsakhri/holter-af-burden-analyzer.git
cd holter-af-burden-analyzer
python -m pip install -e ".[dev]"

# Optional local browser UI
python -m http.server 8080 -d web

# RR / heart rate / burden / complete report
python cli.py rr --rr "800,810,790,805,795,800"
python cli.py hr --rr "800,810,790,805,795,800"
python cli.py burden --rr "800,810,790,805,795,800"
python cli.py comprehensive --rr "800,810,790,805,795,800"
python cli.py --json comprehensive --rr "800,810,790,805,795,800"

# Local API and browser UI on http://127.0.0.1:8000/
python cli.py serve --host 127.0.0.1 --port 8000
```

The API exposes `POST /api/analyze` for a JSON payload such as:

```json
{"rr_intervals_ms":[500,1500],"af_annotations":[true,false]}
```

A 25% time-weighted annotated AF burden is expected for this example. The legacy `POST /api/audit`, `POST /api/chat`, `GET /api/audit/logs`, and `GET /metrics` endpoints remain available for compatibility. **The legacy generic audit thresholds are not calibrated Holter clinical thresholds**; the mock chat endpoint performs no clinical analysis.

The API is unauthenticated, and its audit history is in-memory. Its identifier-screening regexes are **not** comprehensive PHI de-identification. Do not expose the API on a public network or submit identifiable clinical information. `AUDIT_SECRET_KEY` controls the in-process HMAC audit signing key; set it securely for server use. The audit ledger is neither persistent nor a regulated audit system.

For container use, set up a local `.env` based on `.env.example`, then run `docker compose up --build`. Container mode explicitly binds port 8000; apply network access controls.

## Testing

```bash
python -m pytest -v
python -m compileall -q .
node --test tests/browser-calculator.test.mjs
```

GitHub Actions runs Python 3.10–3.12 and Node-based calculator tests. Tests cover annotated time burden, invalid numeric input, CSV validation, core HRV arithmetic, audit integrity, and API responses.

## Technology, privacy and license

The browser client uses HTML, CSS and JavaScript ES modules without external dependencies. The server is Python with FastAPI/Pydantic. The CLI calculation code is plain Python.

Browser analysis is local, but normal web hosting still serves the site assets. The Python API processes any data explicitly submitted to it. Only synthetic or de-identified data should be used.

Licensed under the [MIT License](LICENSE).
