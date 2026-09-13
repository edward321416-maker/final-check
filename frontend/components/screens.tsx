"use client";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { request, sessionRequest } from "@/lib/api";
import { pollSession } from "@/lib/poll-session";
import type { CheckSession, SemanticReadiness, SubmissionFile } from "@/types/check";
import { useSession } from "./session-provider";
import { ModeNote, PageTitle, useAction, WorkflowGuard } from "./ui";
import { AnnouncementWorkspace } from "./announcement-workspace";
import { RequirementsWorkspace } from "./requirements-workspace";
import { LandingScreen } from "./landing";
import { PreflightPackageWorkspace } from "./preflight-package";
import { ResultsWorkspace } from "./results-workspace";

export function HomeScreen() {
  return <LandingScreen />;
}

export function AnnouncementScreen() {
  return <WorkflowGuard step="announcement"><ModeNote /><PageTitle step="01 / ANNOUNCEMENT ANALYSIS" title="공고의 조건부터 확인하세요" description="제출 전에 지켜야 할 조건과 공고문에 적힌 근거를 살펴봅니다." />
    <AnnouncementWorkspace />
  </WorkflowGuard>;
}

export function RequirementsScreen() {
  return <WorkflowGuard step="requirements"><ModeNote /><PageTitle step="02 / REQUIREMENTS REVIEW" title="확정 전 요구사항을 확인하세요" description="공고에서 확인된 요구사항과 원문 근거를 읽고 다음 검사 범위를 확인합니다." />
    <RequirementsWorkspace />
  </WorkflowGuard>;
}

export function UploadScreen({ recheck = false }: { recheck?: boolean }) {
  const { session, update } = useSession();
  const router = useRouter();
  const { busy, error, run } = useAction();
  const [selected, setSelected] = useState<File[]>([]);
  const [readiness, setReadiness] = useState<SemanticReadiness | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [pollError, setPollError] = useState("");
  const activeSessionId = useRef(session?.id);
  activeSessionId.current = session?.id;
  const pollingGeneration = useRef(0);
  const pollingSession = useRef<{ id: string; generation: number; controller: AbortController } | null>(null);
  async function loadReadiness(current: CheckSession) {
    setAcknowledged(false);
    setReadiness(null);
    setReadiness(await request<SemanticReadiness>(`/sessions/${current.id}/semantic-readiness`));
  }
  async function resumePolling(current: CheckSession) {
    if (pollingSession.current?.id === current.id) return;
    pollingSession.current?.controller.abort();
    const generation = pollingGeneration.current + 1;
    pollingGeneration.current = generation;
    const controller = new AbortController();
    pollingSession.current = { id: current.id, generation, controller };
    const isCurrent = () => !controller.signal.aborted
      && pollingGeneration.current === generation
      && pollingSession.current?.generation === generation
      && activeSessionId.current === current.id;
    setPollError("");
    try {
      const completed = await pollSession(current.id, value => { if (isCurrent()) update(value); }, 1000, controller.signal);
      if (!isCurrent()) return;
      if (completed.run_state === "COMPLETE") router.push("/results");
      if (completed.run_state === "FAILED") setPollError(completed.run_error ?? "검사를 완료하지 못했습니다. 다시 시도해 주세요.");
    } catch (pollingError) {
      if (!isCurrent()) return;
      setPollError(pollingError instanceof Error ? pollingError.message : "검사 진행 상태를 불러오지 못했습니다.");
    } finally {
      if (pollingSession.current?.generation === generation) pollingSession.current = null;
    }
  }
  useEffect(() => () => {
    pollingGeneration.current += 1;
    pollingSession.current?.controller.abort();
    pollingSession.current = null;
  }, [session?.id]);
  useEffect(() => {
    let active = true;
    if (!session?.files.length) {
      setReadiness(null);
      setAcknowledged(false);
      return;
    }
    request<SemanticReadiness>(`/sessions/${session.id}/semantic-readiness`)
      .then(value => { if (active) setReadiness(value); })
      .catch(value => { if (active) setPollError(value instanceof Error ? value.message : "내용 검토 준비 상태를 불러오지 못했습니다."); });
    return () => { active = false; };
  }, [session?.id, session?.files.length]);
  useEffect(() => {
    if (session?.run_state === "RUNNING") void resumePolling(session);
  }, [session?.id, session?.run_state]);
  async function choose(fixture: "demo-broken" | "demo-fixed") {
    if (!session) return;
    const manifest = await request<SubmissionFile[]>(`/demo-files/${fixture}`);
    const form = new FormData();
    for (const file of manifest) {
      const response = await fetch(`/api/demo-files/${fixture}/${encodeURIComponent(file.name)}`, { cache: "no-store" });
      if (!response.ok) throw new Error("demo 파일을 불러오지 못했습니다.");
      form.append("files", await response.blob(), file.name);
    }
    const next = await sessionRequest(session.id, "files", form);
    update(next);
    await loadReadiness(next);
    setSelected([]);
  }
  async function upload() {
    if (!session || !selected.length) return;
    const form = new FormData();
    selected.forEach(file => form.append("files", file));
    const next = await sessionRequest(session.id, "files", form);
    update(next);
    await loadReadiness(next);
    setSelected([]);
  }
  async function validate() {
    if (!session) return;
    try {
      const next = await sessionRequest(session.id, "validate", {
        semantic_text_ai_acknowledged: readiness?.ack_required ? acknowledged : false,
      });
      update(next);
      if (next.run_state === "RUNNING") {
        void resumePolling(next);
        return;
      }
      if (next.run_state === "COMPLETE") router.push("/results");
    } catch (error) {
      update(await request<CheckSession>(`/sessions/${session.id}`));
      throw error;
    }
  }
  function selectFiles(event: ChangeEvent<HTMLInputElement>) { setSelected(Array.from(event.target.files ?? [])); }
  return <WorkflowGuard step={recheck ? "recheck" : "upload"}><ModeNote /><PageTitle step={recheck ? "05 / RECHECK" : "03 / SUBMISSION UPLOAD"} title={recheck ? "수정한 파일로 다시 확인하세요" : "제출할 파일을 모아주세요"} description={recheck ? "수정 패키지를 선택하고 다시 검사하면 이전 판정과 달라진 항목을 보여줍니다." : "패키지에 포함된 파일을 확인한 뒤 제출 전 검사를 시작합니다."} />
    {session && <PreflightPackageWorkspace
      session={session} recheck={recheck} busy={busy} readiness={readiness} acknowledged={acknowledged}
      selected={selected} error={error} pollError={pollError} onSelectFiles={selectFiles}
      onUpload={() => void run(upload)} onChooseDemo={fixture => void run(() => choose(fixture))}
      onAcknowledge={setAcknowledged} onValidate={() => void run(validate)}
    />}
  </WorkflowGuard>;
}

export function ResultsScreen() {
  const { session } = useSession();
  return <WorkflowGuard step="results"><ModeNote /><PageTitle step="04 / PREFLIGHT RESULTS" title="근거를 확인하고, 제출을 준비하세요" description="판정별 근거와 필요한 조치를 확인한 뒤 수정한 파일로 다시 검사할 수 있습니다." />
    {session && <ResultsWorkspace session={session} />}
  </WorkflowGuard>;
}
