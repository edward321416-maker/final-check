import { request } from "@/lib/api";
import type { CheckSession } from "@/types/check";

const MAX_TRANSIENT_POLL_RETRIES = 3;

export async function pollSession(
  id: string,
  update: (session: CheckSession) => void,
  intervalMs = 1000,
): Promise<CheckSession> {
  let transientFailures = 0;
  for (;;) {
    try {
      const session = await request<CheckSession>(`/sessions/${id}`);
      transientFailures = 0;
      update(session);
      if (session.run_state !== "RUNNING") return session;
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    } catch (error) {
      if (transientFailures >= MAX_TRANSIENT_POLL_RETRIES) throw error;
      await new Promise(resolve => setTimeout(resolve, Math.min(intervalMs * 2 ** transientFailures, 5_000)));
      transientFailures += 1;
    }
  }
}
