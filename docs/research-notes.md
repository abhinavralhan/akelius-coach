# Research notes and thought process

The thinking behind the coach: what we found and why we decided what we did. This file is kept up to date as the work goes on.
Started 2026-11-18. This research was prep and is **not** part of the 2-hour build.

---

## Guiding principle: trustworthy and reliable before anything else

Teachers who lack confidence will repeat what the coach tells them in front of a class. A wrong answer does more harm than no answer. So:
- **Grounded:** sheets are generated from checked lessons, not from the model's memory alone.
- **Verified:** the math in worked examples is recomputed with SymPy; any mismatch blocks the sheet.
- **Honest:** everything AI-generated is labelled "not yet reviewed" until an educator approves it; the model is told to say when it isn't sure.
- **No invented links:** URLs come from fixed templates only.
- **Strict reuse:** a cached answer is reused only for a near-identical question, and the matched question is shown.
- **Fails safely:** if the model fails, returns invalid output or the budget is reached, the coach says so plainly; nothing broken is cached or shown.

## 0. The brief in one paragraph

Akelius wants the first part of a coach. It should help math teachers who lack confidence refresh their knowledge and prepare lessons. The teachers learn alone in a browser, dislike chatbots, and don't want tests, scores or certificates. There will be 20k–50k of them, so cost per teacher matters. We get a 2-hour timebox. We choose what the coach does and what material it uses, and we explain and defend those choices. The reviewers judge product judgment, architecture, LLM use (quality and cost), and documentation and compliance.

## 1. Decision log

| # | Decision | Why | Alternatives rejected |
|---|---|---|---|
| D1 | The main form is a **lesson prep sheet** per topic, not a chat | Teachers dislike chatbots. A sheet fits how lessons are really prepared: the night before, in about 15 minutes | Chat tutor (explicitly unwanted); course with quizzes (no tests allowed) |
| D2 | **Live LLM use is in scope**: "explain this differently", one-shot "ask about this topic", and on-demand sheets for new topics | Teachers keep asking new questions about new topics, and a fixed library can't cover everything | Fully static library (cheapest, but can't answer new questions) |
| D3 | **Sheets are generated once and shared** across all teachers, then cached | A sheet depends on the topic, not the teacher. The first teacher pays, everyone after gets it free. Each sheet can be reviewed once by a human | Generating a sheet per request (costs scale with teachers, and quality can't be checked) |
| D4 | The live path uses a **small, cheap model** | Our cost math shows the live path drives the bill, and a large model there costs 20–40× more | Sonnet or Opus for live answers |
| D5 | **The model sits behind a swappable boundary** (`coach/llm.py`). Development uses the local Claude Code CLI | The model can change without touching the product. The open-source vs Claude choice is made by our own eval, not by a benchmark | Writing calls to one provider directly into the code |
| D6 | Scope covers **grades 1–10** through a topic map. Only a few sheets are pre-generated; the rest are generated on demand | The user wants grade 1–10 coverage. On-demand generation plus caching gives it without writing 400 sheets in 2 hours | Covering only fractions |
| D7 | **Enrichment** means copying text only from CC BY sources and linking to everything else. Links come from fixed templates, never from the LLM | This avoids license risk and invented URLs, and costs $0 | Scraping Khan Academy (API shut down, NC license); paid Wolfram API calls |
| D8 | **SymPy** verifies every worked example | It's free, local and deterministic. Wolfram is only a "check it yourself" link | Wolfram API as the verifier (paid in production) |
| D9 | **No accounts, no tracking, no history** | Teachers fear judgment, and GDPR is simplest when there's no personal data | Progress tracking and "streaks" |
| D10 | **A cap of 50 live queries per teacher per month** | It bounds the worst case at 2.5M queries a month, so the cost is predictable | Unlimited use (unbounded cost) |
| D11 | **A $2,000 monthly budget, enforced in code** by a spend ledger. When the budget is reached, the coach serves prep sheets and cached answers only | Haiku's worst case of $1,966 is too close to $2k; a hard stop makes overspending impossible and still leaves teachers something useful | Alerts only (a surprise bill) |
| D12 | **Accuracy is part of the cost**: wrong answers caught by the checks are re-answered by Sonnet, and that cost is counted | It shows that a cheap model with a high error rate isn't really cheap | Comparing models on price per call alone |
| D13 | **The demo runs on the local Claude Code CLI**; production numbers are modelled, not spent | The prototype doesn't need real scale | – |
| D14 | **Country flexibility:** content is keyed by a *concept* that doesn't depend on any standard. Each country's standard is one mapping file (its codes → concept + grade). We start with **Common Core (CCSS)**: it is widely used, well structured, in English and freely licensed | Countries teach the same math in different grades and under different codes. Adding a country is one YAML file, with no change to code or content | One curriculum hard-coded into the topics |
| D15 | **Teacher's own language: moved to TODO**. The demo is English only | Saves build time. Multilingual answers are cheap with current models, but local notation and native-speaker review are the real work | Partial multilingual support with no quality check |
| D16 | **Only openly licensed content and data** go into prompts or the repo (CC BY, CC BY-SA, CCSS public license). Every source has a `license` field, so licensed content could be enabled later through configuration. Links to free sites (Khan, Wolfram) are only links; none of their content is used | It keeps compliance simple, and the user asked for open content only for now | Copying NC or proprietary content |
| D17 | **AI transparency:** every generated sheet and answer is labelled "AI-generated" and "not yet reviewed" | This matches the transparency duty in the EU AI Act; Akelius is EU-based | Unlabelled AI content |
| D19 | **A feedback box for teachers:** free text about what they need, stored anonymously with the topic it was written on | We learn what to build next from the real users. The box warns teachers not to type personal details | Surveys or ratings (feel like judgment) |
| D20 | **Grounding lessons are short texts we wrote ourselves** (released CC BY 4.0), each linking to the matching OpenStax section | The brief allows "a few short lessons you write". It's faster and safer than quoting OpenStax from memory | Verbatim OpenStax excerpts (no time to fetch and check them) |
| D21 | **The main view is only the prep notes for the chosen topic** (printable). "Ask the coach", "explain differently" and feedback sit in a secondary side tab | The core job is preparing a lesson, and teachers dislike chatbots. The notes must be useful without ever touching the AI | A chat-first or mixed layout |
| D22 | **The question cache also needs the numbers and math symbols to match exactly**, on top of ≥ 0.95 similarity | Character similarity alone could treat "why is 1/2 > 1/3" and "why is 1/3 > 1/2" as the same question | Similarity score only |
| D23 | **Interactive drawings on the lesson page use JSXGraph** (open source, LGPL/MIT) through 4 fixed templates: function graph (the teacher types a function), draggable right triangle, number line with sliders, fraction bars (the teacher sets the fractions). Each concept names its template in `concepts.yaml` | Teachers can adjust the drawing for their own class. The templates are fixed code, so the model never writes drawing code. JSXGraph parses typed functions with its own parser, not `eval` | GeoGebra embed (free for non-commercial use only, so it stays a link); Desmos (proprietary, needs an API key); Wolfram\|Alpha images (proprietary, needs a key); Excalidraw free drawing (heavy; TODO) |
| D18 | **Question cache with promotion and a very strict match:** a cached answer is reused only for an exact match after normalisation, or a near-identical one (character similarity ≥ 0.95, order-sensitive). The matched question is always shown. The most-asked questions are promoted into the static sheets in order of demand | Typed questions drive the cost; promoted questions become free for all later teachers. The strict, order-sensitive match means "why is 1/2 > 1/3" never reuses the answer to "why is 1/3 > 1/2" | A looser word-overlap match (risks wrong answers); embedding search (extra model and cost; the upgrade path once we see which paraphrases get missed) |

## 2. Teacher problems (product hypothesis)

1. **They know the procedure but not why it works** (flip and multiply, − × − = +, move the decimal). This is where confidence breaks.
2. **They fear the student's "but why?"** in front of the class.
3. **They have only one way to explain** a topic, with no picture, model or story to fall back on.
4. **They can't predict common mistakes**, so they don't plan for them.
5. **They have little time.** Prep happens the night before.
6. **There is no safe person to ask.** Asking a colleague means admitting a gap.
7. **Many countries and languages.** Wording must be plain and translatable.

**Prep sheet sections (each section answers a problem above):**
- idea in plain words → 1
- why it works → 1
- three ways to explain it → 3
- questions students will ask → 2
- common mistakes → 4
- worked examples and try-it problems (no score) → 1, 6
- 40-minute lesson outline → 5
- resources → enrichment

To validate with real teachers (we haven't yet): which section they actually use first, and whether "questions students will ask" is as valuable as we think.

## 3. Cost findings

The full model, with every assumption, the method, the results and a script you can rerun, is in [cost-model.md](cost-model.md). In short:

- **Constraints:** 50k teachers, a cap of 50 live queries per teacher per month, a $2k monthly budget enforced in code.
- **Caching:** our answer cache serves an estimated 47% of queries (buttons 95%, typed questions 15%). Claude's prompt cache makes the fixed system prompt about 10× cheaper.
- **Worst case (2.5M queries):** Claude Haiku 5.5 costs ~$1,966 a month, DeepSeek V3.2 ~$1,829 and gpt-oss-120b (DeepInfra) ~$1,817; all three fit the budget. Sonnet 5.5 (~$29.8k) and Opus 5.5 (~$59.7k) don't fit.
- **Realistic case (375k queries):** a small model costs ~$275–295 a month, about $0.006 per teacher.
- **Accuracy-adjusted:** gpt-oss is 3× cheaper per call than Haiku, but about $1,400 of its cost is Sonnet re-answering its errors. The cheapest per call isn't the cheapest overall.
- **Prep sheets:** a 2,000-sheet library costs ~$120 once with the Batch API, plus ~$36 a month for new topics.
- **Weakest input:** the per-model error rates are priors. Anthropic hasn't published math benchmark scores for Haiku 5.5. Our eval replaces these priors.

## 4. Open-source model quality findings

- **llm-stats.com:** its headline score combines GPQA, SWE-Bench, coding arena results and price. It is **not a math score**, so don't choose a model from it alone. The top open-weight model shown is Kimi K3.1 Pro (53.9, about $2.38/M).
- **BenchLM math (2026-11-18):** Claude Opus 4.8 scores 77.7. The best open-weight models are close behind: GLM-5.2 (74.0), DeepSeek V4 Pro (73.9) and Kimi K2.6 (72.6).
- **AIME 2026:** open-weight models reach 93–99% (GLM-5.x, Kimi K2.x, Qwen3.5-35B-A3B on MathArena). MATH-500 is saturated.
- **Hallucination:** I found **no math-specific hallucination benchmark**. General ones (Vectara HHEM, nc-bench) measure summarization, not teaching.

**Takeaway:** grade 1–10 math is far below competition level, so solving the math is not the risk. The risks are:
- teaching quality: is the "why" really explained?
- quality in other languages (Arabic, Ukrainian and so on)
- invented facts or links

No leaderboard measures these, so we use:
- grounding in openly licensed source text
- SymPy checks of the math
- URLs from fixed templates only
- **our own rubric eval**, which decides the model

## 5. Enrichment sources

| Source | License / access | Use |
|---|---|---|
| OpenStax (Prealgebra 2e, Elementary/Intermediate Algebra 2e) | CC BY 4.0 | Ground prompts (copy text, with attribution) |
| Illustrative Mathematics K–12 (2019–21 edition) | CC BY 4.0 (the newer v.360 is CC BY-NC) | Ground prompts; its misconception notes feed "common mistakes" |
| Common Core State Standards | free with attribution | Grade 1–10 topic map |
| Wikipedia | CC BY-SA | Definitions and history only (share-alike) |
| Khan Academy | public API shut down in 2020; NC license, status disputed | Link only |
| Wolfram\|Alpha | free non-commercial dev tier; production is paid; the 2,000 calls/month figure is unverified | Link only (prefilled query) |
| SymPy | BSD | Math verification |
| GeoGebra | free for non-commercial use | Link to interactive models |
| NRICH, CK-12 | copyrighted / CC BY-NC | Link only |

## 6. Future scope (TODO)

- **The teacher's own language:** answer in the language of the question; include the language in the cache key; `dir=auto` for right-to-left scripts; country-specific notation (decimal comma, ÷ vs :, Eastern Arabic numerals); native-speaker review; translated UI. Token cost differs by script, see cost-model.md.
- **Sign-up and authentication:** needed for a cap that can't be bypassed, and for a teacher to find their own past sheets. Prefer Akelius's existing login (SSO) over our own accounts; keep only a pseudonymous ID.
- **More country standards:** one mapping file per country in `curriculum/standards/`.
- **Licensed content:** the `license` field already exists on every source; it would need an allow-list setting and an agreement with the rights holder.
- **Free-hand whiteboard:** Excalidraw (MIT) for sketching on the lesson page.
- **Semantic question matching:** multilingual embeddings, once our logs show which paraphrases the strict match misses.
- **Educator review workflow:** a page where reviewers approve sheets and promoted FAQs, which flips "not yet reviewed" to reviewed.
- **Production LLM backend:** the Anthropic API (Haiku 5.5) or a hosted open-weight model, chosen by the eval.

## 7. Discussion log (each user prompt, how it shaped the design, in order)

| # | User prompt (short) | What changed |
|---|---|---|
| 1 | Build a coach that helps teachers prepare; think hard about their problems; read the brief | Teacher problems (§2), a prep sheet instead of a chat (D1) |
| 2 | An LLM is needed because questions keep coming; is that too expensive for 50k teachers? Compare open-source models (llm-stats.com) | Cost research (§3), model quality research (§4), live LLM features (D2) |
| 3 | Cover math up to grade 10; Python; use the local Claude CLI for development | Grade 1–10 scope (D6), swappable LLM function (D5) |
| 4 | Use online resources (Wolfram, Khan Academy…); enrichment is key; write down the thinking | Enrichment licence table (§5), this file |
| 5 | Cap 50 queries per teacher per month, use caching, $2k budget, include accuracy in the cost | cost-model.md, D10–D13 |
| 6 | Plan against the 4 review criteria; keep a MEMORY.md step log (critical) | MEMORY.md plan and step log, CLAUDE.md |
| 7 | Countries have their own standards; native-language questions; open content only; check the plan against the brief | D14 (concept + country mapping), D16 (open only), plan v2 (timestamps, AI-use section, labels, input validation, smaller scope) |
| 8 | Question cache for similar or repeated questions, promoted into the static pages by demand | D18 |
| 9 | Native language → TODO; very strict matching; a teacher feedback box; sign-up/auth → TODO | D15, D18 (≥ 0.95), D19, §6 |
| 10 | "The core idea is to build a super trustworthy and reliable system" | The guiding principle at the top of this file; CLAUDE.md rule; corrected guessed timestamps to real clock times |
| 11 | The core job is lesson prep, so the static page must be very helpful; dislike of chatbots → AI in a side tab, the main tab shows only the notes | D21; exact math match in the question cache (D22) |
| 12 | Tools like Wolfram or open-source materials so teachers can draw and customise graphs embedded in the lesson page | D23 (JSXGraph templates) |
| 13 | Keep this document updated with my prompts | This table is updated after every prompt |

## 8. Open questions

- **For Akelius:** does Akelius count as commercial or non-commercial under CC BY-NC? This decides whether Khan Academy, CK-12 and IM v.360 content could be copied rather than only linked.
- **For Akelius:** which languages and countries come first? Do they need data to stay in a region, which would decide whether we self-host?
- **For us:** are the usage assumptions (40 calls per teacher per month) realistic? We need real usage data to check.
- **For us:** does the Haiku 5.5 vs open-weight eval hold up in non-English languages?

## Sources

- [BenchLM math leaderboard](https://benchlm.ai/md/math.md)
- [llm-stats](https://llm-stats.com)
- [MathArena AIME via Developers Digest](https://www.developersdigest.tech/benchmarks/aime)
- [Together pricing](https://www.aipricing.guru/together-pricing/)
- [DeepInfra: open-source LLM API providers](https://deepinfra.com/blog/best-open-source-llm-api-providers)
- [Khan Academy usage policy](https://support.khanacademy.org/hc/en-us/articles/202262954-Can-I-use-Khan-Academy-s-videos-name-materials-links-)
- [Khan Academy API decommissioning](https://support.khanacademy.org/hc/de/community/posts/360073275571/comments/38456925391373)
- [Illustrative Mathematics terms of use](https://www.illustrativemathematics.org/terms-of-use)
- [Wolfram|Alpha API](https://products5c.wolframalpha.com/api)
- Claude prices: Anthropic pricing table, as of 2026-11
