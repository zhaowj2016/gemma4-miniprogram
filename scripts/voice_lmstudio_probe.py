from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import wave
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1"
DEFAULT_MODEL = "gemma-4-e4b-it"
DEFAULT_TEXT = (
    "我想做一个 AI 婚礼影像工作室的小程序，"
    "需要作品集展示，套餐预约，AI 修图服务，客户案例，"
    "整体风格要高级黑金，适合高端婚礼客户。"
)


def http_json(method: str, url: str, payload: dict | None = None, timeout: int = 120) -> dict:
    # LM Studio builds on local runtimes that can be surprisingly sensitive to
    # raw non-ASCII request bodies. ASCII-escaped JSON keeps Chinese prompts
    # intact across the OpenAI-compatible and native REST endpoints.
    data = None if payload is None else json.dumps(payload, ensure_ascii=True).encode("utf-8")
    req = Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot reach {url}: {exc.reason}") from exc


def synthesize_windows_tts(text: str, out_wav: Path) -> None:
    """Generate a deterministic local Chinese speech sample using Windows SAPI."""
    escaped = text.replace("'", "''")
    script = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voice = $s.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Culture.Name -eq 'zh-CN' }} | Select-Object -First 1
if ($voice) {{ $s.SelectVoice($voice.VoiceInfo.Name) }}
$s.Rate = 0
$s.Volume = 100
$s.SetOutputToWaveFile('{str(out_wav).replace("'", "''")}')
$s.Speak('{escaped}')
$s.Dispose()
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        check=True,
        capture_output=True,
        text=True,
    )


def wav_info(path: Path) -> dict:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return {
            "channels": wf.getnchannels(),
            "sample_rate": rate,
            "sample_width": wf.getsampwidth(),
            "frames": frames,
            "duration_sec": round(frames / float(rate), 2),
        }


def extract_text(response: dict) -> str:
    try:
        msg = response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return json.dumps(response, ensure_ascii=False, indent=2)
    content = msg.get("content")
    if isinstance(content, str):
        return content.strip()
    return json.dumps(content, ensure_ascii=False, indent=2)


def list_models(base_url: str) -> list[str]:
    data = http_json("GET", f"{base_url.rstrip('/')}/models", timeout=8)
    return [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]


def chat(base_url: str, payload: dict, timeout: int) -> tuple[str, float, dict]:
    started = time.perf_counter()
    data = http_json("POST", f"{base_url.rstrip('/')}/chat/completions", payload, timeout=timeout)
    elapsed = time.perf_counter() - started
    return extract_text(data), elapsed, data


def audio_payloads(model: str, audio_path: Path) -> list[tuple[str, dict]]:
    audio_b64 = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    prompt = (
        "Transcribe the following speech segment in its original language into text. "
        "Only output the transcription, with no newlines."
    )
    return [
        (
            "openai_input_audio",
            {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "input_audio",
                                "input_audio": {"data": audio_b64, "format": "wav"},
                            },
                        ],
                    }
                ],
                "temperature": 0,
                "max_tokens": 256,
            },
        ),
        (
            "audio_data_url",
            {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "audio",
                                "audio": f"data:audio/wav;base64,{audio_b64}",
                            },
                        ],
                    }
                ],
                "temperature": 0,
                "max_tokens": 256,
            },
        ),
    ]


def structure_need(base_url: str, model: str, transcript: str, timeout: int) -> tuple[str, float]:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是 Gemma Match 的语音需求整理器。把口语转写整理成可生成微信小程序的需求，"
                    "只输出简洁中文，不要编造没有出现的核心事实。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请把下面的语音转写整理为：行业、核心功能、视觉风格、生成目标、可直接用于生成的需求句。\n\n"
                    f"转写：{transcript}"
                ),
            },
        ],
        "temperature": 0.1,
        "max_tokens": 512,
    }
    text, elapsed, _ = chat(base_url, payload, timeout)
    return text, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe local LM Studio Gemma audio ASR loop.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--make-sample", action="store_true")
    parser.add_argument("--sample-text", default=DEFAULT_TEXT)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    out_dir = Path("dev_artifacts") / "voice_probe"
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_path = args.audio or out_dir / "sample_zh_wedding.wav"

    if args.make_sample or not audio_path.exists():
        synthesize_windows_tts(args.sample_text, audio_path)

    print(f"[audio] {audio_path}")
    print(f"[audio_info] {json.dumps(wav_info(audio_path), ensure_ascii=False)}")

    try:
        models = list_models(args.base_url)
    except RuntimeError as exc:
        print(f"[server] not reachable: {exc}")
        print("[next] Start LM Studio Developer Server, then rerun this command:")
        print(
            f"python scripts/voice_lmstudio_probe.py --make-sample --base-url {args.base_url} --model {args.model}"
        )
        return 2

    print(f"[models] {models or '(no loaded models returned)'}")
    model = args.model
    if models and model not in models:
        model = models[0]
        print(f"[model] requested model not listed; using loaded model: {model}")

    transcript = ""
    audio_errors: list[str] = []
    for name, payload in audio_payloads(model, audio_path):
        print(f"[asr] trying {name}...")
        try:
            transcript, elapsed, _ = chat(args.base_url, payload, args.timeout)
            print(f"[asr:{name}] elapsed={elapsed:.2f}s")
            print(f"[transcript] {transcript}")
            if transcript and "audio" not in transcript.lower()[:120]:
                break
        except RuntimeError as exc:
            audio_errors.append(f"{name}: {exc}")
            print(f"[asr:{name}] failed: {exc}")

    if not transcript:
        print("[asr] all audio request formats failed.")
        for err in audio_errors:
            print(f"  - {err}")
        return 3

    print("[structure] organizing transcript for Gemma Match...")
    structured, elapsed = structure_need(args.base_url, model, transcript, args.timeout)
    print(f"[structure] elapsed={elapsed:.2f}s")
    print(structured)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
