import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gemma 4 AI 小程序生成平台",
  description: "使用 Gemma 4 和 LM Studio 构建的 AI Agent 小程序生成平台"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}