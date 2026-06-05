```md
# AI小程序生成平台

## 项目简介

AI小程序生成平台是爱(AI)学爱(AI)创营面向 Google Gemma 4 Hackathon 赛道 A「AI Agent 开发」提交的参赛项目。

项目目标是让用户通过自然语言快速生成微信小程序原型。用户只需要输入一句需求，例如“生成一个咖啡店点单小程序，包含商品列表、数量选择、提交订单按钮”，系统就会调用本地运行的 Gemma 4 模型，完成需求理解、页面规划，并生成微信小程序所需的核心代码文件。

生成结果包括：

- `index.wxml`
- `index.wxss`
- `index.js`
- `app.json`

本项目不是简单的单轮文本生成，而是将“小程序生成”拆解为 Agent 工作流：需求理解、页面规划、组件生成、分文件输出。

## 参赛信息

- 比赛：Google Gemma 4 Hackathon
- 赛道：Track A - AI Agent 开发
- 项目名称：AI小程序生成平台
- 组名：爱(AI)学爱(AI)创营
- 核心模型：Gemma 4 E4B Instruct
- 模型运行方式：LM Studio 本地运行
- 项目类型：AI Agent / 小程序代码生成 / 开发辅助工具

## 项目背景

小程序开发通常需要开发者理解页面结构、样式、交互逻辑和工程文件组织。对于开发小白或非技术用户来说，从一个想法到可运行原型之间存在较高门槛。

本项目希望通过 Gemma 4 的自然语言理解和代码生成能力，构建一个 AI 小程序生成平台。用户只需要描述需求，系统即可自动完成小程序原型代码生成，从而降低开发门槛，提高原型搭建效率。

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
- 固定标签协议解析模型输出，提升代码生成稳定性

## Demo 场景

### 咖啡店点单小程序

输入示例：

```text
生成一个咖啡店点单小程序，包含商品列表、数量选择、提交订单按钮
```

生成内容包括商品列表、数量选择、价格展示、订单提交按钮等小程序代码。

### 课程报名小程序

输入示例：

```text
请帮我生成课程报名小程序
```

生成内容包括课程列表、课程筛选、报名按钮和报名交互逻辑。

### 个人作品集小程序

输入示例：

```text
个人作品集小程序
```

生成内容包括个人简介、项目展示、技能标签和联系方式模块。

## 技术架构

```text
用户自然语言需求
  ↓
Next.js 前端页面
  ↓
/api/generate API Route
  ↓
Agent Prompt 编排
  ↓
LM Studio OpenAI-compatible API
  ↓
Gemma 4 E4B Instruct
  ↓
返回 Agent 规划 + 小程序代码文件
  ↓
前端分文件展示
```

## 技术栈

- Next.js
- React
- TypeScript
- Tailwind CSS
- LM Studio
- Gemma 4 E4B Instruct

## 目录结构

```text
gemma4-miniprogram/
  src/
    app/
      api/
        generate/
          route.ts
      globals.css
      layout.tsx
      page.tsx
    lib/
      agent.ts
      lmstudio.ts
  package.json
  package-lock.json
  next.config.ts
  postcss.config.mjs
  tailwind.config.ts
  tsconfig.json
  README.md
  TECH_REPORT.md
  requirements.txt
```

## 环境安装步骤

### 1. 安装 Node.js

请安装 Node.js 20 或以上版本。

验证：

```bash
node -v
npm -v
```

### 2. 安装 LM Studio

下载并安装 LM Studio：

```text
https://lmstudio.ai/
```

在 LM Studio 中下载并加载模型：

```text
lmstudio-community/Gemma 4 E4B Instruct
```

### 3. 启动 LM Studio Local Server

在 LM Studio 中进入 Local Server / Developer Server 页面，启动本地 API 服务。

默认地址：

```text
http://127.0.0.1:1234/v1
```

可在浏览器中访问：

```text
http://127.0.0.1:1234/v1
```

如果看到 LM Studio 的 API 返回信息，说明服务已启动。

### 4. 安装项目依赖

在项目根目录执行：

```bash
npm install
```

### 5. 配置环境变量

新建 `.env.local` 文件：

```env
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_MODEL=lmstudio-community/Gemma 4 E4B Instruct
```

如果 LM Studio 中显示的模型名称不同，请将 `LMSTUDIO_MODEL` 改成 LM Studio Local Server 页面中的实际模型 ID。

### 6. 启动项目

```bash
npm run dev
```

浏览器打开：

```text
http://localhost:3000
```

## requirements.txt 说明

比赛要求提交 `requirements.txt`。本项目是 Next.js + TypeScript 项目，不使用 Python 依赖，实际依赖由 `package.json` 和 `package-lock.json` 管理。

`requirements.txt` 中保留运行环境说明：

```text
Node.js >= 20
npm >= 10
LM Studio
Gemma 4 E4B Instruct
```

## Gemma 4 使用方式

本项目通过 LM Studio 在本地运行 Gemma 4，并使用 OpenAI-compatible API 调用模型。

相关调用逻辑位于：

```text
src/lib/lmstudio.ts
src/lib/agent.ts
src/app/api/generate/route.ts
```

调用流程：

1. 前端将用户需求提交到 `/api/generate`
2. 后端构造 Agent Prompt
3. 后端请求 LM Studio 本地接口
4. Gemma 4 返回规划内容和小程序代码
5. 前端解析并展示生成结果

## Agent 工作流设计

本项目面向赛道 A: AI Agent 开发，重点不是简单代码生成，而是将任务拆解为可解释的 Agent 流程。

### 1. 需求理解

Gemma Agent 首先理解用户输入，识别小程序类型、目标用户、核心页面和主要功能。

例如：

```text
用户输入：生成一个咖啡店点单小程序
Agent 理解：需要商品列表、数量选择、订单合计和提交按钮
```

### 2. 页面规划

Agent 会输出页面结构规划，包括页面区域、组件布局和交互逻辑。

例如：

```text
顶部标题区域
商品列表区域
数量选择区域
订单合计区域
提交订单按钮
```

### 3. 组件生成

Agent 根据规划生成微信小程序组件代码，包括：

- `view`
- `text`
- `button`
- `input`
- 列表循环
- 事件绑定

### 4. 分文件输出

Agent 最终按微信小程序工程结构输出：

```text
index.wxml
index.wxss
index.js
app.json
```

前端再将这些文件分 Tab 展示，方便用户复制和继续开发。

## Agent Memory 与 Tool Calling 设计

### Memory 设计

当前版本在前端维护轻量级上下文状态，包括：

- 当前用户需求
- 当前 Agent 规划结果
- 当前生成文件集合
- 当前选中的代码文件
- 当前生成状态和错误状态

这些状态构成一次生成任务中的短期 Memory，使用户可以在同一页面中查看完整生成过程和结果。

### Tool Calling 设计

当前版本采用“受控工具协议”的方式组织模型输出。系统要求 Gemma 4 按固定标签格式返回内容：

```text
<plan>
Agent 规划内容
</plan>

<file name="index.wxml">
WXML 代码
</file>

<file name="index.wxss">
WXSS 代码
</file>

<file name="index.js">
JS 代码
</file>

<file name="app.json">
app.json 代码
</file>
```

应用侧会解析这些标签，并将其转换为结构化文件对象：

```ts
{
  plan: string,
  files: {
    "index.wxml": string,
    "index.wxss": string,
    "index.js": string,
    "app.json": string
  }
}
```

这种设计相当于将模型输出限制在可解析的工具协议中，避免自由文本难以处理的问题。

后续可扩展为更完整的真实工具调用，例如：

- `create_project_plan(requirement)`
- `generate_file(path, content)`
- `read_file(path)`
- `repair_error(errorLog)`
- `export_zip()`

## 核心源码说明

### `src/app/page.tsx`

前端主页面，负责：

- 展示输入框
- 展示预设 Demo
- 调用生成接口
- 展示 Agent 规划
- 分文件展示生成代码
- 复制当前文件代码

### `src/app/api/generate/route.ts`

后端 API Route，负责：

- 接收用户需求
- 调用 Agent 生成逻辑
- 返回结构化生成结果

### `src/lib/agent.ts`

Agent 核心逻辑，负责：

- 构造 Agent Prompt
- 要求模型按固定标签协议输出
- 解析 `<plan>` 和 `<file>` 标签
- 生成最终结构化结果

### `src/lib/lmstudio.ts`

LM Studio 调用封装，负责：

- 读取环境变量
- 调用本地 Gemma 4 模型
- 返回模型输出文本

## 运行日志示例

运行项目：

```bash
npm run dev
```

示例输出：

```text
Next.js 15.x
Local: http://localhost:3000
Ready
```

调用 LM Studio 成功后，页面会显示：

- Agent 规划
- `index.wxml`
- `index.wxss`
- `index.js`
- `app.json`

## 项目亮点

- 使用 Gemma 4 作为核心生成模型
- 面向 AI Agent 赛道设计，展示可解释生成流程
- 支持自然语言到微信小程序代码生成
- 使用本地模型运行，保护用户需求隐私
- 输出接近真实微信小程序工程结构
- 标签协议比直接 JSON 输出更适合承载代码内容
- 适合小白用户快速生成小程序原型

## 当前限制

- 当前版本主要生成微信小程序页面代码，尚未直接接入微信开发者工具编译
- 当前版本未实现真实 ZIP 导出
- 复杂多页面小程序仍需要进一步增强
- 生成结果依赖模型输出质量，复杂需求可能需要多次生成

## 后续计划

- 增加导出 ZIP 功能
- 增加小程序页面实时预览
- 增加代码校验和自动修复
- 增加更多标准组件工具函数
- 增加多页面小程序生成能力
- 增加真实 Function Calling 工具执行链路

## 提交内容

本项目提交内容包括：

- `README.md`
- `requirements.txt`
- `TECH_REPORT.md`
- 核心源码目录 `src/`
- Next.js 项目配置文件
- `package.json`
- `package-lock.json`

## 总结

AI小程序生成平台验证了 Gemma 4 在 AI Agent 开发辅助场景中的可行性。通过自然语言输入、Agent 规划和分文件代码生成，用户可以快速获得一个可继续开发的小程序原型。

该项目可用于小白用户快速入门、小程序原型设计、开发者辅助生成页面代码等场景。
```