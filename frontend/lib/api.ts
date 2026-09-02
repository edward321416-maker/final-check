import type { CheckSession } from "@/types/check";

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
export async function request<T>(path: string, body?: object | FormData): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 200_000);
  try {
    const response = await fetch(`/api${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: body instanceof FormData ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body),
      signal: controller.signal, cache: "no-store",
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      const detail = typeof payload?.detail === "string" ? payload.detail : "요청을 완료하지 못했습니다.";
      const message = response.status === 503 ? "이 공고의 분석 프로필 또는 검증 엔진을 사용할 수 없습니다. 제공된 동결 공고 demo로 확인해 주세요."
        : response.status === 404 ? "검사 세션이 만료되었습니다. 홈에서 새 검사를 시작해 주세요."
        : detail;
      throw new ApiError(response.status, message);
    }
    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new Error("검사 서버에 연결할 수 없습니다. 서버 실행 상태를 확인하고 다시 시도해 주세요.");
  } finally { clearTimeout(timer); }
}
export const sessionRequest = (id: string, action: string, body: object | FormData) =>
  request<CheckSession>(`/sessions/${id}/${action}`, body);
