# Cost model

What the coach costs per teacher per month, how accuracy changes that number, and how we keep the total under budget.
Prices were checked on 2026-11-18. The open-source prices come from aggregator sites; check them on the providers' own pricing pages before relying on them.

## 1. Constraints (product decisions)

| Constraint | Value |
|---|---|
| Teachers | 50,000 |
| Live queries per teacher | hard cap of **50 per month** (explain-differently button presses and typed questions combined) |
| Monthly LLM budget | **$2,000**, enforced in code |
| Demo | runs on the local Claude Code CLI; nothing in the demo spends real money at this scale |

## 2. Assumptions (all of them, so anyone can challenge them)

| Input | Value | Why |
|---|---|---|
| Share of queries that are button presses | 40% | buttons are lower effort than typing |
| Answer-cache hit rate for buttons | 95% | the key (topic, section, variant) repeats across thousands of teachers |
| Answer-cache hit rate for typed questions | 15% | conservative: exact and near matches only. The question cache, and promoting popular questions into the sheets, should raise this; measure it before raising the number |
| → Overall answer-cache hit rate | **47%** | 0.4 × 0.95 + 0.6 × 0.15 |
| Input tokens per call | 1,200 system prompt + 1,500 sheet context + 100 question | the system prompt is identical on every call |
| Visible output tokens | 600 | capped by the prompt and by `max_tokens` |
| Reasoning tokens | Haiku 300 (effort low), gpt-oss 500, Sonnet/Opus 800, DeepSeek 1,000 | reasoning models produce extra hidden output |
| Tokenizer factor | Claude 5.x = 1.3×, open models = 1.0× | the newer Claude tokenizers count the same text as about 30% more tokens |
| Prompt cache | Claude reads the system prompt from cache at about 0.1× the input price; open hosts are assumed to have no caching | conservative for open hosts |
| Error rate per model (grade 1–10 answers) | Haiku 5%, Sonnet 2%, Opus 1.5%, DeepSeek V3.2 4%, gpt-oss-120b 8% | **these are priors, not measurements** (see §6) |
| Automatic checker catch rate | 60% | SymPy catches arithmetic and algebra errors; it can't catch teaching errors |
| Errors still left after escalation to Sonnet | 2% of the escalated answers | |
| Usage, worst case | all 50k teachers use all 50 queries: 2.5M queries | |
| Usage, realistic | 50% active × 15 queries: 375k queries | to be replaced with real usage data |

## 3. Method

```
cost per call  = (system tokens × prompt-cache price + other input tokens × input price
                 + (visible + reasoning) output tokens × output price) × tokenizer factor
paid calls     = queries × (1 − answer-cache hit rate)
cost per query = cost per call + error rate × catch rate × Sonnet escalation cost
residual error = error rate × (1 − catch rate) + escalated share × 2%
monthly cost   = paid calls × cost per query
```

Cached answers are served without any model call. We assume they were checked when they were first created.

## 4. Results

### Worst case: 2.5M queries, of which 1.33M reach a model

| Model | $ per call | Assumed error | Wrong answers reaching teachers | $ per month | $ per teacher | Fits $2k? |
|---|---|---|---|---|---|---|
| Claude Haiku 5.5 | 0.00081 | 5% | 2.1% | 1,966 | 0.039 | yes, barely |
| DeepSeek V3.2 (hosted) | 0.00084 | 4% | 1.6% | 1,829 | 0.037 | yes |
| gpt-oss-120b (DeepInfra) | 0.00029 | 8% | 3.3% | 1,817 | 0.036 | yes |
| gpt-oss-120b (Together) | 0.00108 | 8% | 3.3% | 2,863 | 0.057 | no |
| Claude Sonnet 5.5 | 0.0225 | 2% | 0.8% | 29,834 | 0.60 | no |
| Claude Opus 5.5 | 0.045 | 1.5% | 0.6% | 59,667 | 1.19 | no |

### Realistic case: 375k queries, of which about 199k reach a model

| Model | $ per month | $ per teacher |
|---|---|---|
| Claude Haiku 5.5 | ~295 | 0.006 |
| DeepSeek V3.2 / gpt-oss-120b (DeepInfra) | ~275 | 0.006 |
| Claude Sonnet 5.5 | ~4,475 | 0.09 |

### Prep sheet generation (separate from live queries)

At about $0.12 per sheet with Sonnet 5.5 (6k tokens in, 4k visible and 4k reasoning tokens out):
- the full library of 2,000 sheets (about 400 topics × 5 languages) costs about **$120 once** with the Batch API (50% off);
- about 300 new typed topics a month cost about **$36 a month**.

## 5. Conclusions

1. **Only small models fit the budget on the live path.** In the worst case, Sonnet and Opus cost 15–30× the budget. We use them only for one-time sheet generation and for re-answering flagged errors.
2. **A cheap model with a high error rate isn't really cheap.** gpt-oss on DeepInfra costs 3× less per call than Haiku, but about $1,400 of its $1,817 is Sonnet re-answering flagged errors. It ends up costing about the same and lets more wrong answers through.
3. **Haiku's worst case ($1,966) is too close to $2k**, so the budget is enforced in code. A spend ledger records the tokens × price of every call. When the ledger reaches the monthly budget, live calls stop. The coach then serves prep sheets and cached answers, and new typed questions wait until next month. It degrades gently and never overspends.
4. **The realistic case uses about 15% of the budget.** The spare budget can go to a stronger model for the "why it works" sections only, if the eval shows a gain.
5. **How to lower costs further, in order of effect:** a higher answer-cache hit rate (point near-duplicate questions to existing sheet sections); lower reasoning effort; capping output; the Batch API for sheets; and a cheaper host once the eval shows quality holds.

## 6. What's weakest, and how we fix it

- **Error rates are priors.** Anthropic hasn't published math benchmark scores for Haiku 5.5. For the open-source models we only have relative signals: on BenchLM's competition math scores, DeepSeek V3.2 (thinking) averages 86 and gpt-oss-120b averages 50, and on the Artificial Analysis index they score 32 and 24. **Fix:** our eval set (about 15 teacher questions across grades 1–10) measures the real error rate per model, and we rerun this model with those numbers.
- **First measurements (prototype, 2026-11-18):** a live Haiku answer cost $0.00085 (the model predicted $0.00081). All 27 sheets together cost $1.12, about $0.04 each (the model assumed $0.12). On the 10-question eval, Haiku made 0 math errors. That isn't enough to lower the 5% prior: with 0/10, the true rate could still be as high as about 26% at 95% confidence. We need 100+ cases before the priors change.
- **Non-English questions cost more.** Scripts like Arabic and Ukrainian (Cyrillic) usually need more tokens for the same text (about 1.5–2× is a rough figure we haven't verified), and caching splits by language. If half the traffic were non-English at 1.75× tokens, the worst case for Haiku would rise to about $2.7k a month, which is over budget. The budget limit in code then stops live calls earlier. **Fix:** measure tokens per language with `count_tokens` before launching in a country.
- **Cache hit rates, catch rate, reasoning tokens and usage** are also assumptions. **Fix:** log anonymous counts (hits, misses, tokens) and recompute monthly.

## Appendix: the script

Run it with `python3`. Change the inputs at the top to test other assumptions.

```python
BUDGET, TEACHERS, CAP = 2000, 50_000, 50
SCEN = {"worst (all at cap)": TEACHERS*CAP, "realistic (50% active x 15)": int(TEACHERS*0.5*15)}
BUTTON_SHARE, BUTTON_HIT, ASK_HIT = 0.4, 0.95, 0.15
HIT = BUTTON_SHARE*BUTTON_HIT + (1-BUTTON_SHARE)*ASK_HIT
SYS, CTX, Q, VISIBLE = 1200, 1500, 100, 600
# name: $in/M, $out/M, $cache_read/M, reasoning tokens, tokenizer factor, prompt-cached system?
M = {
 "Claude Haiku 5.5":         (0.10, 0.50, 0.01, 300, 1.3, True),
 "Claude Sonnet 5.5":        (2.00,10.00, 0.10, 800, 1.3, True),
 "Claude Opus 5.5":          (4.00,20.00, 0.20, 800, 1.3, True),
 "DeepSeek V3.2 (hosted)":   (0.14, 0.28, None,1000, 1.0, False),
 "gpt-oss-120b (DeepInfra)": (0.037,0.17, None, 500, 1.0, False),
 "gpt-oss-120b (Together)":  (0.15, 0.60, None, 500, 1.0, False),
}
ERR = {"Claude Haiku 5.5":0.05,"Claude Sonnet 5.5":0.02,"Claude Opus 5.5":0.015,
       "DeepSeek V3.2 (hosted)":0.04,"gpt-oss-120b (DeepInfra)":0.08,"gpt-oss-120b (Together)":0.08}
CATCH, ESC_ERR = 0.6, 0.02

def call(name):
    i, o, cr, r, tf, pc = M[name]
    inp = SYS*tf*(cr if pc else i) + (CTX+Q)*tf*i
    return (inp + (VISIBLE+r)*tf*o) / 1e6

ESC = call("Claude Sonnet 5.5")
for s, q in SCEN.items():
    paid = q*(1-HIT)
    print(f"== {s}: {q:,} queries, {paid:,.0f} reach a model")
    for n in M:
        c, e = call(n), ERR[n]
        escalates = n not in ("Claude Sonnet 5.5", "Claude Opus 5.5")
        per = c + (e*CATCH*ESC if escalates else 0)
        resid = e*(1-CATCH) + (e*CATCH*ESC_ERR if escalates else 0)
        month = paid*per
        print(f"{n:26} ${c:.5f}/call  resid {resid:.1%}  ${month:,.0f}/month  "
              f"${month/TEACHERS:.4f}/teacher  {'fits' if month <= BUDGET else 'OVER'}")
sheet = (6000*1.3*2.0 + 8000*1.3*10.0) / 1e6
print(f"sheet ${sheet:.3f}; library 2,000 batch ${2000*sheet*0.5:,.0f}; 300 new/month ${300*sheet:,.0f}")
```

Sources: [Anthropic pricing (via the claude-api reference, 2026-11)](https://platform.claude.com/docs/en/about-claude/pricing) · [Together pricing](https://www.aipricing.guru/together-pricing/) · [DeepInfra](https://deepinfra.com/blog/best-open-source-llm-api-providers) · [BenchLM DeepSeek V3.2 vs gpt-oss-120b](https://benchlm.ai/compare/deepseek-v3-2-thinking-vs-gpt-oss-120b) · [Artificial Analysis](https://artificialanalysis.ai/models/comparisons/deepseek-v3-2-reasoning-vs-gpt-oss-120b) · [Haiku 5.5 benchmarks (no math published)](https://aiidelist.com/blog/claude-haiku-5-5-benchmarks.md)
