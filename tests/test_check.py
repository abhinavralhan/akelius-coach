"""Run: python -m unittest tests.test_check"""
import unittest

from coach.check import verify

BASE = {
    "idea": "x", "why": "x", "student_questions": [{"question": "q", "answer": "a"}],
    "explanations": [{"kind": k, "text": "t"} for k in ("picture", "story", "procedure")],
    "mistakes": [{"mistake": "m", "response": "r"}], "lesson_outline": [{"minutes": 40, "activity": "a"}],
    "try_it": [{"problem": "3/4 / 2/5", "solution": "s", "expression": "Rational(3,4)/Rational(2,5)", "answer": "15/8"}],
}


def sheet(expression, answer, **extra):
    return {**BASE, "worked_examples": [{"problem": "p", "steps": "s", "expression": expression, "answer": answer}], **extra}


class CheckTest(unittest.TestCase):
    def test_correct_sheet_passes(self):
        self.assertEqual(verify(sheet("sqrt(3^2 + 4^2)", "5")), [])

    def test_wrong_answer_is_caught(self):
        self.assertTrue(any("wrong answer" in e for e in verify(sheet("(-3)*(-2)", "-6"))))

    def test_code_in_expression_is_rejected_not_run(self):
        errors = verify(sheet("__import__('os').system('echo hacked')", "0"))
        self.assertTrue(any("unsafe" in e for e in errors))

    def test_model_written_url_is_rejected(self):
        self.assertTrue(any("URL" in e for e in verify(sheet("1+1", "2", idea="see https://x.y"))))

    def test_missing_section_is_caught(self):
        self.assertIn("missing section: why", verify(sheet("1+1", "2", why="")))


if __name__ == "__main__":
    unittest.main()
