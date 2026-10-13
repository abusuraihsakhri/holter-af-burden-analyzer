/**
 * Browser-local RR interval analysis.
 * AF flags must originate from reviewed ECG annotations.
 * RR-only "burden" is an unvalidated irregularity screening estimate.
 */
const finitePositive = (value) => typeof value === 'number' && Number.isFinite(value) && value > 0;
const round = (value, digits = 2) => Number(value.toFixed(digits));

export function parseRRText(text) {
  const tokens = String(text).trim().split(/[\s,;]+/).filter(Boolean);
  if (!tokens.length) throw new Error('Enter at least two RR intervals in milliseconds.');
  const intervals = tokens.map((token, i) => {
    if (token.trim() === '' || !Number.isFinite(Number(token)) || !finitePositive(Number(token))) {
      throw new Error('Invalid RR interval at position ' + (i + 1) + ': ' + token);
    }
    return Number(token);
  });
  return intervals;
}

function csvRows(text) {
  const rows = [];
  let cells = [], field = '', quoted = false;
  const src = String(text).replace(/^\uFEFF/, '');
  for (let i = 0; i < src.length; i++) {
    const char = src[i];
    if (char === '"') {
      if (quoted && src[i + 1] === '"') { field += '"'; i++; }
      else quoted = !quoted;
    } else if (!quoted && (char === ',' || char === '\t' || char === ';')) {
      cells.push(field.trim()); field = '';
    } else if (!quoted && (char === '\n' || char === '\r')) {
      cells.push(field.trim()); field = '';
      if (cells.some(Boolean)) rows.push(cells);
      cells = [];
      if (char === '\r' && src[i + 1] === '\n') i++;
    } else field += char;
  }
  if (quoted) throw new Error('Unclosed quoted CSV field.');
  cells.push(field.trim());
  if (cells.some(Boolean)) rows.push(cells);
  return rows;
}

export function parseCSV(text) {
  const rows = csvRows(text);
  if (!rows.length) throw new Error('CSV is empty.');
  const header = rows[0].map(x => x.trim().toLowerCase());
  const rrCol = header.findIndex(x => ['rr_ms', 'rr', 'rr_interval_ms', 'rr_interval'].includes(x));
  if (rrCol === -1) {
    if (rows.every(row => row.length === 1)) return {rr: parseRRText(rows.map(row => row[0]).join('\n')), flags: null};
    throw new Error('CSV requires an rr_ms column; optionally add an af column with 1/0.');
  }
  const afCol = header.findIndex(x => ['af', 'af_flag', 'af_annotation'].includes(x));
  const rr = [], flags = afCol === -1 ? null : [];
  for (const [index, row] of rows.slice(1).entries()) {
    const number = Number(row[rrCol]);
    if (row[rrCol] === undefined || row[rrCol] === '' || !finitePositive(number)) {
      throw new Error('Invalid rr_ms value on CSV line ' + (index + 2));
    }
    rr.push(number);
    if (flags) {
      const token = String(row[afCol] ?? '').trim().toLowerCase();
      if (['1', 'true', 'yes'].includes(token)) flags.push(true);
      else if (['0', 'false', 'no'].includes(token)) flags.push(false);
      else throw new Error('Invalid AF annotation on CSV line ' + (index + 2) + ' (use 1/0).');
    }
  }
  return {rr, flags};
}

function sd(values) {
  if (values.length < 2) return 0;
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  return Math.sqrt(values.reduce((a, v) => a + (v - mean) ** 2, 0) / (values.length - 1));
}

export function analyzeRR(rr, flags = null, options = {}) {
  if (!Array.isArray(rr) || rr.length < 2) throw new Error('At least two RR intervals are required.');
  if (rr.length > 1000000) throw new Error('Maximum supported input is 1,000,000 RR intervals.');
  rr.forEach((v, i) => {
    if (!finitePositive(v) || v < 1 || v > 86400000) throw new Error('RR interval ' + (i + 1) + ' must be between 1 ms and 24 h.');
  });
  if (flags !== null && (!Array.isArray(flags) || flags.length !== rr.length || flags.some(flag => typeof flag !== 'boolean'))) {
    throw new Error('AF annotations must be one boolean per RR interval.');
  }
  const tachyThreshold = options.tachyThreshold ?? 100;
  const bradyThreshold = options.bradyThreshold ?? 50;
  const cvThreshold = options.cvThreshold ?? 0.15;
  if (![tachyThreshold, bradyThreshold, cvThreshold].every(finitePositive)) {
    throw new Error('All thresholds must be positive finite numbers.');
  }
  const totalTime = rr.reduce((a, b) => a + b, 0);
  if (!Number.isFinite(totalTime)) throw new Error('Total recording duration is too large.');
  const meanRR = totalTime / rr.length;
  const sdnn = sd(rr);
  let sumSq = 0, n50 = 0;
  for (let i = 1; i < rr.length; i++) {
    const delta = rr[i] - rr[i - 1];
    sumSq += delta * delta;
    if (Math.abs(delta) > 50) n50++;
  }

  const minRR = rr.reduce((a, b) => Math.min(a, b));
  const maxRR = rr.reduce((a, b) => Math.max(a, b));
  const tachyTime = rr.reduce((total, v) => total + (v < 60000 / tachyThreshold ? v : 0), 0);
  const bradyTime = rr.reduce((total, v) => total + (v > 60000 / bradyThreshold ? v : 0), 0);
  const pauses = rr.map((v, i) => ({index: i, duration_ms: v})).filter(p => p.duration_ms > 2000);
  const cv = sdnn / meanRR;
  let afTime = 0, afBeats = 0;
  if (flags !== null) {
    rr.forEach((value, i) => {
      if (flags[i]) { afTime += value; afBeats++; }
    });
  } else {
    for (let i = 0; i < rr.length; i++) {
      const start = Math.max(0, i - 15);
      const window = rr.slice(start, Math.min(rr.length, i + 15));
      if (window.length < 5) continue;
      const wMean = window.reduce((a, b) => a + b, 0) / window.length;
      if (sd(window) / wMean > cvThreshold) { afTime += rr[i]; afBeats++; }
    }
  }
  const allWarnings = [];
  if (flags === null) {
    allWarnings.push('No verified ECG annotations: the RR-variability estimate is not a diagnosis or confirmed AF burden.');
    if (rr.length < 5) allWarnings.push('Fewer than five intervals: RR screening cannot classify any window; zero estimated burden is not informative.');
  } else if (flags.some(Boolean)) {
    allWarnings.push('AF present in annotations: RR-derived HRV is not NN-only HRV.');
  }
  if (pauses.length) allWarnings.push('Long RR intervals require ECG review to distinguish pauses from artefact or ectopy.');
  if (cv > cvThreshold) allWarnings.push('Elevated RR variability is nonspecific and cannot diagnose AF.');
  return {
    sample_count: rr.length,
    total_time_ms: totalTime,
    monitoring_hours: round(totalTime / 3600000, 4),
    mean_rr_ms: round(meanRR, 2),
    mean_hr_bpm: round(60000 * rr.length / totalTime, 2),
    min_hr_bpm: round(60000 / maxRR, 2),
    max_hr_bpm: round(60000 / minRR, 2),
    sdnn_ms: round(sdnn, 2),
    rmssd_ms: round(Math.sqrt(sumSq / (rr.length - 1)), 2),
    pnn50_percent: round(100 * n50 / (rr.length - 1), 2),
    irregularity_cv: round(cv, 4),
    tachy_time_percent: round(100 * tachyTime / totalTime, 2),
    brady_time_percent: round(100 * bradyTime / totalTime, 2),
    pauses,
    af_time_ms: afTime,
    af_beat_count: afBeats,
    af_burden_percent: round(100 * afTime / totalTime, 2),
    af_is_estimate: flags === null,
    warnings: allWarnings
  };
}
