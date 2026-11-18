"""Run: python -m unittest tests.test_promote  (temp DB and content dir; no LLM)"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coach import promote, qa, sheet


class PromoteTest(unittest.TestCase):
    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        qa.DB, self.content = tmp / "t.db", tmp / "content"
        self.content.mkdir()
        shutil.copy(Path("content/dividing-fractions.json"), self.content)
        self.saved = sheet.CONTENT, promote.REVIEW
        sheet.CONTENT, promote.REVIEW = self.content, self.content / "faq_review"
        with qa.db() as con:
            con.execute("INSERT INTO questions VALUES ('dividing-fractions','n','My student Lina in 6B is stuck','a',2,'t')")

    def tearDown(self):
        sheet.CONTENT, promote.REVIEW = self.saved

    def test_promoted_questions_wait_for_review_before_reaching_teachers(self):
        promote.promote()
        live = json.loads((self.content / "dividing-fractions.json").read_text())
        self.assertNotIn("teacher_faq", live)  # a pupil's name must not go live unreviewed
        queued = json.loads((promote.REVIEW / "dividing-fractions.json").read_text())
        self.assertEqual(queued[0]["question"], "My student Lina in 6B is stuck")
        promote.approve("dividing-fractions")  # the educator approves the (edited) file
        live = json.loads((self.content / "dividing-fractions.json").read_text())
        self.assertEqual(len(live["teacher_faq"]), 1)
        self.assertFalse((promote.REVIEW / "dividing-fractions.json").exists())


if __name__ == "__main__":
    unittest.main()
