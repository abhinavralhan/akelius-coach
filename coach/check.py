"""Deterministic checks a sheet must pass before it is cached or shown."""
import re

from sympy import simplify, sympify

REQUIRED = ["idea", "why", "explanations", "student_questions", "mistakes",
            "worked_examples", "try_it", "lesson_outline"]
# sympify evaluates strings, so model output is whitelisted before it gets there.
SAFE_CHARS = re.compile(r"^[0-9a-zA-Z+\-*/^().,\s]*$")
SAFE_NAMES = {"sqrt", "pi", "Rational"}


def _value(expr):
    if not SAFE_CHARS.match(expr) or set(re.findall(r"[A-Za-z_]+", expr)) - SAFE_NAMES:
        raise ValueError(f"unsafe or unsupported expression: {expr!r}")
    return sympify(expr.replace("^", "**"))


def verify(sheet):
    """Return a list of problems; an empty list means the sheet passes."""
    errors = [f"missing section: {k}" for k in REQUIRED if not sheet.get(k)]
    if len(sheet.get("explanations", [])) != 3:
        errors.append("need exactly 3 explanations")
    for item in sheet.get("worked_examples", []) + sheet.get("try_it", []):
        try:
            if simplify(_value(item["expression"]) - _value(item["answer"])) != 0:
                errors.append(f"wrong answer: {item['problem'][:60]!r}: {item['expression']} != {item['answer']}")
        except Exception as e:  # unparsable math is a failure, never a pass
            errors.append(f"cannot verify {item.get('problem', '')[:60]!r}: {e}")
    text = str({k: sheet.get(k) for k in REQUIRED})
    if re.search(r"https?://|www\.", text):
        errors.append("model-written URL found; links must come from resources.py")
    return errors
