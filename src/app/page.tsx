"use client";

import { useState } from "react";
import { Code, Loader2, Play, Sparkles } from "lucide-react";

type Result = {
  plan: string;
  files: Record<string, string>;
};

export default function Home() {
  const [requirement, setRequirement] = useState("生成一个咖啡店点单小程序，包含商品列表、数量选择、提交订单按钮");
  const [result, setResult] = useState<Result | null>(null);
  const [activeFile, setActiveFile] = useState("index.wxml");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requirement })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "生成失败");

      setResult(data);
      setActiveFile(Object.keys(data.files)[0]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f5f7fb] text-slate-950">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-6 py-4">
          <Sparkles className="h-6 w-6 text-blue-600" />
          <div>
            <h1 className="text-xl font-semibold">Gemma 4 AI 小程序生成平台</h1>
            <p className="text-sm text-slate-500">Agent 规划、生成微信小程序代码、分文件展示</p>
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl grid-cols-1 gap-4 px-6 py-6 lg:grid-cols-[360px_1fr_1fr]">
        <aside className="rounded-lg border bg-white p-4">
          <h2 className="mb-3 font-semibold">输入需求</h2>
          <textarea
            value={requirement}
            onChange={(event) => setRequirement(event.target.value)}
            className="h-52 w-full resize-none rounded-md border p-3 text-sm outline-none focus:border-blue-500"
          />
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="mt-4 flex h-10 w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-4 text-sm font-medium text-white disabled:opacity-60"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            一键生成
          </button>
          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        </aside>

        <section className="rounded-lg border bg-white p-4">
          <h2 className="mb-3 font-semibold">Agent 规划</h2>
          <div className="min-h-52 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-sm text-slate-700">
            {result?.plan || "生成后这里会展示 Gemma Agent 的需求理解和页面规划。"}
          </div>
        </section>

        <section className="rounded-lg border bg-white p-4">
          <div className="mb-3 flex items-center gap-2">
            <Code className="h-4 w-4" />
            <h2 className="font-semibold">生成代码</h2>
          </div>

          {result ? (
            <>
              <div className="mb-3 flex flex-wrap gap-2">
                {Object.keys(result.files).map((file) => (
                  <button
                    key={file}
                    onClick={() => setActiveFile(file)}
                    className={`rounded-md border px-3 py-1 text-sm ${
                      activeFile === file ? "border-blue-600 bg-blue-50 text-blue-700" : "bg-white"
                    }`}
                  >
                    {file}
                  </button>
                ))}
              </div>
              <pre className="h-[480px] overflow-auto rounded-md bg-slate-950 p-4 text-xs text-slate-100">
                {result.files[activeFile]}
              </pre>
            </>
          ) : (
            <div className="rounded-md bg-slate-50 p-3 text-sm text-slate-500">
              代码会按 index.wxml、index.wxss、index.js、app.json 分文件展示。
            </div>
          )}
        </section>
      </section>
    </main>
  );
}