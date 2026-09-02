"use client";
export default function ErrorBoundary({ reset }: { reset: () => void }) {
  return <section className="empty" role="alert"><h1>화면을 불러오지 못했습니다</h1><p>다시 시도하거나 홈에서 새 검사를 시작해 주세요.</p><button className="button primary" onClick={reset}>다시 시도</button><a className="button secondary" href="/">홈으로</a></section>;
}
