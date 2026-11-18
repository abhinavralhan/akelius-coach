// Run: node tests/notes_save.test.mjs  — exercises the real save code from web/index.html with fake browser storage.
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const html = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
const code = html.slice(html.indexOf('// Every write is read back'), html.indexOf('// "My notes" tab'));

function run(storage) {
  const status = {textContent: '', className: ''};
  const env = {localStorage: storage, $: id => (id === 'savestatus' ? status : null), addEventListener() {}};
  const api = new Function(...Object.keys(env), code + '; return {changed, saveAll, pending, value};')(...Object.values(env));
  return {api, status};
}
const memory = () => { const m = new Map(); return {getItem: k => m.has(k) ? m.get(k) : null, setItem: (k, v) => m.set(k, String(v)), m}; };

// 1. Normal browser: saved, confirmed, nothing pending.
{ const st = memory(); const {api, status} = run(st);
  api.changed('t:lesson', 'Use fraction bars first'); assert.equal(api.saveAll(), true);
  assert.equal(st.m.get('coach:t:lesson'), 'Use fraction bars first'); assert.equal(api.pending.size, 0);
  assert.match(status.textContent, /All notes saved/); }
// 2. Private mode: storage throws. Must say "Not saved" and keep the text in memory.
{ const {api, status} = run({getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }});
  api.changed('t:lesson', 'keep me'); assert.equal(api.saveAll(), false);
  assert.match(status.textContent, /Not saved/); assert.equal(api.value('t:lesson'), 'keep me'); }
// 3. Storage silently drops the write: the read-back check must catch it.
{ const {api, status} = run({getItem: () => null, setItem() {}});
  api.changed('t:part1', 'lost?'); assert.equal(api.saveAll(), false); assert.match(status.textContent, /Not saved/); }
console.log('notes save: 3/3 ok');
