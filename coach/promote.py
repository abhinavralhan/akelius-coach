"""Promote the most-asked questions into each static sheet as a FAQ, in order of demand.
Run: python -m coach.promote [top_n]. Promoted answers stay marked not reviewed, like the rest of the sheet."""
import json
import sys

from coach import qa, sheet


def promote(top_n=5, min_hits=1):
    with qa.db() as con:
        rows = con.execute("SELECT concept, question, answer, hits FROM questions WHERE hits >= ? "
                           "ORDER BY concept, hits DESC", (min_hits,)).fetchall()
    by_concept = {}
    for concept, question, answer, hits in rows:
        by_concept.setdefault(concept, [])
        if len(by_concept[concept]) < top_n:
            by_concept[concept].append({"question": question, "answer": answer, "asked": hits + 1})
    for concept, faq in by_concept.items():
        path = sheet.CONTENT / f"{concept}.json"
        if path.exists():  # only sheets that already passed the checks
            s = json.loads(path.read_text())
            s["teacher_faq"] = faq
            path.write_text(json.dumps(s, indent=2, ensure_ascii=False))
            print(concept, len(faq), "promoted")


if __name__ == "__main__":
    promote(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
