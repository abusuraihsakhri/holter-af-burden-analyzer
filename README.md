# Holter Monitor AF Burden Analyzer

> **Cardiology - Ambulatory ECG Monitoring**  
> Reference Standards: ESC AF Guidelines (2020), HRV Task Force (1996)

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)

---

## Overview

A real, functional Holter monitor analyzer implementing:

- **AF Burden**: Time in AF / Total monitoring time x 100%
- **RR Interval Analysis**: Mean RR, SDNN, RMSSD, pNN50
- **Heart Rate Statistics**: Min, max, mean, resting HR
- **Pause Detection**: Significant (>2000ms), Pathological (>3000ms)
- **Tachycardia Burden**: % time HR >100 bpm
- **Bradycardia Burden**: % time HR <50 bpm
- **Irregularity Index**: Coefficient of variation of RR intervals

**No external dependencies** - uses only Python standard library.

---

## Quick Start

```bash
# RR interval / HRV analysis
python cli.py rr --rr "800,820,790,810,850,780,800,830,790,810"

# Heart rate statistics
python cli.py hr --rr "800,820,790,810,850,780,800,830,790,810"

# Pause detection
python cli.py pauses --rr "800,820,2500,810,3200,780,800"

# Burden analysis (tachy/brady/AF)
python cli.py burden --rr "800,820,790,810,850,780,800,830,790,810"

# Irregularity index
python cli.py irregularity --rr "800,650,900,700,850,600,950,750"

# Comprehensive analysis
python cli.py comprehensive --rr "800,820,790,810,850,780,800,830,790,810"
```

---

## Python API

```python
from holter_af import (
    calculate_mean_rr,
    calculate_sdnn,
    calculate_rmssd,
    calculate_pnn50,
    calculate_heart_rate_stats,
    detect_pauses,
    calculate_af_burden,
    calculate_irregularity_index,
    comprehensive_holter_analysis,
)

rr = [800, 820, 790, 810, 850, 780, 800, 830, 790, 810]

# HRV metrics
sdnn = calculate_sdnn(rr)       # Standard deviation of NN intervals
rmssd = calculate_rmssd(rr)     # Root mean square of successive differences
pnn50 = calculate_pnn50(rr)     # % of successive RR intervals >50ms different

# Heart rate stats
stats = calculate_heart_rate_stats(rr)
# -> {'min_hr': ..., 'max_hr': ..., 'mean_hr': ..., 'resting_hr': ...}

# Pause detection
pauses = detect_pauses([800, 2500, 810, 3200, 780])
# -> {'num_significant': 1, 'num_pathological': 1, ...}

# AF burden
af = calculate_af_burden(rr)
# -> {'af_burden_percent': ..., 'monitoring_hours': ..., ...}

# Irregularity index
irreg = calculate_irregularity_index(rr)
# -> {'irregularity_index': 0.03, 'irregular': False, ...}
```

---

## Clinical Reference

### HRV Metrics
| Metric | Normal (24h) | Significance |
|--------|-------------|-------------|
| SDNN | >50 ms | <50 ms: high risk for cardiac events |
| RMSSD | >20 ms | Reflects parasympathetic activity |
| pNN50 | >5% | Decreases with age, reduced in AF |

### Pause Thresholds
| Type | Duration | Clinical Action |
|------|----------|----------------|
| Significant | >2000 ms | Evaluate for symptomatic bradycardia |
| Pathological | >3000 ms | Consider pacemaker evaluation |

### AF Burden Categories
| Burden | Classification |
|--------|---------------|
| 0% | No AF detected |
| <1% | Low burden |
| 1-10% | Moderate burden |
| >10% | High burden |

### Irregularity Index (CV)
| CV Value | Interpretation |
|----------|---------------|
| <0.10 | Regular rhythm |
| 0.10-0.15 | Borderline irregularity |
| >0.15 | Irregular (suggests AF) |

---

## Disclaimer

This tool is for **educational and clinical decision support purposes only**. It does not replace professional medical judgment. Always correlate with clinical context.

## License

MIT License. See [LICENSE](LICENSE) for details.
