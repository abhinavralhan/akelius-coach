"""Live questions: monthly cap, hard budget stop, strict question cache, then the small model."""
import difflib
import os
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path

from coach import sheet as sheets
from coach.llm import complete

DB = Path(os.environ.get("COACH_DB", Path(__file__).resolve().parent.parent / "data/coach.db"))
CAP = 50                                                   # live queries per teacher per month
BUDGET = float(os.environ.get("COACH_BUDGET_USD", 2000))   # hard monthly LLM budget, all teachers
SIMILAR = 0.95                                             # deliberately strict; see is_same()
ASK_MODEL = "haiku"

SYSTEM = """You help a math teacher prepare a lesson. They may lack confidence in this topic; never judge them.
Answer their question about the topic in plain, warm language, under 200 words, using the prep sheet as reference.
Be mathematically exact. If the question is outside the topic or you are not sure, say so plainly and suggest
checking the sheet's resources or a colleague. Never write URLs or links."""


def db():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS questions (concept TEXT, norm TEXT, question TEXT, answer TEXT,
                                              hits INTEGER DEFAULT 0, created TEXT);
        CREATE TABLE IF NOT EXISTS usage (teacher TEXT, month TEXT, count INTEGER, PRIMARY KEY (teacher, month));
        CREATE TABLE IF NOT EXISTS spend (month TEXT PRIMARY KEY, usd REAL);
        CREATE TABLE IF NOT EXISTS feedback (concept TEXT, text TEXT, created TEXT);""")
    return con


def normalise(q):
    return re.sub(r"\s+", " ", q.lower()).strip(" ?.!")


def is_same(a, b):
    """Near-identical only: the math (numbers, operators) must match exactly, the wording almost exactly."""
    math = lambda s: re.findall(r"[\d.]+|[-+*/^=<>√²³]", s)
    return math(a) == math(b) and difflib.SequenceMatcher(None, a, b).ratio() >= SIMILAR


def ask(concept, question, teacher, force=False):
    """Return {answer, cached, matched_question, remaining}. Raises ValueError for a request we refuse."""
    question = question.strip()
    if concept not in sheets.CONCEPTS:
        raise ValueError("unknown topic")
    if not 3 <= len(question) <= 500:
        raise ValueError("please write a question between 3 and 500 characters")
    if not re.fullmatch(r"[\w-]{8,64}", teacher):
        raise ValueError("invalid teacher id")
    month, norm = date.today().strftime("%Y-%m"), normalise(question)
    with db() as con:
        used = (con.execute("SELECT count FROM usage WHERE teacher=? AND month=?", (teacher, month)).fetchone() or [0])[0]
        if used >= CAP:
            raise ValueError(f"you have used all {CAP} questions this month; the prep notes stay available")
        remaining = CAP - used - 1  # a query counts only once an answer is delivered (see _count)
        for rowid, cached_q, cached_norm, answer in con.execute(
                "SELECT rowid, question, norm, answer FROM questions WHERE concept=?", (concept,)).fetchall():
            if cached_norm == norm or (not force and is_same(cached_norm, norm)):
                con.execute("UPDATE questions SET hits=hits+1 WHERE rowid=?", (rowid,))
                _count(con, teacher, month)
                return {"answer": answer, "cached": True, "matched_question": cached_q, "remaining": remaining}
        spent = (con.execute("SELECT usd FROM spend WHERE month=?", (month,)).fetchone() or [0])[0]
        if spent >= BUDGET:
            raise ValueError("the coach has reached its monthly budget; prep notes and earlier answers still work")
    s = sheets.get(concept)
    context = {k: s[k] for k in ("idea", "why", "subtopics")}
    answer, cost = complete(SYSTEM, f"Topic: {s['meta']['title']}\nPrep sheet: {context}\n\nTeacher's question: {question}",
                            model=ASK_MODEL)
    if re.search(r"https?://|www\.", answer):
        raise RuntimeError("the answer contained a link the coach cannot vouch for, so it was not shown")
    with db() as con:
        con.execute("INSERT INTO spend VALUES (?,?) ON CONFLICT DO UPDATE SET usd=usd+excluded.usd", (month, cost))
        con.execute("INSERT INTO questions VALUES (?,?,?,?,0,?)", (concept, norm, question, answer, datetime.now().isoformat()))
        _count(con, teacher, month)
    return {"answer": answer, "cached": False, "matched_question": None, "remaining": remaining}


def _count(con, teacher, month):
    con.execute("INSERT INTO usage VALUES (?,?,1) ON CONFLICT DO UPDATE SET count=count+1", (teacher, month))


def feedback(concept, text):
    text = text.strip()
    if not 3 <= len(text) <= 2000:
        raise ValueError("please write between 3 and 2000 characters")
    with db() as con:
        con.execute("INSERT INTO feedback VALUES (?,?,?)", (concept or None, text, datetime.now().isoformat()))
