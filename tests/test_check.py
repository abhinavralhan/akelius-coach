"""Run: python -m unittest tests.test_check"""
import copy
import unittest

from coach.check import verify

SUB = {
    "title": "t", "ways_to_explain": [{"kind": "picture", "text": "p"}, {"kind": "story", "text": "s"}],
    "example": {"problem": "3/4 ÷ 1/2", "steps": "s", "expression": "Rational(3,4)/Rational(1,2)", "answer": "3/2"},
    "visual": {"kind": "fractionbar", "expr": "", "a": 3, "b": 4, "c": 1, "d": 2},
    "mistakes": [{"mistake": "m", "response": "r"}] * 2,
    "student_questions": [{"question": "q", "answer": "a"}] * 3,
    "check_question": {"question": "q", "solution": "s", "expression": "sqrt(3^2 + 4^2)", "answer": "5"},
}
EXTRA = {"problem": "p", "solution": "s", "expression": "2/Rational(1,4)", "answer": "8"}
GOOD = {"lesson_outline": [{"minutes": 30, "activity": "a"}, {"minutes": 10, "activity": "extra examples and questions"}],
        "extra_examples": [EXTRA] * 3,
        "idea": "i", "why": "w", "theory_example": SUB["example"], "subtopics": [SUB, SUB]}


def sheet(**sub_changes):
    s = copy.deepcopy(GOOD)
    s["subtopics"][0].update(sub_changes)
    return s


class CheckTest(unittest.TestCase):
    def test_correct_sheet_passes(self):
        self.assertEqual(verify(GOOD, "fractionbar"), [])

    def test_wrong_answer_is_caught(self):
        bad = {**SUB["example"], "expression": "(-3)*(-2)", "answer": "-6"}
        self.assertTrue(any("wrong answer" in e for e in verify(sheet(example=bad), "fractionbar")))

    def test_code_in_expression_is_rejected_not_run(self):
        bad = {**SUB["check_question"], "expression": "__import__('os').system('echo hacked')", "answer": "0"}
        self.assertTrue(any("unsafe" in e for e in verify(sheet(check_question=bad), "fractionbar")))

    def test_model_written_url_is_rejected(self):
        self.assertTrue(any("URL" in e for e in verify({**GOOD, "idea": "see https://x.y"}, "fractionbar")))

    def test_each_subtopic_needs_its_parts(self):
        errors = verify(sheet(student_questions=SUB["student_questions"][:2], mistakes=[]), "fractionbar")
        self.assertIn("subtopic 1: need 3 student_questions", errors)
        self.assertIn("subtopic 1: need 2 mistakes", errors)

    def test_lesson_must_be_40_minutes(self):
        self.assertIn("lesson outline does not add up to 40 minutes",
                      verify({**GOOD, "lesson_outline": [{"minutes": 30, "activity": "a"}]}, "fractionbar"))

    def test_last_10_minutes_are_the_extra_round(self):
        s = {**GOOD, "lesson_outline": [{"minutes": 10, "activity": "a"}, {"minutes": 30, "activity": "b"}]}
        self.assertIn("the last 10 minutes must be the extra examples and questions round", verify(s, "fractionbar"))

    def test_visual_must_fit_its_template(self):
        self.assertTrue(verify(sheet(visual={**SUB["visual"], "d": 99}), "fractionbar"))
        self.assertTrue(verify(GOOD, "graph"))
        self.assertEqual(verify(sheet(visual={**SUB["visual"], "kind": "none"}), "graph"), [])  # no drawing is allowed
        self.assertTrue(verify(sheet(visual={"kind": "graph", "expr": "x; __import__", "a": 0, "b": 0, "c": 0, "d": 0}), "graph"))


if __name__ == "__main__":
    unittest.main()
