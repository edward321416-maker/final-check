"use client";
export default function ErrorBoundary({ reset }: { reset: () => void }) {
  return <section className="recovery-state empty" role="alert"><h1>화면을 불러오지 못했습니다</h1><p>현재 검사 상태는 가능한 범위에서 유지됩니다. 다시 시도하거나 홈에서 새 검사를 시작할 수 있습니다.</p><button className="button primary" onClick={reset}>다시 시도</button><a className="button secondary" href="/">홈으로</a></section>;
}
