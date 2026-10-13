import test from 'node:test';
import assert from 'node:assert/strict';
import {analyzeRR, parseRRText, parseCSV} from '../web/calculator.mjs';

test('annotated burden is weighted by elapsed time rather than beats', () => {
  const result = analyzeRR([500, 1500], [true, false]);
  assert.equal(result.af_burden_percent, 25);
  assert.equal(result.mean_hr_bpm, 60);
  assert.equal(result.af_is_estimate, false);
});

test('RR-only output is explicitly labelled as an estimate', () => {
  const result = analyzeRR([600, 1200, 500, 1300, 700, 1000]);
  assert.equal(result.af_is_estimate, true);
  assert.ok(result.warnings.some(w => w.includes('not a diagnosis')));
});

test('CSV parses ECG annotations with a header', () => {
  assert.deepEqual(parseCSV('rr_ms,af\n800,1\n1200,0\n'), {rr:[800,1200], flags:[true,false]});
});

test('CSV handles UTF-8 BOM and quoted columns', () => {
  assert.deepEqual(parseCSV('\uFEFF"rr_ms","af"\n"800","true"\n"900","false"'), {rr:[800,900], flags:[true,false]});
});

test('CSV rejects unknown headers and malformed annotation flags', () => {
  assert.throws(() => parseCSV('age,af\n35,1'), /rr_ms/);
  assert.throws(() => parseCSV('rr_ms,af\n800,maybe'), /Invalid AF/);
});

test('paste input accepts commas, whitespace and lines', () => {
  assert.deepEqual(parseRRText('800, 820\n790;810'), [800,820,790,810]);
});

test('invalid, missing, zero and nonfinite RR inputs fail', () => {
  for (const data of [[800,0], [800,-2], [800,NaN], [800,Infinity], [800], []]) {
    assert.throws(() => analyzeRR(data));
  }
  assert.throws(() => parseRRText('800,unknown'));
});

test('flags must be boolean and exactly match the intervals', () => {
  assert.throws(() => analyzeRR([800,900], [true]));
  assert.throws(() => analyzeRR([800,900], [1,0]));
});

test('threshold validation rejects zero and NaN', () => {
  assert.throws(() => analyzeRR([800,900], null, {tachyThreshold:0}));
  assert.throws(() => analyzeRR([800,900], null, {bradyThreshold:NaN}));
});

test('pause, rate burden and baseline HRV remain correct', () => {
  const r = analyzeRR([500, 1000, 3500], [true, true, true]);
  assert.equal(r.af_burden_percent,100);
  assert.equal(r.tachy_time_percent,10);
  assert.equal(r.pauses.length,1);
  assert.equal(r.pnn50_percent,100);
});

test('larger recordings avoid JavaScript argument-spread overflow', () => {
  const data = Array(60000).fill(800);
  const r = analyzeRR(data);
  assert.equal(r.mean_hr_bpm,75);
  assert.equal(r.af_is_estimate,true);
});

test('CSV rejects empty RR cells', () => {
  assert.throws(() => parseCSV('rr_ms,af\n,1\n800,0'), /Invalid rr_ms/);
});
