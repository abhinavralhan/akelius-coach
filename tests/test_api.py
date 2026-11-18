"""Run: python -m unittest tests.test_api  — the real server in a thread, a temp DB, and a fake model (no LLM, no network)."""
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import uvicorn

from coach import qa, server

PORT = 8799
calls = []


def call(path, body=None):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.load(r) if "json" in r.headers["content-type"] else None
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        qa.DB = Path(tempfile.mkdtemp()) / "api.db"
        qa.complete = lambda *a, **k: calls.append(1) or ("Dividing by 2/5 is undone by multiplying by 5/2.", 0.001)
        cls.server = uvicorn.Server(uvicorn.Config(server.app, port=PORT, log_level="critical"))
        threading.Thread(target=cls.server.run, daemon=True).start()
        while not cls.server.started:
            time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True

    def test_pages_and_topics(self):
        self.assertEqual(call("/")[0], 200)
        status, d = call("/api/topics")
        self.assertEqual((status, len(d["topics"])), (200, 97))
        self.assertEqual(call("/api/topics?standard=..%2Fsecret")[0], 404)  # no path tricks

    def test_sheets(self):
        status, s = call("/api/sheet/dividing-fractions")
        self.assertEqual(status, 200)
        self.assertTrue({"lesson_outline", "theory_example", "subtopics", "extra_examples", "resources"} <= s.keys())
        self.assertEqual(call("/api/sheet/nope")[0], 404)
        missing = next(t["concept"] for t in call("/api/topics")[1]["topics"] if not t["ready"])
        status, e = call(f"/api/sheet/{missing}")
        self.assertEqual(status, 404)  # not prepared yet: "coming soon", never generated live
        self.assertIn("prepared", e["detail"])

    def test_ask_cache_validation_and_feedback(self):
        ask = lambda q, t="api-teacher-01": call("/api/ask", {"concept": "dividing-fractions", "question": q, "teacher": t})
        before = len(calls)
        s1, a1 = ask("Why do we flip the second fraction?")
        s2, a2 = ask("why do we flip the second fraction")
        self.assertEqual((s1, a1["cached"], s2, a2["cached"]), (200, False, 200, True))
        self.assertEqual(len(calls) - before, 1)  # the repeat cost nothing
        self.assertEqual(a2["matched_question"], "Why do we flip the second fraction?")
        for bad in (ask("x"), ask("y" * 501), ask("hello there", t="bad id!")):
            self.assertEqual(bad[0], 400)
        self.assertEqual(call("/api/feedback", {"text": "Please add worksheets"})[0], 200)
        self.assertEqual(call("/api/feedback", {"text": "x"})[0], 400)

    def test_model_failure_shows_plain_message_only(self):
        def boom(*a, **k):
            raise RuntimeError("You've hit your monthly spend limit · raise it at https://claude.ai/settings/usage")
        qa.complete, saved = boom, qa.complete
        try:
            status, e = call("/api/ask", {"concept": "dividing-fractions", "question": "a brand new question?", "teacher": "api-teacher-02"})
        finally:
            qa.complete = saved
        self.assertEqual(status, 502)
        self.assertNotIn("http", e["detail"])  # no internal or billing text reaches teachers


if __name__ == "__main__":
    unittest.main()
