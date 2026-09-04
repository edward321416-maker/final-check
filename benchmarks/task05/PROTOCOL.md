# TASK 05: one blind AI-first direction probe

Scope: eight unchanged TASK04 public announcement text snapshots, 173 frozen Gold
requirements. TASK04 PR #3 merge baseline is
`0125f05e8b7d68362dcf9e781f0a627e097eaddd`.

The prompt, canonical schema, candidate `gpt-5.6-sol`, high reasoning setting and
runner were frozen before the first candidate output. `freeze.json` records byte
hashes and timing. Each case receives the identical prompt and schema plus only
its own source. No case retry, prompt revision, local extractor tuning or provider
bakeoff is permitted. Earlier prerequisite BLOCKED attempts and the synthetic
authentication/isolation probe are excluded from all benchmark metrics.

The subprocess uses a new temporary cwd, CODEX_HOME and thread for each case,
existing local authentication, no user config, no memory, no skills instructions,
no MCP/apps/plugins, no browsing and a disabled code-mode execution host. A
pre-invocation `debug prompt-input` export preserves model-visible messages and
checks for inherited project context. Built-in model instructions, CLI environment
metadata and unavailable tool stubs remain. This is context and execution-path
isolation, not an OS container. Any actual tool-call event invalidates the run.
Temporary auth copies are removed in a finally block and never copied into Git.

RAW preserves the model's returned JSON text. GATED calls the unchanged TASK03
`anchor` validation, schema, exact substring, forbidden BLOCKER modality,
duplicate-ID, offsets and atomicity flag logic. The existing 100-candidate cap is
retained. No spelling repair, evidence repair, semantic rewrite or automatic
approval occurs. Atomicity flags remain review flags; they do not certify truth.

Manual scoring follows `benchmarks/task04/PROTOCOL.md` and its frozen formulae:
one-to-one complete atomic MATCH; PARTIAL scores zero; no duplicate Gold credit;
modality accuracy uses MATCH pairs; quote support assesses rule, condition and
modality. Every candidate and Gold receives a row. GATED is the primary product
denominator; RAW is diagnostic. The local comparison copies the frozen TASK04 raw
baseline metrics without executing its extractor again for benchmark scores.

Gold was authored and scored within the same engineering workflow, without
independent human adjudication. The accurate label is PRE-OUTPUT FROZEN REAL
BENCHMARK, not an independently human-annotated benchmark. The isolated extractor
does not receive Gold or scoring. This limited eight-case probe selects a product
direction, not a production provider or a population accuracy estimate.

No production integration, default-provider changes, UI claims, Vision/OCR,
generic submission verifier, deployment, R19 changes or next-task implementation.
The TASK05 PR must remain OPEN / NOT MERGED.

Product direction thresholds are inherited from the handoff, separate from
measurement completion. Strong GO requires recall at least 70%, precision 65%,
modality 70%, semantic support 85%, zero unsupported blockers, at most one
hallucination and clear improvement over local rules. MODIFY may be considered
around recall 55-70% and precision 50-65% with bounded, safe failures. Recall below
55%, precision below 50%, unsupported blockers or structural extraction failures
support STOP for this primary candidate. An unfavorable model score does not
convert an honestly completed measurement into a failed experiment.
