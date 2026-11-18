"""Answer-quality eval. Run: python -m evals.run   (writes evals/results.md; uses a throwaway DB, no cache)
Each case goes through the real ask pipeline (Haiku), then a stronger model (Sonnet) grades it on a fixed rubric."""
import os
import tempfile
from pathlib import Path

import yaml

os.environ["COACH_DB"] = str(Path(tempfile.mkdtemp()) / "eval.db")
from coach import qa  # noqa: E402  (after COACH_DB is set)
from coach import sheet  # noqa: E402
from coach.llm import complete  # noqa: E402

HERE = Path(__file__).parent
RUBRIC = ["correct", "explains_why", "plain_language", "respectful", "honest_scope"]
JUDGE = """You grade answers a teaching assistant gave to a math teacher. Be strict about mathematics.
correct: the math is right and matches the expected content. explains_why: it gives a reason, not only a rule.
plain_language: a teacher with shaky confidence would understand it. respectful: no judging or talking down.
honest_scope: it corrects false premises and declines off-topic questions instead of making things up.
The answerer was given the teacher's prep sheet (shown to you too), so references to it are legitimate if they match it."""
SCHEMA = {"type": "object", "additionalProperties": False, "required": RUBRIC + ["note"],
          "properties": {**{k: {"type": "boolean"} for k in RUBRIC}, "note": {"type": "string"}}}


def main():
    rows, totals, cost = [], dict.fromkeys(RUBRIC, 0), 0.0
    cases = yaml.safe_load((HERE / "cases.yaml").read_text())
    for i, c in enumerate(cases, 1):
        before = _spent()
        try:
            answer = qa.ask(c["concept"], c["question"], "eval-runner-0001", force=True)["answer"]
        except Exception as e:  # a refused or failed answer is scored, not hidden
            answer = f"(no answer: {e})"
        cost += _spent() - before
        grade, judge_cost = complete(JUDGE, f"Prep sheet the answerer saw: {_context(c['concept'])}\n\n"
                                     f"Question: {c['question']}\nExpected: {c['expect']}\nAnswer: {answer}",
                                     model="sonnet", schema=SCHEMA)
        cost += judge_cost
        for k in RUBRIC:
            totals[k] += grade[k]
        marks = " | ".join("✓" if grade[k] else "✗" for k in RUBRIC)
        rows.append(f"| {i} | {c['concept']} | {c['question']} | {marks} | {grade['note']} |")
        print(i, marks)
    n = len(cases)
    out = ["# Eval results", "", f"{n} teacher questions, answered by the live pipeline (Claude Haiku 5.5), graded by Claude Sonnet 5.5 on a fixed rubric.",
           f"Total cost of this run: ${cost:.4f}.", "",
           "| Criterion | Passed |", "|---|---|", *[f"| {k} | {totals[k]}/{n} |" for k in RUBRIC], "",
           "| # | Concept | Question | " + " | ".join(RUBRIC) + " | Judge note |", "|---|---|---|" + "---|" * len(RUBRIC) + "---|", *rows]
    (HERE / "results.md").write_text("\n".join(out) + "\n")


def _context(concept):  # the same sheet sections the live pipeline sends (see coach/qa.py)
    s = sheet.get(concept)
    return {k: s[k] for k in ("idea", "why", "explanations", "mistakes", "student_questions")}


def _spent():
    with qa.db() as con:
        return sum(r[0] for r in con.execute("SELECT usd FROM spend"))


if __name__ == "__main__":
    main()
