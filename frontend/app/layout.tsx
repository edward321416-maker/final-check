import type { Metadata } from "next";
import { AppChrome } from "@/components/app-chrome";
import { SessionProvider } from "@/components/session-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "FINAL CHECK — AI Submission Preflight",
  description: "공고와 제출파일의 근거를 확인하는 제출 전 검사. 동결 Validator v1.5 실제 파일 검사 demo.",
  robots: { index: false, follow: false },
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ko"><body><SessionProvider><a className="skip-link" href="#main">본문으로 이동</a>
    <AppChrome>{children}</AppChrome>
  </SessionProvider></body></html>;
}
