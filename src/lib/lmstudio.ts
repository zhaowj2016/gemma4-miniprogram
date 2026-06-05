type ChatMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

export async function callGemma(messages: ChatMessage[]) {
  const baseUrl = process.env.LMSTUDIO_BASE_URL || "http://127.0.0.1:1234/v1";
  const model = process.env.LMSTUDIO_MODEL || "local-model";

  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model,
      messages,
      temperature: 0.2,
      max_tokens: 5000
    })
  });

  if (!response.ok) {
    throw new Error(`LM Studio 调用失败：${response.status} ${await response.text()}`);
  }

  const data = await response.json();
  return data.choices?.[0]?.message?.content || "";
}