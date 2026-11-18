"""Run: python -m unittest tests.test_qa  (no LLM calls: the model is never reached in these cases)"""
import tempfile
import unittest
from pathlib import Path

from coach import qa


class QaTest(unittest.TestCase):
    def setUp(self):
        qa.DB = Path(tempfile.mkdtemp()) / "t.db"

    def test_strict_match(self):
        n = qa.normalise
        self.assertTrue(qa.is_same(n("Why do we flip the second fraction?"), n("why do we flip the second fraction")))
        self.assertFalse(qa.is_same(n("why is 1/2 > 1/3"), n("why is 1/3 > 1/2")))
        self.assertFalse(qa.is_same(n("why flip the second fraction"), n("why flip the first fraction")))

    def test_monthly_cap_blocks_before_any_model_call(self):
        qa.CAP = 0
        with self.assertRaisesRegex(ValueError, "used all"):
            qa.ask("dividing-fractions", "why flip?", "teacher-abcdefgh")
        qa.CAP = 50

    def test_budget_stop_blocks_new_questions(self):
        qa.BUDGET = 0
        with self.assertRaisesRegex(ValueError, "monthly budget"):
            qa.ask("dividing-fractions", "a brand new question", "teacher-abcdefgh")
        qa.BUDGET = 2000
        with qa.db() as con:  # refused, so it must not use up one of the teacher's 50
            self.assertIsNone(con.execute("SELECT count FROM usage").fetchone())

    def test_input_validation(self):
        for concept, q, t in [("nope", "hello", "teacher-abcdefgh"), ("dividing-fractions", "x", "teacher-abcdefgh"),
                              ("dividing-fractions", "hello", "bad id!")]:
            with self.assertRaises(ValueError):
                qa.ask(concept, q, t)


if __name__ == "__main__":
    unittest.main()
