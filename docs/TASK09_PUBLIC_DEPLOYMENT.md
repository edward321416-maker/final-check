# TASK09 zero-cost public deployment

Status: **ngrok Free public runtime candidate using the existing local production build and Codex CLI.**

Public URL: `https://uncoy-joelle-macrodont.ngrok-free.dev`

## Architecture

```text
Judge browser
  -> ngrok Free HTTPS development domain
  -> local Next.js production server on 127.0.0.1:3100
  -> server-side /api rewrite
  -> local FastAPI on 127.0.0.1:8100 (one worker)
  -> local .final-check/runtime SQLite and session files
  -> existing ChatGPT-authenticated Codex CLI
     -> Stage1 -> Stage2 -> human confirmation -> Planner
  -> local deterministic verifier and ffprobe
```

Railway Hobby and OpenAI API billing were canceled by the Product Lead. The OpenAI Responses production provider is deferred and is not present in this delivery. No OpenAI API key is required. Codex authentication stays in the user's existing local Codex home and is copied only into each isolated, temporary provider invocation as established in TASK06/TASK08. It is never placed in the repository, frontend, ngrok configuration, or runtime evidence.

## Public runtime configuration

`scripts/start-public-judge.ps1` builds the frontend and starts three hidden local processes: one Uvicorn backend worker, one Next.js production server, and one ngrok agent bound to the account's assigned development domain. It applies:

```text
FINAL_CHECK_ENV=production
FINAL_CHECK_AI_PROVIDER=codex
FINAL_CHECK_AI_MODEL=gpt-5.6-sol
FINAL_CHECK_AI_REASONING=high
FINAL_CHECK_DATA_DIR=<repository>/.final-check/runtime
FINAL_CHECK_PUBLIC_GUARD=1
FINAL_CHECK_AI_MAX_CONCURRENT_WORKFLOWS=2
FINAL_CHECK_AI_MAX_OPERATIONS_PER_HOUR=40
FINAL_CHECK_AI_MAX_OPERATIONS_PER_SESSION_HOUR=6
FINAL_CHECK_MAX_FILE_BYTES=16777216
FINAL_CHECK_MAX_PACKAGE_BYTES=25165824
FINAL_CHECK_MAX_FILES=8
API_ORIGIN=http://127.0.0.1:8100
```

The public upload limit is 16 MiB per file and 24 MiB per package with at most eight files. The application rejects production health when Codex authentication, the exact model/reasoning setting, local storage, the frozen Validator, ffprobe, or the public guard is unavailable.

## Data and authority boundary

Stage1 and Stage2 receive the announcement source. Planner receives only the human-confirmed source/profile. Submission names, bytes, metadata, ffprobe output, and verifier results stay in the local deterministic path. AI output cannot issue PASS, BLOCKER, READY, or BLOCKED. Human confirmation and the deterministic Plan Gate remain required.

API responses use `Cache-Control: no-store`; public responses add `nosniff`, `no-referrer`, and `noindex, nofollow`. Crawlers are disallowed. Durable global/per-session hourly counters and a two-workflow lease cap remain active. `PER_IP_LIMIT = NOT_IMPLEMENTED` because forwarded client identity is not trusted.

## Explicit limitations

- Judge availability depends on the host PC and network remaining continuously online.
- There is no cloud failover.
- ngrok Free allows 1 GB/month outbound data transfer and other free-plan request limits.
- There is no production SLA.
- Free endpoints can show an ngrok browser warning on a visitor's first visit.
- The runtime is a public, unauthenticated competition MVP on one local process; it is not a distributed or high-traffic deployment.
- Vision/OCR, semantic submission verification, new formats, product login, payments, analytics, and backups remain deferred.

The ngrok Free plan supplies one account-assigned stable development domain. The domain does not time out while its agent remains connected, but the local process and host must stay running. See the official [Free Plan Limits](https://ngrok.com/docs/pricing-limits/free-plan-limits) and [Agent CLI](https://ngrok.com/docs/agent/cli) documentation.
