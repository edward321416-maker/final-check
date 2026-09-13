import Link from "next/link";
export default function NotFound() { return <section className="recovery-state empty"><h1>페이지를 찾을 수 없습니다</h1><p>주소를 확인하거나 홈에서 새 검사를 시작해 주세요.</p><Link className="button primary" href="/">홈으로 돌아가기</Link></section>; }
