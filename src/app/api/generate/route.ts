import { NextRequest, NextResponse } from "next/server";
import { generateMiniProgram } from "@/lib/agent";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const requirement = String(body.requirement || "").trim();

    if (!requirement) {
      return NextResponse.json({ error: "请输入小程序需求" }, { status: 400 });
    }

    const result = await generateMiniProgram(requirement);
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "生成失败" },
      { status: 500 }
    );
  }
}