"""Most-asked questions → a review queue; an educator approves them into the live notes.
Teachers' typed questions can contain names or class details, so nothing reaches other teachers unreviewed.
Run: python -m coach.promote            (writes content/faq_review/<topic>.json)
     python -m coach.promote approve <topic>   (after editing/removing entries in that file)"""
import json
import sys

from coach import qa, sheet

REVIEW = sheet.CONTENT / "faq_review"


def promote(top_n=5):
    with qa.db() as con:
        rows = con.execute("SELECT concept, question, answer, hits FROM questions WHERE hits >= 1 "
                           "ORDER BY concept, hits DESC").fetchall()
    by_concept = {}
    for concept, question, answer, hits in rows:
        faq = by_concept.setdefault(concept, [])
        if len(faq) < top_n:
            faq.append({"question": question, "answer": answer, "asked": hits + 1})
    REVIEW.mkdir(parents=True, exist_ok=True)
    for concept, faq in by_concept.items():
        (REVIEW / f"{concept}.json").write_text(json.dumps(faq, indent=2, ensure_ascii=False))
        print(concept, len(faq), "questions waiting for review")


def approve(concept):
    """Move a reviewed FAQ file into the live sheet."""
    path = REVIEW / f"{concept}.json"
    s = json.loads((sheet.CONTENT / f"{concept}.json").read_text())
    s["teacher_faq"] = json.loads(path.read_text())
    sheet.save(concept, s)
    path.unlink()
    print(concept, len(s["teacher_faq"]), "approved into the notes")


if __name__ == "__main__":
    approve(sys.argv[2]) if sys.argv[1:2] == ["approve"] else promote()
