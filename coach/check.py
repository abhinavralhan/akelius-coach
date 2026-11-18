"""Deterministic checks a sheet must pass before it is cached or shown."""
import re

from sympy import simplify, sympify

REQUIRED = ["lesson_outline", "idea", "why", "theory_example", "subtopics", "extra_examples"]
SUB_COUNTS = {"ways_to_explain": 2, "mistakes": 2, "student_questions": 3}
# sympify evaluates strings, so model output is whitelisted before it gets there.
SAFE_CHARS = re.compile(r"^[0-9a-zA-Z+\-*/^().,\s]*$")
SAFE_NAMES = {"sqrt", "pi", "Rational"}


def _safe_expr(expr, extra=()):
    return bool(SAFE_CHARS.match(expr)) and not set(re.findall(r"[A-Za-z_]+", expr)) - SAFE_NAMES - set(extra)


def _value(expr):
    if not _safe_expr(expr):
        raise ValueError(f"unsafe or unsupported expression: {expr!r}")
    return sympify(expr.replace("^", "**"))


def _visual_errors(v, template):
    """Drawing values are data for a fixed template; check they fit it before any browser draws them."""
    if v["kind"] == "none":  # no drawing is fine: only where it helps
        return []
    if v["kind"] != template:
        return [f"visual kind {v['kind']!r} does not match this topic's template {template!r}"]
    a, b, c, d = (v[k] for k in "abcd")
    whole = lambda *ns, lo, hi: all(float(n).is_integer() and lo <= n <= hi for n in ns)
    ok = {"graph": lambda: _safe_expr(v["expr"].replace(";", " "), {"x"}),
          "triangle": lambda: 1 <= a <= 9 and 1 <= b <= 9,
          "numberline": lambda: whole(a, b, lo=-20, hi=20) and c in (0, 1),
          "fractionbar": lambda: whole(a, b, c, d, lo=1, hi=12),
          "bars": lambda: bool(re.fullmatch(r"[\w %;.,/-]{1,120}", v["expr"])) and all(0 <= n <= 1000 for n in (a, b, c, d))}
    return [] if ok[v["kind"]]() else [f"visual values out of range for {v['kind']}: {v}"]


def _math_errors(item, label):
    try:
        if simplify(_value(item["expression"]) - _value(item["answer"])) != 0:
            return [f"wrong answer in {label}: {item['expression']} != {item['answer']}"]
    except Exception as e:  # unparsable math is a failure, never a pass
        return [f"cannot verify {label}: {e}"]
    return []


def verify(sheet, template=None):
    """Return a list of problems; an empty list means the sheet passes."""
    errors = [f"missing section: {k}" for k in REQUIRED if not sheet.get(k)]
    if sum(step.get("minutes", 0) for step in sheet.get("lesson_outline", [])) != 40:
        errors.append("lesson outline does not add up to 40 minutes")
    if sheet.get("theory_example"):
        errors += _math_errors(sheet["theory_example"], "theory example")
    if (sheet.get("lesson_outline") or [{}])[-1].get("minutes") != 10:
        errors.append("the last 10 minutes must be the extra examples and questions round")
    if len(sheet.get("extra_examples", [])) != 3:
        errors.append("need 3 extra examples")
    for i, ex in enumerate(sheet.get("extra_examples", []), 1):
        errors += _math_errors(ex, f"extra example {i}")
    if not 2 <= len(sheet.get("subtopics", [])) <= 3:
        errors.append("need 2-3 subtopics")
    for i, sub in enumerate(sheet.get("subtopics", []), 1):
        errors += [f"subtopic {i}: need {n} {k}" for k, n in SUB_COUNTS.items() if len(sub.get(k, [])) != n]
        if len({w["kind"] for w in sub.get("ways_to_explain", [])}) != 2:
            errors.append(f"subtopic {i}: the 2 ways to explain must differ")
        errors += _math_errors(sub["example"], f"subtopic {i} example")
        errors += _math_errors(sub["check_question"], f"subtopic {i} check question")
        errors += _visual_errors(sub["visual"], template) if template else []
    text = str({k: sheet.get(k) for k in REQUIRED})
    if re.search(r"https?://|www\.", text):
        errors.append("model-written URL found; links must come from resources.py")
    return errors
