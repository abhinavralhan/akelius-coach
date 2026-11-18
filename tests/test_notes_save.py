"""Run: python -m unittest tests.test_notes_save — runs the real My-notes save code from web/index.html in Node
against fake browser storage (normal, blocked, silently dropping). Skipped if Node is not installed."""
import shutil
import subprocess
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "web/index.html"
JS = r"""
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const html = readFileSync(process.argv[1], 'utf8');
const code = html.slice(html.indexOf('// Every write is read back'), html.indexOf('// "My notes" tab'));
function run(storage) {
  const status = {textContent: '', className: ''};
  const env = {localStorage: storage, $: id => (id === 'savestatus' ? status : null), addEventListener() {}};
  const api = new Function(...Object.keys(env), code + '; return {changed, saveAll, pending, value};')(...Object.values(env));
  return {api, status};
}
const memory = () => { const m = new Map(); return {getItem: k => m.has(k) ? m.get(k) : null, setItem: (k, v) => m.set(k, String(v)), m}; };
{ const st = memory(); const {api, status} = run(st);  // normal browser: saved and confirmed
  api.changed('t:lesson', 'Use fraction bars first'); assert.equal(api.saveAll(), true);
  assert.equal(st.m.get('coach:t:lesson'), 'Use fraction bars first'); assert.equal(api.pending.size, 0);
  assert.match(status.textContent, /All notes saved/); }
{ const {api, status} = run({getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }});  // private mode
  api.changed('t:lesson', 'keep me'); assert.equal(api.saveAll(), false);
  assert.match(status.textContent, /Not saved/); assert.equal(api.value('t:lesson'), 'keep me'); }
{ const {api, status} = run({getItem: () => null, setItem() {}});  // write silently dropped: read-back must catch it
  api.changed('t:part1', 'lost?'); assert.equal(api.saveAll(), false); assert.match(status.textContent, /Not saved/); }
"""


@unittest.skipUnless(shutil.which("node"), "Node.js not installed")
class NotesSaveTest(unittest.TestCase):
    def test_saves_are_verified_in_all_storage_cases(self):
        r = subprocess.run(["node", "--input-type=module", "-e", JS, str(PAGE)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
