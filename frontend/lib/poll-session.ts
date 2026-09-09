import { request } from "@/lib/api";
import type { CheckSession } from "@/types/check";

export async function pollSession(
  id: string,
  update: (session: CheckSession) => void,
  intervalMs = 1000,
): Promise<CheckSession> {
  for (;;) {
    const session = await request<CheckSession>(`/sessions/${id}`);
    update(session);
    if (session.run_state !== "RUNNING") return session;
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }
}
