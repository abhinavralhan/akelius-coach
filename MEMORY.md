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
| 5 | 50–70 | `coach/server.py` + `web/index.html`: topics by standard, sheet, explain, ask. Answers in the teacher's language; `dir=auto` for right-to-left scripts. SQLite stores the answer cache, the 50-a-month cap and a spend ledger with a hard budget stop; input length is validated | P, A, L | a second click is a cache hit; a question in Arabic or Ukrainian is answered in that language |
| 5b | (inside 5) | **Question cache:** typed questions are normalised (case, punctuation, spaces) and matched against earlier questions on the same concept and language. An exact match, or a near match (token similarity ≥ 0.85), returns the cached answer with no LLM call and shows the matched question ("answer to a similar question: …", with an "ask mine anyway" option). Each hit adds 1 to a counter. `coach/promote.py` copies the most-asked questions per concept into that concept's static sheet as an FAQ, ordered by hit count and marked "not yet reviewed" | P, L | a repeated question costs $0; promote adds the top questions to the sheet |
| 6 | 70–80 | `evals/`: 10 cases across grades, including 2 non-English; rubric + LLM judge; `evals/results.md` | L | results committed |
| 7 | 80–90 | README (run, design and trade-offs, skipped items, time, quality, cost, plain-language data flow, how AI was used); zip with .git; push | D, P | zip built |

**If we run behind, drop in this order:** the eval judge (SymPy stays) → on-demand sheets for new topics → UI polish. The README is never dropped.

---

## Step log

### Step 0: research and planning (prep, before the 2-hour clock) — done 2026-11-18
- **Did:** read the assignment; worked out the teacher problems; researched open-source model math quality, LLM prices and online resource licenses; built the cost model.
- **Decided:** decisions D1–D13 in research-notes.md. Main ones: a prep sheet instead of a chat; shared, cached sheets; a small model on the live path; a cap of 50 queries per teacher per month; a $2k budget enforced in code; copy text only from CC BY sources and link to the rest; SymPy for verification; no accounts.
- **Achieved:** docs/research-notes.md, docs/cost-model.md, this file and CLAUDE.md.
- **Next:** Step 1, once the user says go. That starts the 2-hour clock.

### Step 1: repo setup — 16:46–16:55
- **Did:** `git init` (branch main) and the remote `origin` → github.com/abhinavralhan/akelius-coach (not pushed yet); `.venv` with fastapi, uvicorn, sympy and pyyaml (`requirements.txt`); `.gitignore`.
- **Decided:** the assignment PDF stays local (gitignored), so the brief isn't published to GitHub. Plan v2 adds country standards (D14), the teacher's language (D15), open content only (D16), AI labelling (D17) and the question cache with promotion to the sheets (D18).
- **Achieved:** first commit, containing the docs, the plan and this log.
- **Next:** Step 2, the curriculum (concepts, CCSS mapping, CC BY excerpts, attribution).
