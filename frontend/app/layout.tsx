import type { Metadata } from "next";
import Link from "next/link";
import { SessionProvider } from "@/components/session-provider";
import { Navigation } from "@/components/ui";
import "./globals.css";

export const metadata: Metadata = { title: "FINAL CHECK — AI Submission Preflight", description: "공고와 제출파일의 근거를 확인하는 제출 전 검사. 동결 Validator v1.5 실제 파일 검사 demo." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ko"><body><SessionProvider><a className="skip-link" href="#main">본문으로 이동</a>
    <header className="site-header"><Link href="/" className="brand"><span className="brand-mark">✓</span>FINAL CHECK<span className="brand-sub">AI SUBMISSION PREFLIGHT</span></Link><span className="header-note"><span className="dot" /> MVP / DEMO</span></header>
    <div className="shell"><Navigation /><main id="main">{children}</main><footer className="site-footer"><strong>FINAL CHECK</strong><span>확신은, 근거에서 시작됩니다.</span><span>FROZEN v1.5 · LOCAL DEMO</span></footer></div>
  </SessionProvider></body></html>;
}
