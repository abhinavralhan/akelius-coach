"""Prep sheets: generated once per concept, verified, then cached and shared by every teacher."""
import json
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
_list = lambda props: {"type": "array", "items": {"type": "object", "properties": props,
                                                  "required": list(props), "additionalProperties": False}}
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "idea": _str, "why": _str,
        "explanations": _list({"kind": {"type": "string", "enum": ["picture", "story", "procedure"]}, "text": _str}),
        "student_questions": _list({"question": _str, "answer": _str}),
        "mistakes": _list({"mistake": _str, "response": _str}),
        "worked_examples": _list({"problem": _str, "steps": _str, "expression": _str, "answer": _str}),
        "try_it": _list({"problem": _str, "solution": _str, "expression": _str, "answer": _str}),
        "lesson_outline": _list({"minutes": {"type": "integer"}, "activity": _str}),
    },
}
SCHEMA["required"] = list(SCHEMA["properties"])

SYSTEM = """You write lesson-prep sheets for math teachers who may lack confidence in the math they teach.
They prepare alone, often the night before. Be warm, plain and precise. Never judge, test or score the teacher.
Rules:
- Mathematical correctness comes first. If a lesson text is given, stay consistent with it and do not add facts beyond standard school math.
- "why" explains why the method works, not only how.
- explanations: exactly 3, one each of kind picture, story, procedure.
- student_questions: 3-4 questions students really ask ("but why...?"), with answers a teacher can say aloud.
- mistakes: 3 common student mistakes and how the teacher can respond.
- worked_examples: 2-3; try_it: 3. For each, "expression" is a SymPy expression whose value is the answer
  (use only numbers, + - * / ** ( ) sqrt, pi, Rational), and "answer" is the exact value (e.g. 15/8, 5, 3*sqrt(2)).
- lesson_outline: a 40-minute lesson, minutes add up to 40.
- Never write URLs or links."""


def generate(concept_id, model=SHEET_MODEL):
    """Generate, verify and cache a sheet. Raises if the model fails or the sheet fails a check."""
    c = CONCEPTS[concept_id]
    lesson = (ROOT / "curriculum/lessons" / c["lesson"]).read_text() if c.get("lesson") else None
    prompt = f"Topic: {c['title']}\n\n" + (f"Lesson text to ground the sheet:\n{lesson}" if lesson
                                           else "No checked lesson exists for this topic yet; stay with standard school math.")
    sheet, cost = complete(SYSTEM, prompt, model=model, schema=SCHEMA)
    errors = verify(sheet)
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
    """Cached sheet if present, else generate it once (the first teacher pays, everyone after reads the file)."""
    if concept_id not in CONCEPTS:
        raise KeyError(concept_id)
    path = CONTENT / f"{concept_id}.json"
    return json.loads(path.read_text()) if path.exists() else generate(concept_id)


if __name__ == "__main__":  # python -m coach.sheet <concept-id> ...
    for cid in sys.argv[1:]:
        s = generate(cid)
        print(cid, "ok", s["meta"]["cost_usd"])
