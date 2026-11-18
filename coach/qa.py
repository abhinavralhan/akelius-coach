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
Be mathematically exact: when something is always or never true, say "always" or "never", not "usually".
Give the reason behind every rule, not only the rule. If the question is outside the topic or you are not sure, say so plainly and suggest
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
    try:  # sig/len let the cache fetch only rows that could match (see ask); added to older DBs too
        con.executescript("ALTER TABLE questions ADD COLUMN sig TEXT; ALTER TABLE questions ADD COLUMN len INTEGER;")
    except sqlite3.OperationalError:
        pass  # columns already exist
    con.executescript("""CREATE INDEX IF NOT EXISTS q_exact ON questions (concept, norm);
                         CREATE INDEX IF NOT EXISTS q_near ON questions (concept, sig, len);""")
    return con


def normalise(q):
    return re.sub(r"\s+", " ", q.lower()).strip(" ?.!")


def signature(q):
    """The numbers and math symbols of a question; near-identical questions must share it exactly."""
    return " ".join(re.findall(r"[\d.]+|[-+*/^=<>√²³]", q))


def is_same(a, b):
    """Near-identical only: the math (numbers, operators) must match exactly, the wording almost exactly."""
    return signature(a) == signature(b) and difflib.SequenceMatcher(None, a, b).ratio() >= SIMILAR


def context(s, question):
    """Only what the answer needs: the short theory and part titles, plus the full part the question names
    (as "explain differently" always does). Sending the whole sheet tripled the tokens per answer."""
    ctx = {k: s[k] for k in ("idea", "why", "theory_example")} | {"parts": [t["title"] for t in s["subtopics"]]}
    named = [t for t in s["subtopics"] if t["title"].lower() in question.lower()]
    if named:
        ctx["part"] = {k: v for k, v in named[0].items() if k != "visual"}
    return ctx


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
        # Only rows that can match: the exact text, or same math signature and a length a ratio >= 0.95 allows
        # (2*min/(la+lb) >= 0.95 needs the lengths within ~10%). Indexed, so this stays fast as questions pile up.
        rows = con.execute("SELECT rowid, question, norm, answer FROM questions WHERE concept=? AND norm=?",
                           (concept, norm)).fetchall()
        if not rows and not force:
            rows = con.execute("SELECT rowid, question, norm, answer FROM questions WHERE concept=? AND sig=? "
                               "AND len BETWEEN ? AND ?", (concept, signature(norm), int(len(norm) * .9), int(len(norm) / .9) + 1)).fetchall()
        for rowid, cached_q, cached_norm, answer in rows:
            if cached_norm == norm or is_same(cached_norm, norm):
                con.execute("UPDATE questions SET hits=hits+1 WHERE rowid=?", (rowid,))
                _count(con, teacher, month)
                return {"answer": answer, "cached": True, "matched_question": cached_q, "remaining": remaining}
        spent = (con.execute("SELECT usd FROM spend WHERE month=?", (month,)).fetchone() or [0])[0]
        if spent >= BUDGET:
            raise ValueError("the coach has reached its monthly budget; prep notes and earlier answers still work")
    s = sheets.get(concept)
    answer, cost = complete(SYSTEM, f"Topic: {s['meta']['title']}\nPrep sheet: {context(s, question)}\n\nTeacher's question: {question}",
                            model=ASK_MODEL)
    if re.search(r"https?://|www\.", answer):
        raise RuntimeError("the answer contained a link the coach cannot vouch for, so it was not shown")
    with db() as con:
        con.execute("INSERT INTO spend VALUES (?,?) ON CONFLICT DO UPDATE SET usd=usd+excluded.usd", (month, cost))
        con.execute("INSERT INTO questions (concept, norm, question, answer, hits, created, sig, len) VALUES (?,?,?,?,0,?,?,?)",
                    (concept, norm, question, answer, datetime.now().isoformat(), signature(norm), len(norm)))
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
