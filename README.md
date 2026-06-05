# Gemma 4 AI 小程序生成平台

面向 Google Gemma 4 Hackathon Track A「AI Agent 开发」的参赛项目。

本项目是一个基于 Gemma 4 的 AI 小程序生成平台。用户只需要输入一句自然语言需求，例如“生成一个咖啡店点单小程序”，系统会通过 Gemma Agent 完成需求理解、页面规划，并生成微信小程序所需的 `index.wxml`、`index.wxss`、`index.js`、`app.json` 等代码文件。

## 项目目标

降低小程序开发门槛，让没有完整开发经验的用户也可以通过自然语言快速生成小程序原型。

本项目重点展示：

- Gemma 4 对自然语言需求的理解能力
- AI Agent 的多步骤任务拆解能力
- 小程序代码的自动生成能力
- 分文件代码展示，方便后续复制到微信开发者工具中继续开发

## 核心功能

- 自然语言输入小程序需求
- 预设 Demo 场景快速生成
  - 咖啡店点单小程序
  - 课程报名小程序
  - 个人作品集小程序
- Gemma Agent 自动输出页面规划
- 自动生成微信小程序代码文件
  - `index.wxml`
  - `index.wxss`
  - `index.js`
  - `app.json`
- 分文件 Tab 展示生成代码
- 支持复制当前文件代码
- 本地 LM Studio 接入 Gemma 4 模型

## 技术架构

```text
用户需求
  ↓
Next.js 前端页面
  ↓
API Route /api/generate
  ↓
Gemma Agent Prompt 编排
  ↓
LM Studio OpenAI-compatible API
  ↓
Gemma 4 E4B Instruct
  ↓
返回 Agent 规划 + 小程序代码文件