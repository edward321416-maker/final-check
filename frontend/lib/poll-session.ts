import { request } from "@/lib/api";
import type { CheckSession } from "@/types/check";

const MAX_TRANSIENT_POLL_RETRIES = 3;

export async function pollSession(
  id: string,
  update: (session: CheckSession) => void,
  intervalMs = 1000,
  signal?: AbortSignal,
): Promise<CheckSession> {
  let transientFailures = 0;
  for (;;) {
    try {
      if (signal?.aborted) throw new DOMException("The operation was aborted.", "AbortError");
      const session = await request<CheckSession>(`/sessions/${id}`, undefined, signal);
      if (signal?.aborted) throw new DOMException("The operation was aborted.", "AbortError");
      transientFailures = 0;
      update(session);
      if (session.run_state !== "RUNNING") return session;
      await abortableDelay(intervalMs, signal);
    } catch (error) {
      if (signal?.aborted) throw error;
      if (transientFailures >= MAX_TRANSIENT_POLL_RETRIES) throw error;
      await abortableDelay(Math.min(intervalMs * 2 ** transientFailures, 5_000), signal);
      transientFailures += 1;
    }
  }
}

function abortableDelay(delayMs: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("The operation was aborted.", "AbortError"));
      return;
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", abort);
      resolve();
    }, delayMs);
    const abort = () => {
      clearTimeout(timer);
      reject(new DOMException("The operation was aborted.", "AbortError"));
    };
    signal?.addEventListener("abort", abort, { once: true });
  });
}
