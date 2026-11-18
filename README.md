# Lesson Prep Coach: a math coach for teachers

Math teachers who lack confidence in a topic open the coach the evening before a lesson, pick the topic, and get **prep notes laid out the way the lesson is taught**:

1. **What the lesson covers**: the 2–3 subtopics, plus a **40-minute lesson plan** (the core of the class). The last 10 minutes are always an extra-examples and questions round.
2. **Short theory**: the idea, why it works, and one worked example. This is a refresher for the teacher.
3. **Each subtopic, in teaching order**:
   - 2 ways to explain it;
   - a worked example, with an interactive drawing where one helps;
   - 2 common mistakes and how to respond;
   - 3 questions students may ask, with answers;
   - a check question for the class.
4. **Extra examples** for the final 10 minutes.

Teachers can add **their own notes** to the lesson and to each part, and use a **sketch pad**. Both are saved only in their browser.

It is not a chatbot. The notes are the product. An optional side panel lets a teacher ask one question or have a part explained differently.

Built as a prototype for the Akelius assignment "AI engineer, math teacher coach". The guiding principle: **trustworthy and reliable before anything else.** A teacher repeats what the coach says in front of a class, so a wrong answer is worse than no answer.

## How to run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn coach.server:app --port 8000      # open http://127.0.0.1:8000
```

You need the [Claude Code CLI](https://claude.com/claude-code), logged in. It is the development LLM backend (see "Design"). 26 of 27 topics (grades 1–10) have notes pre-generated and checked in `content/` (`right-triangle-trig` is pending: the generation run hit an account usage limit). Live, only these are served (D28). To generate a missing topic on first open in development, start with `COACH_ALLOW_GENERATE=1`.

```bash
.venv/bin/python -m unittest tests.test_check tests.test_qa   # 9 tests, no LLM calls
.venv/bin/python -m evals.run                                 # answer-quality eval → evals/results.md
.venv/bin/python -m coach.sheet pythagorean-theorem           # (re)generate one sheet
.venv/bin/python -m coach.promote                             # move most-asked questions into the sheets
```

## What the coach does, and why (product decisions)

The teachers in the brief learn alone, dislike chatbots, and don't want tests, scores or judgment. The problems I designed for:
1. They know the procedure but not **why** it works.
2. They fear a student's "but why?".
3. They have only one way to explain a topic.
4. They can't predict student mistakes.
5. They prepare late, with little time.
6. They have no safe person to ask.

Each section of the prep notes answers one of these. The full reasoning, with 23 decisions and the alternatives rejected, is in [docs/research-notes.md](docs/research-notes.md).

- **The notes come first, the AI second.** The main view is only the notes, printable. "Ask the coach", "explain differently" and "tell us what you need" sit in a side panel.
- **No tests or scores for the teacher.** Check questions are for the teacher's students. Answers are behind "show answer", and nothing is recorded or scored.
- **Drawings where they help** (JSXGraph, open source). Never empty: a drawing that can't render is removed. They come from five fixed templates: function graph, draggable right triangle, number line, fraction bars, bar chart. The AI supplies only the values, matched to that subtopic's example; the checker validates them, and the teacher can edit them. Every concept has a template.
- **Country-neutral content.** Notes are keyed to a math *concept*. A country's standard is one mapping file (`curriculum/standards/ccss.yaml`: code → grade → concept). The demo uses Common Core, grades 1–10 (27 concepts).

## Design and trade-offs

```
curriculum/   concepts.yaml (standard-neutral) · standards/ccss.yaml · lessons/ (our CC BY lessons) · ATTRIBUTION.md
coach/llm.py        the ONLY place a model is called (swap the backend here)
coach/sheet.py      concept → grounded prompt → structured JSON → verify → cache in content/
coach/check.py      deterministic gate: all sections present, every answer recomputed with SymPy, no model-written URLs
coach/resources.py  enrichment links from fixed templates (Khan Academy, Wolfram|Alpha, GeoGebra, Wikipedia)
coach/qa.py         live questions: validation → monthly cap → strict question cache → budget stop → small model
coach/promote.py    most-asked questions → FAQ section of the static sheet, ordered by demand
coach/server.py     thin FastAPI layer        web/index.html   one page, no framework, no login
evals/              10 teacher questions + rubric, graded by a stronger model
```

| Decision | Trade-off |
|---|---|
| **Generate and check all notes before launch, then share them** with every teacher (D24) | Nothing reaches a teacher unchecked, and nobody waits. Notes are versioned JSON files (reviewable diffs, CDN-ready); dynamic data is in SQLite. Topics added later fall back to generate-on-first-open. The cost doesn't grow with the number of teachers, and an educator can review each sheet once. |
| **Strong model (Sonnet) for notes, small model (Haiku) for live questions** | Notes are generated once, so quality is worth the price. Live questions are the cost driver, and only small models fit the budget (see cost). |
| **Ground notes in short lessons we wrote** (`curriculum/lessons/`, CC BY) | They have to be written and checked by hand, but the model then elaborates on checked facts instead of its memory. Topics without a lesson are labelled. |
| **SymPy verifies every worked answer**; model expressions are whitelisted first, because `sympify` evaluates code | It checks the arithmetic, not the wording of the problem. A sheet that fails is never cached or shown. |
| **Strict question cache:** reuse an answer only on an exact match, or ≥ 0.95 similarity *and* identical numbers and symbols | It misses many paraphrases (a lower hit rate). In exchange, "why is 1/2 > 1/3" can never get the answer to "why is 1/3 > 1/2". The matched question is always shown, with "ask mine anyway". |
| **Hard monthly budget in code** ($2k): when it's reached, new questions stop, while notes and cached answers keep working | Some teachers may meet the limit late in a month, but the bill can never be exceeded. |
| **Development backend is the Claude Code CLI** (`claude -p`, lean mode: no tools, custom system prompt) | It isn't meant for serving 50k teachers. In production, `coach/llm.py` swaps to the Anthropic API (Haiku 5.5) or a hosted open-weight model, whichever wins the eval. It's one function. |
| **SQLite, no framework, no Docker** | Fine for a prototype on one machine; production would use a managed database. |

## What I skipped, and why

- **Answers in the teacher's own language:** the models can do it, but local notation (decimal comma, ÷ vs :) and native-speaker review are the real work. It's first on the TODO list.
- **Sign-up and login:** without them, the 50-question cap uses an anonymous ID stored in the browser, which can be reset. Production should use Akelius's existing login.
- **An educator review screen:** sheets carry `reviewed: false` and show a banner. The approval workflow comes next.
- **Semantic (embedding) question matching:** the upgrade once real logs show which paraphrases the strict match misses.
- **More countries' standards, free-hand drawing (Excalidraw), licensed content:** each is a provision already in the code (a mapping file, a template slot, a `license` field).

Full list: [docs/research-notes.md §6](docs/research-notes.md).

## How we know the coach gives good answers

1. **Grounding:** notes are generated from lessons we checked by hand (their arithmetic is verified with Python).
2. **A deterministic gate:** `coach/check.py` enforces the structure: a 40-minute plan ending with the 10-minute round, and every part in every subtopic. It recomputes every example, check question and extra example with SymPy, and validates every drawing's values. All 27 sheets passed on the first try. Tests prove the gate catches a wrong answer, an injected expression, a model-written URL and a missing section.
3. **Eval** ([evals/results.md](evals/results.md)): 10 teacher questions across grades 3–9 go through the live pipeline. They include traps: a student's wrong answer to correct, a notation trap (−3² vs (−3)²) and an off-topic question. Claude Sonnet grades each answer on a fixed rubric. **Result (on the previous sheet structure; rerun pending): correct 10/10, explains why 9/10 (the 1 is the off-topic question, where there is nothing to explain), plain language 10/10, respectful 10/10, honest about scope 10/10.** The first run caught a flaw in the eval itself (the judge couldn't see the sheet the answers referred to), and the results file documents the fix. Limits: a small sample, a same-family judge, English only.
4. **Honesty in the product:** everything AI-written says so and shows "not yet reviewed". Failures show a plain message, never a broken answer.

## Cost per teacher per month, and how to lower it

Full model with every assumption and a script to rerun: [docs/cost-model.md](docs/cost-model.md).

- **Constraints:** 50k teachers, at most 50 live questions each per month, a $2k monthly budget enforced in code.
- **Worst case** (everyone uses all 50): about **$0.04 per teacher** with Claude Haiku 5.5 (about $1,970 a month). **Realistic case** (half the teachers active, 15 questions each): about **$0.006 per teacher** (about $300 a month).
- **Measured in the prototype:** a live answer cost **$0.00085** (the model predicted $0.00081), and the whole 27-sheet library cost **$1.12** once (about $0.04 per sheet), shared by all teachers.
- **Accuracy is part of the cost:** a cheaper model with more errors costs more once its errors are re-answered by a stronger model. Sonnet or Opus on the live path would cost 15–30× the budget.
- **How to lower it:** caching (repeated questions are free); promoting popular questions into the static notes; low reasoning effort; capped answer length; the Batch API for generating notes; a cheaper open-weight host if the eval shows the same quality.

## Data: what the coach handles and where it goes (plain language)

- **No accounts and no names.** The browser keeps a random ID, used only to count the 50 questions per month.
- **Prep notes** are the same for every teacher and contain nothing personal.
- **When a teacher asks a question**, the question, the topic and the topic's notes are sent to the AI provider (in this prototype Anthropic, through the Claude Code CLI). Nothing that identifies the teacher is sent.
- **Stored on our server** (SQLite): each question and its answer (to reuse for the next teacher), a count of questions per random ID per month, the monthly AI spend, and feedback text. The feedback box asks teachers not to write personal details.
- **Teachers' own notes and sketches** stay in their browser (local storage). They are never sent to our server or to the AI.
- **Not collected:** names, emails, locations, scores, progress.
- **AI transparency:** all generated content is labelled as written by AI and not yet reviewed, in line with the EU AI Act's transparency duties. Akelius is EU-based.
- **Production notes:** choose an LLM provider with EU data processing and no training on inputs; add a retention period for stored questions and feedback.

## Content and licences

We use only openly licensed content: our own lessons (CC BY 4.0), OpenStax (CC BY 4.0) as further reading, Common Core codes (public licence) and JSXGraph (LGPL/MIT). Khan Academy, Wolfram|Alpha, GeoGebra and Wikipedia are links only. See [curriculum/ATTRIBUTION.md](curriculum/ATTRIBUTION.md).

## How AI was used

- **Building:** Claude Code (Claude Opus 5.5) wrote the code and docs with me, step by step. Every step is logged in [MEMORY.md](MEMORY.md).
- **Inside the product:** Claude Sonnet generates the notes, Claude Haiku answers live questions, and Claude Sonnet grades the eval.
- **Not left to AI:** the decisions (logged in the research notes), the lessons' arithmetic (checked with Python) and every answer's math (checked with SymPy) were not trusted to the model.

## Time spent

| Phase | Clock time | What |
|---|---|---|
| Research and planning | before 16:46, same session (not clocked) | Teacher problems, model and price research, licences, cost model, plan. See [docs/research-notes.md §7](docs/research-notes.md) |
| Build, steps 1–7 | 16:46–17:05 | Setup, curriculum, LLM boundary and sheets, quality gate, server and UI, eval, README. Per-step times are in [MEMORY.md](MEMORY.md) |

The brief asks for two hours. The build stayed inside that; the research before it is reported separately so the total is honest.
