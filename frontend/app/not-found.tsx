import Link from "next/link";
export default function NotFound() { return <section className="empty"><h1>페이지를 찾을 수 없습니다</h1><Link className="button primary" href="/">홈으로 돌아가기</Link></section>; }
