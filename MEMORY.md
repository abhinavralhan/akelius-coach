# Project memory: step log

Read this first. It records every step: what we did, what it achieved and what comes next.
Rule: **after every step, add an entry here in the same commit as the work.** Newest entry at the bottom.

- What we're building: a math teacher coach for Akelius (see the assignment PDF in the repo root).
- Thinking and research: [docs/research-notes.md](docs/research-notes.md). Cost: [docs/cost-model.md](docs/cost-model.md).
- Approved plan: the "Plan" section below.

---

## Plan v2 (revised 2026-11-18 16:46, ~90 minutes of build time left)

Criteria: **P** = product judgment and communication, **A** = architecture and extensibility, **L** = LLM use, answer quality and cost, **D** = documentation and compliance.
Each step ends with a commit and a step-log entry with **start and end times** (they feed the README's "time spent").

| Step | min | Work | Criteria | Done when |
|---|---|---|---|---|
| 1 | 0–8 | git init, remote, venv, requirements.txt, .gitignore; commit the docs | D | first commit |
| 2 | 8–20 | `curriculum/concepts.yaml` (~25 concepts, grades 1–10, standard-neutral); `curriculum/standards/ccss.yaml` (country standard → concept + grade); 3 CC BY excerpts; `curriculum/ATTRIBUTION.md`; each source carries a `license` field | P, A, D | the topic list loads for country=CCSS |
| 3 | 20–40 | `coach/llm.py` (one function, Claude CLI backend, returns text + real cost); `coach/sheet.py` (grounded prompt → JSON sheet, cached per concept + language, `reviewed: false`, labelled AI-generated); generate 3 sheets in the background | A, L | 3 sheets committed |
| 4 | 40–50 | `coach/check.py` (schema + SymPy verification of worked examples); `coach/resources.py` (fixed link templates); one test | L | check passes; the test catches a wrong example |
| 5 | 50–70 | `coach/server.py` + `web/index.html`: topics by standard, sheet, explain, ask. SQLite stores the answer cache, the 50-a-month cap and a spend ledger with a hard budget stop; input length is validated | P, A, L | a second click is a cache hit; feedback is saved |
| 5b | (inside 5) | **Question cache:** typed questions are normalised (case, punctuation, spaces) and matched against earlier questions on the same concept and language. An exact match, or a near-identical match (character similarity ≥ 0.95, order-sensitive), returns the cached answer with no LLM call and shows the matched question ("answer to a similar question: …", with an "ask mine anyway" option). Each hit adds 1 to a counter. `coach/promote.py` copies the most-asked questions per concept into that concept's static sheet as an FAQ, ordered by hit count and marked "not yet reviewed" | P, L | a repeated question costs $0; promote adds the top questions to the sheet |
| 5c | (inside 5) | **Feedback box:** teachers write free-text needs; stored anonymously in SQLite with the topic | P | feedback row saved |
| 6 | 70–80 | `evals/`: 10 cases across grades; rubric + LLM judge; `evals/results.md` | L | results committed |
| 7 | 80–90 | README (run, design and trade-offs, skipped items, time, quality, cost, plain-language data flow, how AI was used); zip with .git; push | D, P | zip built |

**If we run behind, drop in this order:** the eval judge (SymPy stays) → on-demand sheets for new topics → UI polish. The README is never dropped.

---

## Step log

### Step 0: research and planning (prep, before the 2-hour clock) — done 2026-11-18
- **Did:** read the assignment; worked out the teacher problems; researched open-source model math quality, LLM prices and online resource licenses; built the cost model.
- **Decided:** decisions D1–D13 in research-notes.md. Main ones: a prep sheet instead of a chat; shared, cached sheets; a small model on the live path; a cap of 50 queries per teacher per month; a $2k budget enforced in code; copy text only from CC BY sources and link to the rest; SymPy for verification; no accounts.
- **Achieved:** docs/research-notes.md, docs/cost-model.md, this file and CLAUDE.md.
- **Next:** Step 1, once the user says go. That starts the 2-hour clock.

### Step 1: repo setup — 16:46–16:50
- **Did:** `git init` (branch main) and the remote `origin` → github.com/abhinavralhan/akelius-coach (not pushed yet); `.venv` with fastapi, uvicorn, sympy and pyyaml (`requirements.txt`); `.gitignore`.
- **Decided:** the assignment PDF stays local (gitignored), so the brief isn't published to GitHub. Plan v2 adds country standards (D14), the teacher's language (D15), open content only (D16), AI labelling (D17) and the question cache with promotion to the sheets (D18).
- **Achieved:** first commit, containing the docs, the plan and this log.
- **Next:** Step 2, the curriculum (concepts, CCSS mapping, CC BY excerpts, attribution).

### Step 2: curriculum — 16:50–16:53
- **Did:** `curriculum/concepts.yaml` (27 standard-neutral concepts, grades 1–10); `curriculum/standards/ccss.yaml` (each CCSS code → grade + concept; a check confirms every concept is mapped); 3 grounding lessons in `curriculum/lessons/` (dividing fractions, multiplying negative numbers, the Pythagorean theorem), each with its OpenStax section as further reading; `curriculum/ATTRIBUTION.md`.
- **Decided:** we write our own short lessons (CC BY) instead of copying OpenStax text (D20). Native language and sign-up/auth moved to the TODO list (research-notes §6). The question-cache match is strict (≥ 0.95, order-sensitive). Feedback box added (D19). The user set the core principle "trustworthy and reliable", now at the top of the research notes and in CLAUDE.md.
- **Achieved:** all the arithmetic in the lessons is checked with Python. The topic map loads.
- **Note:** the first times written for steps 1–2 were guesses, corrected here with `date`. From now on, all times come from the system clock.
- **Next:** Step 3, `coach/llm.py` + `coach/sheet.py`, then generate 3 sheets.

### Step 3: LLM boundary + sheet generator — 16:53–16:56
- **Did:** `coach/llm.py`, the only place a model is called. It uses the Claude CLI in a lean mode (no tools, no MCP, custom system prompt, so about 1k tokens of overhead instead of about 23k), takes a JSON schema for structured output, returns the real `total_cost_usd`, and raises on any failure. `coach/sheet.py` holds the sheet schema and a grounded prompt; it generates with Sonnet, runs `verify()` and caches the sheet only if it passes. Every sheet carries meta: `ai_generated`, `reviewed: false`, model, cost, grounding lesson, license.
- **Achieved:** 3 sheets in `content/` (dividing fractions, multiplying negative numbers, Pythagoras). All passed the checks first time, at $0.038–0.047 each (the cost model assumed $0.12, so it is conservative).
- **Next:** Step 4.

### Step 4: quality gate + resources — done alongside step 3, 16:53–16:56
- **Did:** `coach/check.py` checks that every section is present, that there are exactly 3 explanations, that every worked example and try-it answer is right (SymPy), and that there are no model-written URLs. Model expressions are whitelisted (characters + `sqrt`, `pi`, `Rational`) before SymPy sees them, because `sympify` evaluates code. `coach/resources.py` builds Khan Academy, Wolfram|Alpha, GeoGebra and Wikipedia links from fixed templates. `tests/test_check.py` has 5 tests, all passing: correct sheet passes, wrong answer caught, code injection rejected, URL rejected, missing section caught.
- **Decided (D21, user):** the main view is only the prep notes for a topic. Ask, explain-differently and feedback go in a secondary side tab, because teachers dislike chatbots and the job is lesson prep.
- **Next:** Step 5, the server + UI. `coach/qa.py` (cap, budget stop, strict question cache, Haiku) is already written.

### Step 5: server, UI, question cache, cap, budget, feedback, drawings — 16:56–17:02
- **Did:**
  - `coach/server.py`: a thin FastAPI layer (topics by standard, sheet, ask, feedback). Unchecked output is never shown: a model or check failure returns a plain message, and nothing is cached.
  - `coach/qa.py`: input validation → monthly cap (50) → strict question cache (exact match, or ≥ 0.95 similarity **and** identical numbers and math symbols) → hard budget stop → Haiku. Spend is recorded from the real CLI cost. A query counts against the cap only when an answer is delivered. Data lives in SQLite: questions with hit counts, usage, spend, feedback.
  - `coach/promote.py`: the most-asked questions per concept go into that sheet's `teacher_faq`, ordered by demand.
  - `web/index.html`: the main view is only the prep notes (D21), printable, with an "AI-generated, not reviewed" banner. "Draw and explore" uses fixed JSXGraph templates (D23): function graph, draggable right triangle, number line, fraction bars. The side panel holds "Ask the coach", explain-differently and feedback. All model text is inserted as text, never as HTML.
  - `tests/test_qa.py`: strict matching, cap, budget stop (and that a refused query isn't counted), input validation. 9/9 tests pass.
- **Achieved:** tested against a throwaway DB. The first question cost $0.00085 with Haiku (the model predicted $0.00081). A repeated question was served from the cache at $0. Bad inputs are rejected. Feedback is saved. Promotion works. The JS passes `node --check`.
- **Not yet verified:** how the drawings look in a real browser.
- **Next:** Step 6, evals.

### Step 6: eval — 17:01–17:05
- **Did:** generated 3 more sheets on demand (fractions as numbers, linear equations, quadratics; all passed checks, $0.029–0.049 each), so there are now 6 sheets. Wrote `evals/cases.yaml` (10 questions, grades 3–9, with traps: a false premise, a notation trap, an off-topic question) and `evals/run.py` (real ask pipeline with Haiku → Sonnet judge with a JSON rubric → `evals/results.md`).
- **Achieved:** correct 10/10, explains why 9/10 (the off-topic case; a rubric limit), plain 10/10, respectful 10/10, honest scope 10/10. Run cost: $0.16.
- **Learned:** run 1 scored honest scope 8/10. The judge didn't see the sheet, so it flagged real references to the sheet as invented. Fixed the eval (the judge now sees the same context). Documented in the results file.
- **Next:** Step 7, finish the README, then zip and push.

### Step 7: README + delivery — 17:05–17:06
- **Did:** README.md covers every item the brief asks for: how to run, product decisions, design and trade-offs, what was skipped, answer quality (tests + eval), cost per teacher and how to lower it, data in plain language, licences, how AI was used, time spent. Checked the README's run steps from a clean start (server up, 6 topics ready). Added the first measured costs and eval results to docs/cost-model.md. Built the zip with `.git`, excluding `.venv`, the local DB and the assignment PDF.
- **Achieved:** the prototype is complete and runs. 9/9 tests pass. Eval run 2 passes every case except one rubric limit.
- **Open:** not pushed to GitHub yet (waiting for the user's go). Drawings not yet checked by eye in a browser.
- **Next (future scope):** research-notes §6: native language, sign-up/auth, educator review screen, more country standards, semantic matching, production LLM backend.

### Step 8: pre-generate the whole library — 17:12–17:15
- **Did:** at the user's request, generated the remaining 21 sheets (6 in parallel), then re-ran `verify()` over all 27.
- **Decided (D24):** check every sheet before launch; on-demand generation is only a fallback for topics added later. Sheets stay as versioned JSON files (reviewable, CDN-ready); SQLite holds the dynamic data. Moving the sheets into the DB is a small change (only `sheet.get`/`generate` touch storage) if we want it later, e.g. for a reviewer UI.
- **Achieved:** 27/27 sheets passed the checks first try. The library cost $1.12. README and cost model updated with the measured numbers. Zip rebuilt.
- **Open:** push to GitHub (waiting for the user); check the drawings by eye in a browser.

### Step 9: lesson-shaped notes, optional drawings, teacher notes, prepared-only serving — 17:15–17:26
- **Did:** restructured the sheets (D25): the plan first, ending with a 10-minute extra round; short theory + example; 2–3 subtopics, each with 2 ways to explain it, an example, an optional drawing (D26), 2 mistakes, 3 student questions and a check question; 3 extra examples. The checker enforces all of it. Added a bars template, so every concept has one. The page removes empty drawings. Teacher notes + a sketch pad, stored only in the browser (D27). Live serves only pre-generated sheets (D28, `COACH_ALLOW_GENERATE=1` in dev). 14 tests pass.
- **Achieved:** 26/27 sheets regenerated and re-verified ($2.28); drawings in 53 of 78 subtopics.
- **Open:** `right-triangle-trig` failed: the Claude CLI hit the account's monthly spend limit (not a content failure). Regenerate it with `python -m coach.sheet right-triangle-trig` once the limit resets; until then it shows "coming soon". The eval was not rerun on the new structure (same limit). README eval numbers are from the previous structure. Not pushed to GitHub.

### Step 10: grade + topic picker
- **Did:** split the single topic dropdown into a **Grade** field and a **Topic** field. The topic list is rebuilt from the chosen grade (disabled until a grade is picked). Both are built from the standard's mapping file via `/api/topics`, so a new standard or topic needs no UI change.
- **Next:** regenerate `right-triangle-trig`, rerun the eval on the new structure, push when the user says go.

### Step 11: "My notes" tab
- **Did:** the main area has two tabs: **Prep notes** (ours) and **My notes** (the teacher's notes for the lesson and each part, plus the sketch pad). The teacher's material no longer sits inside our sections. The tab is built when opened, so the sketch pad gets its real size. Storage is unchanged (browser only).

### Step 12: 97 topics + YouTube videos
- **Did:** expanded the curriculum to 97 concepts (9–10 per grade, CCSS-mapped); pre-generation of the 71 missing sheets is running. Added `coach/videos.py`: top 3 per topic from the official YouTube Data API, each confirmed via oEmbed, saved into the sheet as `videos`, shown at the bottom of the page and labelled as external and not reviewed. Resources are rebuilt from the templates whenever a sheet is served; a "Search YouTube" link is added. `tests/test_videos.py` (fake network) checks bad IDs and unconfirmed videos are skipped. 15/15 tests pass.
- **Open:** needs `YOUTUBE_API_KEY` to fetch the actual videos (not set yet). Until then, the Search YouTube link is shown.

### Step 13: reliable saving in My notes
- **Did:** Save button + autosave (1 s after typing stops). Every write is read back from localStorage; the status line says "All notes saved … at HH:MM" only when confirmed, otherwise "Not saved …" with the text kept on screen. Pending notes are saved before switching tab or topic; a warning appears before leaving with unsaved notes; "Download my notes" gives a .txt backup. The sketch pad uses the same path. `tests/notes_save.test.mjs` runs the real page code against fake storage: normal, throwing (private mode), silently dropping — 3/3 pass.

### Step 14: removed the AI warning banner from the notes page
- **Did:** removed the "Written by AI and checked automatically … read with extra care" banner at the user's request. Kept: the AI label on live answers, and the `ai_generated`/`reviewed` metadata. D17 updated: educator review and a terms-of-use notice now carry the transparency duty before launch.

### Step 15: full test pass (generation still running)
- **Offline:** 15/15 Python unit tests; notes-save test 3/3; page JS syntax ok; curriculum consistent (97 concepts, unique CCSS codes, 9–10 per grade, every concept has a template); every finished sheet (49 at the time) passes `verify()`.
- **API end to end** (throwaway DB, port 8766): 18/18. Index, topics (97), path-traversal standard rejected, ready sheet with all sections + YouTube link, not-ready sheet → "being prepared" 404 with no generation, ask on not-ready → 404, unknown → 404, live Haiku answer, near-identical question served from the cache with the matched question shown, input validation (short/long/bad id), feedback saved/rejected, spend recorded from the real cost ($0.00125), usage counts delivered answers only.
- **Eval:** run 3 caught a real error (a "usually" hedge on Pythagoras). Answer prompt tightened ("always"/"never" for exact facts, a reason for every rule); run 4: correct 10/10, explains why 9/10 (the off-topic rubric limit). History in evals/results.md.
- **Not tested:** rendering in a real browser (no headless Chrome on this machine).
- **Found:** per-answer cost up to $0.00125 with the richer sheets; the next fix is to send only the relevant subtopic (cost-model.md).

### Step 16: library generated (90/97)
- **Achieved:** 90 of 97 sheets generated and verified (0 failing checks); library cost $8.26; drawings in 171 of 270 subtopics (shown only where useful).
- **Open:** 7 grade 9–10 topics (compound-probability, congruent-triangles, data-spread, distance-midpoint, parallel-lines-angles, radicals, volume-of-solids) hit the Claude account's monthly spend limit; they show "coming soon". Regenerate after the limit resets: run `python -m coach.sheet <id>` for each.

### Step 17: audit fixes, README, demo GIF, push
- **Audit fixes (one commit each):** promoted FAQs go to a review queue before going live (#1); indexed question cache (#2); atomic `sheet.save()` shared by all writers (#3); errors logged, not shown to teachers (#4); trimmed live context, about 6× fewer tokens (#5); stale topic responses ignored (#6); `tests/test_api.py`, with the real server in a thread and a fake model (#7); dead code removed (#8–#11). 19 unit/API tests + 3 notes tests pass.
- **README** rewritten: crisp; maps every delivery item and the 4 review criteria; tools, limitations, future scope.
- **docs/demo.gif:** 16 frames recorded from the real app by `docs/make_demo_gif.py` (Playwright, dev-only). The first real-browser check: all features render.
- **Open:** 7 topics pending (spend limit), eval rerun on the trimmed context, YouTube key.
