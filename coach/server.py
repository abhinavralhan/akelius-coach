"""Web layer only: routes map to coach.sheet and coach.qa. Run: uvicorn coach.server:app"""
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from coach import qa, sheet

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Akelius math teacher coach")


class Ask(BaseModel):
    concept: str
    question: str
    teacher: str
    force: bool = False


class Feedback(BaseModel):
    concept: str | None = None
    text: str


@app.get("/")
def index():
    return FileResponse(ROOT / "web/index.html")


@app.get("/api/topics")
def topics(standard: str = "ccss"):
    path = ROOT / "curriculum/standards" / f"{standard}.yaml"
    if not standard.isalnum() or not path.exists():
        raise HTTPException(404, "unknown standard")
    std = yaml.safe_load(path.read_text())
    return {"standard": std["name"], "topics": [
        {**m, "title": sheet.CONCEPTS[m["concept"]]["title"], "visual": sheet.CONCEPTS[m["concept"]].get("visual"),
         "ready": (sheet.CONTENT / f"{m['concept']}.json").exists(),
         "grounded": bool(sheet.CONCEPTS[m["concept"]].get("lesson"))} for m in std["map"]]}


@app.get("/api/sheet/{concept}")
def get_sheet(concept: str):
    try:
        return sheet.get(concept)
    except KeyError:
        raise HTTPException(404, "unknown topic")
    except (RuntimeError, ValueError) as e:  # model failed or the sheet failed a check: show nothing unverified
        raise HTTPException(502, f"We could not prepare a sheet we can vouch for. Please try again later. ({e})")


@app.post("/api/ask")
def ask(body: Ask):
    try:
        return qa.ask(body.concept, body.question, body.teacher, body.force)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(502, f"No reliable answer this time; nothing was saved. ({e})")


@app.post("/api/feedback")
def feedback(body: Feedback):
    try:
        qa.feedback(body.concept, body.text)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}
