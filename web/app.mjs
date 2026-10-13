import {parseRRText, parseCSV, analyzeRR} from './calculator.mjs';

const el = (id) => document.getElementById(id);
let latest = null;

function status(message, error = false) {
  const target = el('status');
  target.textContent = message;
  target.classList.toggle('error', error);
}

function field(parent, tag, name, value, className = '') {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = value;
  if (name) node.setAttribute(name, value);
  parent.append(node);
  return node;
}

function metric(label, value, unit) {
  const box = field(el('metrics'), 'div', null, '', 'metric');
  field(box, 'span', null, label, 'key');
  field(box, 'span', null, String(value) + (unit ? ' ' + unit : ''), 'value');
}

function detail(label, value) {
  const row = document.createElement('tr');
  field(row, 'td', null, label);
  field(row, 'td', null, String(value));
  el('details').append(row);
}

function render(result) {
  el('empty').hidden = true;
  el('results').hidden = false;
  el('metrics').replaceChildren();
  el('details').replaceChildren();
  el('warnings').replaceChildren();
  el('interpretation').textContent = result.af_is_estimate
    ? 'RR irregularity screening estimate: ' + result.af_burden_percent + '% of analyzed time. Not ECG-confirmed AF.'
    : 'ECG-annotated AF burden: ' + result.af_burden_percent + '% of analyzed time. Verify annotation quality.';
  metric('AF time (' + (result.af_is_estimate ? 'estimate' : 'annotated') + ')', result.af_burden_percent, '%');
  metric('Monitoring duration', result.monitoring_hours, 'h');
  metric('Time-weighted mean HR', result.mean_hr_bpm, 'bpm');
  metric('Tachycardia time', result.tachy_time_percent, '%');
  metric('Bradycardia time', result.brady_time_percent, '%');
  metric('RR intervals', result.sample_count, '');
  detail('Mean RR', result.mean_rr_ms + ' ms');
  detail('SDNN (unfiltered RR)', result.sdnn_ms + ' ms');
  detail('RMSSD (unfiltered RR)', result.rmssd_ms + ' ms');
  detail('pNN50 (unfiltered RR)', result.pnn50_percent + '%');
  detail('RR coefficient of variation', result.irregularity_cv);
  detail('Minimum / maximum instantaneous HR', result.min_hr_bpm + ' / ' + result.max_hr_bpm + ' bpm');
  detail('RR intervals > 2 seconds', result.pauses.length);
  detail('RR intervals > 3 seconds', result.pauses.filter(p => p.duration_ms > 3000).length);
  detail('Time flagged as AF/irregularity', (result.af_time_ms / 60000).toFixed(2) + ' min');
  for (const warning of result.warnings) field(el('warnings'), 'li', null, warning);
  el('export-json').disabled = false;
  el('export-csv').disabled = false;
}

function download(content, mime, filename) {
  const blob = new Blob([content], {type: mime});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function analyze() {
  latest = null;
  el('export-json').disabled = true;
  el('export-csv').disabled = true;
  status('');
  try {
    let dataset;
    const file = el('csv-file').files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) throw new Error('CSV exceeds the 5 MB size limit.');
      dataset = parseCSV(await file.text());
    } else {
      dataset = {rr: parseRRText(el('rr-text').value), flags: null};
    }
    const opts = {tachyThreshold: Number(el('tachy').value), bradyThreshold: Number(el('brady').value)};
    if (!el('tachy').value || !el('brady').value) throw new Error('Both heart-rate thresholds are required.');
    latest = analyzeRR(dataset.rr, dataset.flags, opts);
    render(latest);
    status('Analysis completed locally: ' + latest.sample_count.toLocaleString() + ' intervals.');
  } catch (err) {
    el('results').hidden = true;
    el('empty').hidden = false;
    status(err instanceof Error ? err.message : 'Analysis failed.', true);
  }
}

el('analyze').addEventListener('click', analyze);
el('example').addEventListener('click', () => {
  el('csv-file').value = '';
  el('file-info').textContent = 'Max 5 MB. A selected file takes priority over pasted intervals.';
  el('rr-text').value = '800, 810, 795, 825, 780, 790, 815, 800, 805, 790, 830, 770, 800, 810, 795, 820, 785, 805, 815, 790';
  status('Example RR series loaded. Select Analyze recording.');
});
el('reset').addEventListener('click', () => {
  el('rr-text').value = '';
  el('csv-file').value = '';
  el('file-info').textContent = 'Max 5 MB. A selected file takes priority over pasted intervals.';
  el('tachy').value = '100';
  el('brady').value = '50';
  latest = null;
  el('results').hidden = true;
  el('empty').hidden = false;
  el('export-json').disabled = true;
  el('export-csv').disabled = true;
  status('');
});
el('csv-file').addEventListener('change', () => {
  const file = el('csv-file').files[0];
  el('file-info').textContent = file ? 'Selected: ' + file.name + ' (analyzed locally)' : 'Max 5 MB. A selected file takes priority over pasted intervals.';
});
el('export-json').addEventListener('click', () => {
  if (latest) download(JSON.stringify(latest, null, 2) + '\n', 'application/json', 'holter-af-analysis.json');
});
el('export-csv').addEventListener('click', () => {
  if (!latest) return;
  const rows = [['metric', 'value']];
  Object.entries(latest).forEach(([key, value]) => {
    if (typeof value === 'number' || typeof value === 'boolean') rows.push([key, value]);
  });
  const csv = rows.map(row => row.join(',')).join('\n') + '\n';
  download(csv, 'text/csv', 'holter-af-summary.csv');
});
