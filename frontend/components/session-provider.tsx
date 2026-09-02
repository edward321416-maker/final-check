"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { ApiError, request } from "@/lib/api";
import type { CheckSession } from "@/types/check";

const KEY = "final-check-session-id-v1";
type State = { session: CheckSession | null; loading: boolean; recoveryError: string;
  update: (session: CheckSession) => void };
const Context = createContext<State | null>(null);
export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<CheckSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [recoveryError, setRecoveryError] = useState("");
  useEffect(() => {
    let active = true;
    let id: string | null = null;
    try { id = sessionStorage.getItem(KEY); } catch { /* Storage is optional. */ }
    if (!id) { setLoading(false); return; }
    request<CheckSession>(`/sessions/${id}`).then((value) => {
      if (active) setSession(value);
    }).catch((error: unknown) => {
      if (active) setRecoveryError(error instanceof Error ? error.message : "세션 복구 실패");
      if (error instanceof ApiError && error.status === 404) {
        try { sessionStorage.removeItem(KEY); } catch { /* Optional storage. */ }
      }
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  function update(value: CheckSession) {
    setSession(value); setRecoveryError("");
    try { sessionStorage.setItem(KEY, value.id); } catch { /* Keep working in memory. */ }
  }
  return <Context.Provider value={{ session, loading, recoveryError, update }}>{children}</Context.Provider>;
}
export function useSession() {
  const context = useContext(Context);
  if (!context) throw new Error("SessionProvider is required");
  return context;
}
