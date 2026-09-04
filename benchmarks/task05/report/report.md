# TASK 05 — completed blind AI-first comparison

Measurement: **PASS**. Product direction: **AI-FIRST — STOP** for this locked
primary candidate. FINAL CHECK remains **GO**; LocalRuleExtractor remains **STOP
AS PRIMARY**, retained as the frozen comparison baseline.

Eight public announcements, 173 unchanged pre-output frozen requirements, one
`gpt-5.6-sol` candidate, one locked prompt, eight fresh invocations, zero model
tool-call events and no output retries. Actual execution ran from
2026-09-04 09:48:00 to 10:08:35 UTC using Codex CLI 0.147.0 and existing ChatGPT
authentication. Requested model alias is known; underlying dated snapshot is
UNKNOWN. Reasoning effort was high; temperature and seed were provider defaults
and not exposed.

## Results

| Metric | Frozen local-rules-v1 | AI RAW | AI GATED (primary) |
|---|---:|---:|---:|
| Gold | 173 | 173 | 173 |
| Candidates | 211 | 354 | 237 |
| Complete one-to-one MATCH | 32 | 119 | 83 |
| Recall | 18.50% | 68.79% | 47.98% |
| Precision | 15.17% | 33.62% | 35.02% |
| Modality accuracy on MATCH | 25.00% | 96.64% | 97.59% |
| Exact quote | 100.00% | 100.00% | 100.00% |
| Semantic evidence support | 24.17% | 71.75% | 78.48% |
| Manual atomicity violations | 18 (8.53%) | 7 (1.98%) | 3 (1.27%) |
| Hallucinated constraints | 0 | 0 | 0 |
| Unsupported BLOCKER candidates | 0 | 5 | 3 |
| All BLOCKER candidates | 0 | 156 | 115 |

GATED improves recall by **29.48 percentage points** and precision by **19.86
percentage points** over the fixed local baseline. It still misses the handoff's
minimum direction thresholds (recall 55%, precision 50%) and retains three
unsupported BLOCKER candidates. RAW's higher recall does not override the primary
GATED decision. These are candidate severity labels, not submission findings.

| Case | Gold | RAW | GATED | GATED MATCH |
|---|---:|---:|---:|---:|
| C01 | 49 | 117 | 0 | 0 |
| C02 | 14 | 27 | 27 | 9 |
| C03 | 6 | 10 | 10 | 2 |
| C04 | 44 | 77 | 77 | 27 |
| C05 | 2 | 4 | 4 | 2 |
| C06 | 7 | 6 | 6 | 5 |
| C07 | 19 | 44 | 44 | 17 |
| C08 | 32 | 69 | 69 | 21 |

## Gate and safety

C01 generated 117 candidates, exceeding TASK03's existing 100-candidate cap. The
product extraction operation would fail at that cap. The benchmark records the
equivalent empty retained set and 117 cap rejections; it does not truncate to the
first 100 or change the product limit. This removes 36 otherwise fully matched
RAW candidates. All other cases pass schema/exact-quote/ID checks unchanged.

Gate rejection total: 117 cap rejections; zero schema, duplicate-ID or exact-quote
rejections among the remaining 237 candidates. The unchanged syntactic atomicity
gate flags 29 retained items for review. That flag count differs from the three
manual semantic atomicity violations and must not be reported as the same metric.
All saved GATED profiles remain REVIEW_REQUIRED, never automatically confirmed.

Three unsupported BLOCKER candidates survive the mechanical gate:

- C02 R14: correct SNS-upload content, but the selected quote only lists eligible
  platforms and does not establish the asserted upload duty.
- C04 R58: report submission content matches Gold, but a bare report heading and
  generic file-list section fail to establish finalist applicability.
- C08 R24: conflates the file demonstrating a completed product with additional
  product submission and loses the later presentation-stage condition.

The exact quote gate is an anchoring check, not semantic validation. No generic
submission verifier or semantic safety gate was implemented to hide these results.

## Frozen scoring and limitations

The unchanged TASK04 policy defines complete atomic semantic MATCH with its full
condition, zero credit for PARTIAL, and no duplicate Gold credit. Modality is
scored separately on MATCH. Every RAW candidate has one manual judgement, and
every Gold appears in each comparison pair file. The GATED view filters those
same judgements; no semantic rewrite or favorable rematching is applied.

The original frozen Gold units sometimes group several details. Splitting a fixed
set, full eligibility definition, submission bundle or execution configuration
across several AI candidates therefore yields PARTIAL rather than several full
credits. This is a limitation of comparison against these frozen units, not a
new scoring rule. Gold was not split or repaired after seeing AI output.

Some well-supported additional source statements have no frozen Gold unit. These
are marked OUTSIDE_GOLD, receive no precision credit, and are not automatically
called hallucinations. Empty form labels and organizer/prize operations retain
the frozen scope exclusions. C02's two conflicting deadline times remain
unresolved; the AI's separate statements do not constitute a complete conflict
requirement. No new constraint was confidently judged invented under the frozen
hallucination definition; this does not mean all conditions or evidence are sound.

This is a **PRE-OUTPUT FROZEN REAL BENCHMARK**, not independent human annotation.
Gold creation and manual scoring belong to the same engineering workflow; no
independent human adjudicator reviewed these judgements. Eight selected cases,
unequal document lengths, imperfect Gold coverage and subjective equivalence
judgements limit generalization. No confidence interval or population accuracy is
claimed. The extraction subprocesses did not receive Gold or scoring.

## Isolation and provenance

`freeze.json` records the prompt, schema, runner, source hashes, settings and
timestamp. Prompt freeze was committed as `e2b144f`; `fe6ecdd` preserved artifact
bytes across Git line-ending handling without changing the prompt or runner.
Each case has a fresh cwd, CODEX_HOME and thread, staging only prompt/schema/source.
Parent environment variables were allowlisted; inherited config, skill
instructions, memory, MCP/apps/plugins and execution tools were disabled. Existing
auth was copied only for local transport and each temporary copy was removed.

`execution/*-prompt-input.json` captures each model-visible input list. Mandatory
CLI environment and built-in developer/model instructions remain. The synthetic
probe showed tool names still advertised; code mode failed closed with its host
disabled. This is not an OS container or a claim that no tool schema exists.
Actual event logs show zero tool calls, eight different thread IDs and no resumed
conversation, inherited benchmark material, Gold, scoring or previous case output.
No new login, account, OAuth, paid plan or API key was acquired. Public source was
the only task data transmitted. The synthetic probe is excluded from scores.

Actual per-case CLI telemetry totals: input 79,147 tokens; output 65,627 tokens,
including 27,013 reasoning tokens reported as a separate subset. This excludes
orchestrator work, regression and the synthetic probe; no token savings claimed.

## Regression and source integrity

- Backend: 47 passed (one existing Starlette/httpx deprecation warning).
- Browser: 14 passed, desktop/mobile Chromium, including actual upload/profile
  paths. These existing synthetic regression cases are SELF, not benchmark data.
- TypeScript: PASS. Production build: PASS. `git diff --check`: PASS.
- Product source, tests, fixtures, local extractor, TASK04 and frozen validator:
  unchanged. Gold manifest and all 27 listed frozen files verified before/after.
- Existing mock/fault-injection paths remain SIMULATED. Other providers, Vision,
  OCR, production integration, automatic generic verification, deployment and
  independent human adjudication remain NOT TESTED.

Frozen SHA-256 values:

```text
Gold manifest 035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89
Validator     4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11
Prompt        9edc46cbdcb37a619bb5c02d5e1b8f443fbf56c7dcda0f714b4b9103c1e85155
Schema        f9a4ff385b7ad8f15b59880cb15ddaf67b0cca159539cca9866a89b5a02cdbc8
Runner        c7d6c3910509515009f21bb21e26c55cf53f8cfe12e6787e5e948c919d089644
```

## Delivery and next recommendation

This locked primary candidate is STOP. FINAL CHECK remains GO and local rules
remain STOP AS PRIMARY. Product/Business Lead should review these failure types
and the frozen Gold granularity before authorizing any new, separately frozen
experiment or assisted workflow. No later task, tuning or integration was started.
Delivery [PR #4](https://github.com/edward321416-maker/final-check/pull/4) is verified
OPEN / NOT MERGED. Benchmark commit is
`a48bfbff28cacf053eab848710c05632eaeb6fbc`; later delivery-document changes contain
no candidate, Gold, prompt, gate or scoring changes.

Artifacts: `../raw/`, `../gated/`, `../execution.json`, `../scoring/candidates.tsv`,
both pair CSVs, `comparison.json`, `failure-taxonomy.md`, and
`../../../artifacts/task05/` regression/provenance evidence.
