

# MiniPilot Agent

**GDG Shanghai · Gemma 4 Developer Competition · Track A — Autonomous AI Agent / Agentic Code Generation**

## One-line Pitch

> MiniPilot Agent transforms Gemma 4 from a chat model into an MVP generation agent for small businesses' WeChat Mini Programs.
>
> MiniPilot Agent turns Gemma 4 from a chat model into a small-business WeChat Mini Program MVP generation agent.

A single natural language description of a business idea → The Agent understands the requirements via **Gemma 4 Function Calling**, generates structured code, self-validates and repairs it, and packages the user-uploaded images and local assets into a real Mini Program project, delivering a **previewable and downloadable** Mini Program page prototype.

---

## Project Overview

**Competition**: GDG Shanghai · Gemma 4 Developer Competition (Track A — Autonomous AI Agent / Agentic Code Generation)
**Core Model**: Gemma 4 (Google AI Studio hosted `gemma-4-27b-it` / `gemma-4-31b-it` + AMD vLLM self-hosted `gemma-4-31b-it`, both **Dense** architecture)

**What we most want to show the judges is not "it can generate code", but rather**:

1. Gemma 4's Native Function Calling is used as the core source of system reliability, not as a decorative feature — dual backends, a unified protocol, and a three-tier parsing priority are all designed to ensure that "structured output" holds up in any environment;
2. A true multi-step Agent closed loop capable of "detecting issues itself, understanding errors itself, and correcting them itself" (Validator + Self-Correction);
3. Engineering rigor regarding "whether generated content can withstand real-world testing" — the grounding case study is the most direct evidence;
4. An honest declaration of engineering boundaries: clearly knowing what has been achieved and what is missing — this is itself a part of technical maturity.
5. Web introduction: https://minipilot-agent.vercel.app/

```text
MiniPilot Agent turns Gemma 4 from a chat model into a small-business software prototyping agent.
Through MiniPilot Agent, a small business's idea can be transformed into a previewable Mini Program MVP by Gemma 4.
```

---

## Project Repository Link

GitHub Repository:

https://github.com/zhaowj2016/gemma4-miniprogram.git

---

## Demo Video

The demo video is placed in the repository:

`docs/demo/演示视频_AI小程序生成平台.mp4`

[演示视频_AI小程序生成平台.mp4](docs/demo/%E6%BC%94%E7%A4%BA%E8%A7%86%E9%A2%91_AI%E5%B0%8F%E7%A8%8B%E5%BA%8F%E7%94%9F%E6%88%90%E5%B9%B3%E5%8F%B0.mp4)

---

## Problem — The Real Problem It Solves (Corresponding to "Real Impact" 30%)

Small businesses, individual operators, and local service merchants want to build a Mini Program but often get stuck at the first step:

- Lack of coding skills; traditional outsourcing quotes range from thousands to tens of thousands of RMB, take weeks, and have high communication costs;
- Most of the time, they don't need to launch a complete system immediately, but rather want to see an MVP first to intuitively judge "if this idea works";
- Coffee ordering, event registration, store introduction, appointment forms, product displays — for these high-frequency, small-scale needs, hiring a professional team to develop them actually has the lowest "cost-performance ratio".

**Target Users**: Small businesses / offline stores / individual operators / local service merchants / people who don't know how to code but want to quickly validate Mini Program ideas.

**Typical Prompts** (also recommended stable demo cases for this project):

- "Help me generate a coffee shop ordering Mini Program page, featuring a product list, shopping cart, and bottom checkout button"
- "Help me generate an event registration page, featuring an event introduction, name/phone input fields, and a registration button"
- "Help me generate a store introduction page, featuring a store cover image, business hours, address, contact phone number, and a reservation button"

MiniPilot Agent is **not intended to replace professional development**, but rather compresses the Mini Program MVP process that originally required "communication → design → development" for validation into a single natural language input — lowering the prototype threshold, reducing trial-and-error costs, shortening the cycle from idea to visual prototype, and enabling non-technical users to quickly see results.

---

## Solution

User inputs a one-sentence requirement (optional image upload) →
Gemma 4 completes requirement understanding → calls the `create_miniprogram_page` tool via **Function Calling / Tool Calling** to generate the structured `wxml / wxss / js` trio →
**Static Validator** performs static validation → triggers **Self-Correction** for self-healing repair (sends errors back to Gemma to regenerate) →
**Web-side mobile preview** real-time rendering + **ZIP export**. Uploaded images are saved to `assets/uploads/`, and local industry assets come from `assets/library/`; exports and WeChat previews only carry the assets actually used on the current page to avoid triggering WeChat's 2MB preview package limit.

Its core is not "calling a model to spit out code", but truly placing Gemma 4 into a **software production pipeline**: understanding requirements, calling tools, generating code, accepting validation, fixing errors, and outputting visual results — forming a closed-loop Agentic Workflow.

---

## Demo

- See [How to Run](#how-to-run) below for startup instructions; online demo / Vercel link can be found in the submission registration info.
- **Recommended Demo Prompts** (from recent real iterations with more stable and explainable scenarios, recommended for judging / recording):
  1. `Help me generate a coffee shop ordering Mini Program page, featuring a product list, shopping cart, and bottom checkout button`
  2. `Help me generate an event registration page, featuring an event introduction, name/phone input fields, and a registration button`
  3. `Generate an e-commerce product detail page, including a main product image, price, specification selector, discount info, and a bottom purchase button`
- `app_showcase.py` (port 8504) is the external showcase page, featuring carefully selected real-world examples suitable for storytelling, such as AI wedding studios, Michelin restaurants, and coffee ordering.
- `app_demo.py` (port 8505) is the real-time generation page, displaying the complete closed loop of Brief → Gemma Agent Trace → Phone Preview → Source / Zip / WeChat Preview. The preview area persists the most recent generation result to avoid losing long code samples after a page refresh.

---

## Agent Pipeline

```text
User natural language requirement (optional reference image)
  │
  ▼
P0  Requirement Understanding  gemma-4-27b-it text reasoning, complements vague intents, extracts scene and style directions
  │
  ▼
P1  Function Calling   gemma-4-31b-it calls via the create_miniprogram_page tool
  │                    (Google AI Studio main chain ←→ AMD vLLM Gemma 31B self-hosted chain)
  ▼
P2  Code Generation   Structurally outputs the wxml / wxss / js trio
  │
  ▼
P3  Tool Call Parsing  Unified parsing layer parse_llm_message:
  │                    standard_tool_calls → gemma_raw_tool_call → plain_text_fallback
  ▼
P4  Static Validation  validators.py static gatekeeper
  │                    (Mixed HTML tags / dangerous APIs / sensitive fields / missing event bindings...)
  ▼
P5  Self-Correction   Validation fails → errors sent back to Gemma for regeneration → re-validation
  │                    Still fails → fallback to the closest pre-validated golden example
  ▼
P6  Preview / Export   Web-side mobile preview (WXML→HTML rendering + WeChat Runtime Shim)
                       + ZIP export + share link
```

---

## Architecture

```text
Frontend (Streamlit · app_demo.py / app_showcase.py)
  │
  ▼
Model Router  (gemma_client.call_gemma_with_tools)
  ├─ AMD vLLM Client        Self-hosted Gemma 31B (model: gemm)
  │                         OpenAI-compatible /v1/chat/completions
  │                         + tools / tool_choice + vLLM --tool-call-parser gemma4, streaming response
  │
  └─ Google AI Studio Client   gemma-4-31b-it Native Function Calling
                               functionDeclarations + toolConfig.AUTO
                               Officially hosted, acting as a stable main chain / failure fallback
  │
  ▼
Unified Tool Call Parsing Layer  parse_llm_message
  (Three-tier priority: standard_tool_calls / gemma_raw_tool_call / plain_text_fallback,
    Google and AMD share the same contract, uniformly returning {wxml, wxss, js, provider, parse_method})
  │
  ▼
Static Validator (validators.py)  →  Self-Correction (prompt_builder.build_repair_prompt)
  │
  ▼
Render Layer: render_wxml.py (mobile preview) / zip_exporter.py (project export) / share link
```

> Note: The current code consolidates the "model routing / dual-backend clients / tool call parsing layer" into a single file [`gemma_client.py`](gemma_client.py) (rather than splitting into multiple independent modules). The logical boundaries are clear and responsibilities are singular; this merely differs slightly from the early planning draft in physical file organization — code references in the technical report are based on actual file paths.

---

## Gemma 4 Usage

| Usage | Model | Invocation Method |
| -------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Requirement clarification / text understanding | `gemma-4-27b-it` (Google AI Studio) | Standard text generation, extracting scene keywords and style directions |
| Code generation + self-audit (main chain) | `gemma-4-31b-it` (Google AI Studio, **Dense**) | **Native Function Calling**: `functionDeclarations` + `toolConfig.AUTO` enforces structured output |
| Code generation (self-hosted deep chain) | `gemma-4-31b-it` (AMD vLLM self-hosted, **Dense**, served name `gemm`) | OpenAI-compatible `tools` + `tool_choice`, paired with vLLM `--tool-call-parser gemma4` |
| Long context / long output | AMD vLLM (`max_model_len = 32768`) | Suitable for complex page generation and multi-turn modification scenarios |

> **Model Selection Note**: `Gemma 4 26B-A4B` uses a **MoE** architecture, while `Gemma 4 31B` uses a **Dense** architecture — both chains in this project utilize the **31B Dense** model.

**Why dual backends**:

- **Google AI Studio = Agent Mode (stable main chain)** — Officially hosted API, complete native Function Calling support, low deployment risk, suitable for stable demonstration of the Agent tool calling process at the competition;
- **AMD vLLM Gemma 31B = Deep Generation Mode (technical depth validation)** — Validates the private deployment capability of open-source Gemma 4, providing longer context, longer output, and fewer rate limits, making it more suitable for complex page generation and multi-turn modifications. It also serves as a feasibility validation for the "future private deployment + scaling" route. The two chains are not mutually exclusive: Google is responsible for stably demonstrating native Function Calling, while AMD is responsible for validating long context / long output / private deployment capabilities.

---

## Key Features

### 1. Native Function Calling, Not Simple Text Parsing (Technical Excellence 25%)

The model must structurally output the `wxml / wxss / js` trio via the `create_miniprogram_page` tool — this is not a matter of "preferred invocation method", but rather a design choice to make **Gemma 4's structured reasoning capability the direct source of system reliability**. The current implementation retains live / parser / AMD tool-calls verification scripts; competition demonstrations will rely on real-time API availability, avoiding packaging a single old live statistic into a permanent promise.

### 2. Dual-Backend Unified Tool Protocol (Technical Excellence 25% / Innovation 15%)

Google AI Studio and the AMD self-hosted vLLM share the same `create_miniprogram_page` tool protocol and both connect to the same unified parsing layer — meaning self-deployed models and official APIs can seamlessly serve as backups for each other and switch smoothly, rather than maintaining two disconnected code paths.

### 3. Three-Tier Tool Call Parsing Priority: standard → raw envelope → plain text (Technical Excellence 25%)

- **Tier 1** `standard_tool_calls`: Standard OpenAI format `tool_calls[]` (outputs from Google `functionCall` and AMD vLLM `gemma4` parser are both unified to this tier)
- **Tier 2** `gemma_raw_tool_call`: Regex adaptation fallback when Gemma's native `<|tool_call>...<tool_call|>` envelope is exposed as plain text
- **Tier 3** `plain_text_fallback`: Pure three-part marker text parsing, the final line of defense
The three tiers do not replace each other and do not silently swallow errors — hits from each tier are logged, and the frontend synchronously displays the `provider` and `parse_method` actually hit by the current request, making exactly "how this was parsed" completely transparent to judges (see [`gemma_client.parse_llm_message`](gemma_client.py)).

### 4. Static Validator Gatekeeper (Functional Completeness 20%)

A strict pre-flight check before outbound transmission: checks if WXML/WXSS/JS are completely generated, misuse of HTML tags, illegal function calls inside `{{}}`, misuse of `<swiper current-index>`, JS `Page({})` construction, missing event bindings, dangerous real-capability APIs like `wx.login / wx.requestPayment / wx.cloud`, and leakage of sensitive fields like `appsecret / private_key / access_token / session_key`. HARD errors block outbound traffic and trigger self-healing, while WARNINGs only display without blocking — the reasoning is straightforward: "a slightly flawed but downloadable Zip is always better than a perfect Zip wrongly blocked."

### 5. Self-Correction Closed Loop (Innovation 15% / Functional Completeness 20%)

The official FAQ's best practice recommendation for Function Calling is: when the model returns a non-standard format, robust exception handling code should be written to trigger Agent self-correction. The corresponding implementation in MiniPilot Agent: generate code → Validator checks → detects HARD error → sends specific error info back to Gemma for regeneration → re-validates; if it still fails, it falls back to the pre-validated golden example closest to the original requirement, ensuring the demo chain never interrupts.

### 6. Grounded Image Asset Pipeline (Innovation 15%)

Real Problem: Models generate image paths that are perfectly formatted and visually indistinguishable but inaccessible in real Mini Programs. The solution has been upgraded from "making the model remember remote URLs" to "backend providing a local `asset_list`": user-uploaded images are saved as `assets/uploads/user_upload_###.ext`, and the industry asset library is saved as `assets/library/...`. Prompts strongly constrain the model to only use `/assets/uploads/...` or `/assets/library/...`. If the model misses inserting images, the backend will fallback-insert a hero image; if polluted paths like `blob / localhost / data:image / tmp / Unsplash / Picsum` appear, the Validator will block them.

Recent asset audit logs are in [`docs/image_asset_audit_report.md`](docs/image_asset_audit_report.md): 262 historical remote image candidates were checked, of which 169 were valid, and 93 were invalid / templates / non-images; the current runtime asset library covers 9 industry directories with a total of 27 local image assets. The old Unsplash grounding post-mortem remains in [`docs/unsplash_grounding_case_study.md`](docs/unsplash_grounding_case_study.md), serving as evidence of why a local asset pipeline is necessary.

### 7. Web-Side Mobile Preview (Functional Completeness 20%)

Self-developed WXML → HTML rendering pipeline + lightweight WeChat Runtime Shim ([`render_wxml.py`](render_wxml.py)): tag conversion, `wx:for` loop expansion, `wx:if` conditional rendering, `bindtap` event routing, common API mocks like `wx.showToast / navigateTo / getSystemInfo / Storage` + `Page() / setData`, allowing interactive preview of generation results in the browser without installing the WeChat Developer Tool. **This is a low-fidelity web-side simulation, not an official WeChat real-device rendering or Developer Tool compilation result.**

---

## Current Status — Honest Capability Grading

To avoid "over-promising", the following honestly distinguishes three tiers: **Implemented / Semi-Implemented / Roadmap** (this itself is part of the engineering maturity we wish to demonstrate):

### ✅ Implemented and Verified (Can be directly demonstrated)

- MiniPilot Agent branded showcase page (8504) + real-time generation page (8505)
- Google AI Studio API call + Native Function Calling (retains live verification scripts; on-site results are subject to API / quota)
- AMD vLLM Gemma 31B self-hosted inference + standard `tool_calls` return (verified hit `parse_method = standard_tool_calls`)
- Unified Tool Call parsing layer (three-tier priority, Google + AMD share the same contract, frontend visible `provider` / `parse_method`)
- Raw `<|tool_call>` envelope fallback parsing (adaptation layer when Gemma's private format is exposed as text, not replaced or deleted by new logic)
- Long context Prompt assembly (requirement clarification + few-shot golden example retrieval + design style randomization)
- Local image asset_list injection: user-uploaded images go into `assets/uploads/`, industry assets into `assets/library/`
- Image path pollution interception: prevents `blob / localhost / data:image / tmp / Unsplash / Picsum` from entering WXML
- Image fallback insertion: when the model doesn't use uploaded / hero images, the backend automatically appends `<image class="hero-image" ... />`
- WXML / WXSS / JS trio unpacking parsing
- Static Validator gatekeeper (integrated into main flow, validation results displayed to users in real-time)
- Self-Correction self-healing (triggered by HARD errors, errors sent back for regeneration, falls back to golden examples if still failing)
- Web-side mobile preview (WXML → HTML rendering + WeChat Runtime Shim)
- ZIP export + share link; Zip contains all user-uploaded images and `assets/library` assets referenced by the current page

### ⚙️ Semi-Implemented / Partially Verified (Code exists, but has boundary conditions or external dependencies)

- **WeChat Official Real-Device Preview QR Code**: [`ci_deployer.py`](ci_deployer.py) has genuinely integrated the official `miniprogram-ci` / `upload.js`, copying page files, uploaded images, and local assets to the same `projectPath` before previewing; however, it relies on real AppID, private keys, CI permissions, IP whitelists, and WeChat-side rate limits, so it is not used as a core display path but kept as an optional advanced capability;
- **Availability of AMD vLLM Self-Hosted Chain**: Relies on external cloud GPU instances; instance restarts cause gateway address changes, requiring manual configuration synchronization — technically verified feasible (standard `tool_calls` stably hit), but does not yet possess production-grade "out-of-the-box" stability;
- **Image Cropping**: Uploaded images undergo lightweight automatic edge cropping, suitable for handling screenshot edge black blocks / blank borders, but is not yet a complete manual cropper or multi-image album editor.

### 🗺️ Roadmap (Explicitly listed, not confused with "Implemented")

- More complete user image editing: manual cropping, subject localization, multi-image sorting, and asset management
- LoRA / SFT to improve output format stability (see "Why no fine-tuning currently" in Limitations)
- Incorporate `miniprogram-ci` validation into the main flow's automated gatekeeper (currently optional manual operation)
- Multi-turn modification input box / commercial template marketplace
- More scenarios of "import to WeChat Developer Tool" manual validation records and screenshots

---

## Limitations

Honest declaration of current engineering boundaries to avoid any exaggerated claims:

- **Not a** production-grade Mini Program compiler, **does not guarantee** 0 Error compilation in WeChat Developer Tool — `validators.py` is a self-developed static gatekeeper for the Hackathon stage, used to proactively intercept frequent low-level errors, and cannot replace real compilation validation;
- **Incomplete** full WeChat Mini Program launch pipeline, **not implemented** payment / login / cloud development, and explicitly outside the scope of the current stage;
- **No model fine-tuning performed** — time is limited in the current stage, and the ROCm / AMD fine-tuning chain is complex; more importantly, the core bottleneck is not the model's knowledge itself, but rather tool protocols, static validation, grounding, and Demo stability. Fine-tuning is also unsuitable for "remembering specific external facts like image URLs" (this is the core conclusion revealed by the grounding case study: a model's memory of "what a format looks like" is far stronger than its memory of "whether a specific instance truly exists", and the only reliable solution is to strip factual verification from the generation process);
- **Multimodal**: Currently is "uploading images into real project resources + lightweight automatic edge cropping + grounded image selection", **not implemented** a complete "image-to-Mini Program" closed loop or audio/video multimodal;
- Web-side mobile preview is a **low-fidelity simulation** (lightweight WeChat Runtime Shim, covering a subset of common APIs), not official WeChat real-device rendering or Developer Tool compilation results; some generation results can be manually imported into the WeChat Developer Tool for further validation, with production-level compilation, real-device preview, and launch pipeline being the work for the next phase.

---

## Roadmap

- **Short-term**: Polish the stability of reasoning + tool calling + Validator + Grounding components
- **Mid-term**: Accumulate more high-quality Mini Program generation samples, expand cross-industry scenario coverage
- **Long-term**: LoRA / SFT to improve output format stability and domain styles; explore directions like `miniprogram-ci` automated gatekeepers, multi-turn modifications, and commercial template marketplaces

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API Key (choose one)
cp .env.example .env          # Fill in GEMINI_API_KEY
# Or: export GEMINI_API_KEY=your_key_here

# 3. Start real-time generation page (code generator, including full pipeline)
streamlit run app_demo.py --server.port 8505

# 4. Start effect showcase page (quick overview of multiple scenarios, no need to wait for real-time generation)
streamlit run app_showcase.py --server.port 8504
```

Visit `http://localhost:8505` to use the real-time generator; visit `http://localhost:8504` to browse the MiniPilot Agent showcase page.

> The AMD vLLM self-hosted chain is an optional bonus item: automatically enabled after configuring the gateway address and credentials in `E:\file+desktop\gemma_amd_config.txt`; if not configured, the system directly routes to the Google AI Studio main chain, without affecting core functionality availability — this is precisely the embodiment of the dual-backend architecture's "mutual backup" feature.

### Quick Docker Experience

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV GEMINI_API_KEY=your_key_here
CMD ["streamlit", "run", "app_demo.py", "--server.port", "8505", "--server.address", "0.0.0.0"]
```

```bash
docker build -t minipilot-agent .
docker run -p 8505:8505 -e GEMINI_API_KEY=your_key minipilot-agent
```

---

## Directory Structure

```text
app_demo.py                  # Real-time generation page: Input → Generate → Validate → Self-heal → Preview → Download / WeChat Preview
app_showcase.py              # MiniPilot Agent showcase page (quick overview of multiple scenarios, port 8504)
app.py / showcase.py         # Early entry points, retained for backward compatibility with old flows
gemma_client.py              # Gemma 4 dual-backend calling + Native Function Calling + unified Tool Call parsing layer
render_wxml.py               # WXML → HTML renderer + WeChat Runtime Shim (Web-side mobile preview)
validators.py                # Static validation gatekeeper (WXML/WXSS/JS + security checks)
scaffold.py                  # Fixed Mini Program scaffolding (app.json/project.config.json, etc.)
zip_exporter.py              # Merges scaffolding and page trio, packages ZIP
golden_examples.py           # Golden example keyword search fallback (self-healing fallback)
ci_deployer.py               # WeChat official miniprogram-ci CLI integration (optional: scan QR to preview/deploy)
miniprogram_assets.py        # Upload image saving, lightweight edge cropping, asset_list, hero image fallback insertion
assets/library/              # Local industry image asset library; only copies files referenced by the current page during export/preview
gemma_core/
  prompt_builder.py          # Complete Prompt construction for requirement clarification / code generation / self-audit / self-healing (includes image grounding library)
  golden_examples/           # 23 pre-validated scenario corpora
  eval_harness.py            # Offline batch evaluation entry point
docs/
  image_asset_audit_report.md       # Local image assets and historical remote image audit logs
  unsplash_grounding_case_study.md   # Grounding issue troubleshooting case study
tests/                       # Development phase verification scripts (live API testing, parsing unit tests, AMD standard tool_calls verification, etc.)
requirements.txt
.env.example                 # API Key configuration template
```
