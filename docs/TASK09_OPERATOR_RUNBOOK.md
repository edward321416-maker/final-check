# TASK09 zero-cost operator runbook

## Start

1. Keep the judging PC awake, connected to the internet, and signed into the existing Codex CLI and ngrok accounts.
2. From the repository root, run `powershell -File scripts/start-public-judge.ps1`.
3. Wait for the script to print `FINAL CHECK public judge runtime is ready`.
4. Open `https://uncoy-joelle-macrodont.ngrok-free.dev`. On the first visit, ngrok Free may show a browser warning; continue only to the documented FINAL CHECK domain.
5. Confirm `https://uncoy-joelle-macrodont.ngrok-free.dev/api/health` reports `status=ok`, `provider=Codex CLI`, model `gpt-5.6-sol`, reasoning `high`, writable storage, available ffprobe, and an enabled public guard.

The launcher writes only process IDs, health, and service logs under ignored `artifacts/runtime/`. It never writes Codex or ngrok credentials.

## Stop and recover

- Stop only the recorded processes with `powershell -File scripts/stop-public-judge.ps1`.
- Start again with the normal start command. SQLite and session artifacts remain under ignored `.final-check/runtime/`.
- If the PC, network, Codex login, or ngrok agent is unavailable, the judge URL is unavailable. Restore the dependency and restart; there is no failover host.
- If a stale manifest remains after an abnormal exit, inspect the recorded processes before removing it. The stop script refuses to terminate a reused PID whose name or start time differs.

## During judging

- Disable sleep and automatic reboot for the judging window.
- Check the public health endpoint and ngrok usage daily.
- Keep changes frozen after Product Lead approval. If a restart or code change is required, record the time, reason, commit, and fresh health/E2E result.
- Stop the tunnel after judging ends.

## Limits

Judge availability depends on the host PC/network, there is no cloud failover, ngrok Free outbound transfer is limited to 1 GB/month, and no production SLA is claimed. Keep test uploads small and free of personal or confidential information.
