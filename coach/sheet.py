"""Prep sheets: generated once per concept, verified, then cached and shared by every teacher."""
import json
import os
import sys
from datetime import date
from pathlib import Path

import yaml

from coach.check import verify
from coach.llm import complete
from coach.resources import links

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
CONCEPTS = {c["id"]: c for c in yaml.safe_load((ROOT / "curriculum/concepts.yaml").read_text())}
SHEET_MODEL = "sonnet"  # one-time generation, shared by all teachers, so quality is worth more than price

_str = {"type": "string"}


def _obj(props):
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def _list(props):
    return {"type": "array", "items": _obj(props)}


_math = {"expression": _str, "answer": _str}  # verified with SymPy in coach/check.py
# Parameters for the fixed drawing templates in web/index.html. The model supplies values, never code.
VISUAL = _obj({"kind": {"type": "string", "enum": ["none", "graph", "triangle", "numberline", "fractionbar", "bars"]},
               "expr": _str, **{k: {"type": "number"} for k in "abcd"}})
SUBTOPIC = _obj({
    "title": _str,
    "ways_to_explain": _list({"kind": {"type": "string", "enum": ["picture", "story", "procedure"]}, "text": _str}),
    "example": _obj({"problem": _str, "steps": _str, **_math}),
    "visual": VISUAL,
    "mistakes": _list({"mistake": _str, "response": _str}),
    "student_questions": _list({"question": _str, "answer": _str}),
    "check_question": _obj({"question": _str, "solution": _str, **_math}),
})
SCHEMA = _obj({
    "lesson_outline": _list({"minutes": {"type": "integer"}, "activity": _str}),
    "idea": _str, "why": _str,
    "theory_example": _obj({"problem": _str, "steps": _str, **_math}),
    "subtopics": {"type": "array", "items": SUBTOPIC},
    "extra_examples": _list({"problem": _str, "solution": _str, **_math}),
})

SYSTEM = """You write lesson-prep notes for math teachers who may lack confidence in the math they teach.
They prepare alone, often the night before. Be warm, plain and precise. Never judge, test or score the teacher.
Rules:
- Mathematical correctness comes first. If a lesson text is given, stay consistent with it and do not add facts beyond standard school math.
- lesson_outline: the core of the teacher's class. A 40-minute lesson (minutes add up to 40). Each step says what the
  teacher does and which subtopic it uses (by its title). The last step is always exactly 10 minutes:
  an extra-examples and questions round that uses extra_examples.
- extra_examples: exactly 3 extra problems with solutions for that final round, mixing the subtopics.
- Short theory for the teacher, read before class: idea = the topic in 2-3 plain sentences; why = why the method
  works, not only how; theory_example = one worked example that shows the whole topic.
- subtopics: 2-3 parts the lesson teaches in order. Each subtopic has:
  - ways_to_explain: exactly 2, of different kinds (picture, story or procedure).
  - example: one worked example with clear steps.
  - visual: a drawing made by the topic's fixed template (given below), only where a drawing truly makes this subtopic
    clearer; then its values must match the example. Otherwise kind "none". Not every subtopic needs one.
  - mistakes: exactly 2 common student mistakes in this subtopic, and how the teacher can respond.
  - student_questions: exactly 3 questions students really ask here ("but why...?"), with answers a teacher can say aloud.
  - check_question: one question the teacher asks the class to check understanding (not a test), with its solution.
- expression/answer: "expression" is a SymPy expression whose value is the answer (only numbers, + - * / ** ( ) sqrt,
  pi, Rational), and "answer" is the exact value (e.g. 15/8, 5, 3*sqrt(2)). If the answer is not a single number,
  put the key number in it (e.g. one solution of an equation, or the count asked for).
- visual values: graph: expr = function(s) of x, several separated by ";" (e.g. "2*x + 1; -x + 4").
  triangle: a, b = leg lengths 1-9. numberline: a, b = integers -20..20; c = 1 to also show a*b, else 0.
  fractionbar: a/b ÷ c/d, whole numbers 1-12 (to show a single fraction a/b, use c=1, d=b).
  bars: up to 4 bars; expr = labels separated by ";" (letters, digits, spaces, %), a-d = values 0-1000 (unused = 0).
  Set unused fields to 0 or "".
- Never write URLs or links."""


def generate(concept_id, model=SHEET_MODEL):
    """Generate, verify and cache a sheet. Raises if the model fails or the sheet fails a check."""
    c = CONCEPTS[concept_id]
    lesson = (ROOT / "curriculum/lessons" / c["lesson"]).read_text() if c.get("lesson") else None
    prompt = f"Topic: {c['title']}\nDrawing template for this topic: {c.get('visual', 'none')}\n\n" + (f"Lesson text to ground the sheet:\n{lesson}" if lesson
                                           else "No checked lesson exists for this topic yet; stay with standard school math.")
    sheet, cost = complete(SYSTEM, prompt, model=model, schema=SCHEMA)
    errors = verify(sheet, c.get("visual"))
    if errors:
        raise ValueError(f"{concept_id}: sheet failed checks, not cached: {errors}")
    sheet["meta"] = {"concept": concept_id, "title": c["title"], "model": model, "cost_usd": round(cost, 5),
                     "generated": date.today().isoformat(), "grounded_on": c.get("lesson"),
                     "license": c.get("license"), "ai_generated": True, "reviewed": False}
    sheet["resources"] = links(c["title"])
    CONTENT.mkdir(exist_ok=True)
    (CONTENT / f"{concept_id}.json").write_text(json.dumps(sheet, indent=2, ensure_ascii=False))
    return sheet


def get(concept_id):
    """A pre-generated, checked sheet. Live teachers only see sheets prepared before launch (D27);
    set COACH_ALLOW_GENERATE=1 in development to generate a missing sheet on first open."""
    if concept_id not in CONCEPTS:
        raise KeyError(concept_id)
    path = CONTENT / f"{concept_id}.json"
    if path.exists():
        s = json.loads(path.read_text())
        s["resources"] = links(CONCEPTS[concept_id]["title"])  # always from the current templates
        return s
    if os.environ.get("COACH_ALLOW_GENERATE") != "1":
        raise LookupError("these notes are not ready yet")
    return generate(concept_id)


if __name__ == "__main__":  # python -m coach.sheet <concept-id> ...
    for cid in sys.argv[1:]:
        s = generate(cid)
        print(cid, "ok", s["meta"]["cost_usd"])
