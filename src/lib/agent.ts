import { callGemma } from "./lmstudio";

export type GeneratedMiniProgram = {
  plan: string;
  files: {
    "index.wxml": string;
    "index.wxss": string;
    "index.js": string;
    "app.json": string;
  };
};

function extractTag(content: string, tag: string) {
  const match = content.match(new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`, "i"));
  return match?.[1]?.trim() || "";
}

function extractFile(content: string, fileName: string) {
  const pattern = `<file name="${fileName}">([\\s\\S]*?)<\\/file>`;
  const match = content.match(new RegExp(pattern, "i"));
  return match?.[1]?.trim() || "";
}

export async function generateMiniProgram(requirement: string): Promise<GeneratedMiniProgram> {
  const prompt = `
你是参加 Google Gemma 4 Hackathon 的 AI Agent。
你的任务是根据用户需求生成微信小程序代码。

请严格按照下面格式输出，不要输出 Markdown，不要输出 JSON，不要额外解释。

<plan>
这里写你的需求理解、页面结构、交互逻辑、生成步骤。
</plan>

<file name="index.wxml">
这里写完整 index.wxml
</file>

<file name="index.wxss">
这里写完整 index.wxss
</file>

<file name="index.js">
这里写完整 index.js
</file>

<file name="app.json">
这里写完整 app.json
</file>

要求：
1. 必须生成完整可运行的微信小程序页面代码。
2. index.wxml 使用 view、text、button、input 等微信小程序组件。
3. index.wxss 写清晰美观的样式。
4. index.js 包含 data 和事件处理函数。
5. app.json 必须是合法 JSON。

用户需求：
${requirement}
`;

  const content = await callGemma([
    {
      role: "system",
      content: "你是专业微信小程序开发 Agent，必须严格按照用户要求的标签格式输出。"
    },
    {
      role: "user",
      content: prompt
    }
  ]);

  const plan = extractTag(content, "plan") || "Gemma Agent 已完成需求理解，但输出格式不完整。";

  const files = {
    "index.wxml": extractFile(content, "index.wxml"),
    "index.wxss": extractFile(content, "index.wxss"),
    "index.js": extractFile(content, "index.js"),
    "app.json": extractFile(content, "app.json")
  };

  if (!files["index.wxml"] && !files["index.wxss"] && !files["index.js"]) {
    files["index.wxml"] = content;
    files["index.wxss"] = "";
    files["index.js"] = "";
    files["app.json"] = "";
  }

  return {
    plan,
    files
  };
}