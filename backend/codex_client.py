"""
codex_client.py — Codex CLI integration for PursuitIQ.

Uses the Codex CLI (from VS Code extension) to run GPT-5 inference via
ChatGPT subscription — zero API cost. Falls back to OpenAI API if Codex
is unavailable.

Codex exec mode:
  - Non-interactive, returns JSONL events
  - Uses ChatGPT auth (no API key needed)
  - GPT-5 model (higher capability than API's gpt-5.5 for long-form writing)
  - Stream mode prints live output to terminal (great for demos)
"""

import json
import logging
import os
import subprocess
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Set CODEX_STREAM=1 in .env or environment to see live Codex output in terminal
STREAM_ENABLED = os.getenv("CODEX_STREAM", "0") == "1"


def _find_codex() -> Path | None:
    """Locate the Codex CLI binary — prefers global npm install."""
    found = shutil.which("codex")
    if found:
        return Path(found)
    # Fallback: VS Code extension bundled binary
    vscode_path = Path(
        r"C:\Users\jay-vm\.vscode\extensions\openai.chatgpt-26.623.101652-win32-x64"
        r"\bin\windows-x86_64\codex.exe"
    )
    if vscode_path.exists():
        return vscode_path
    return None


def run_codex(prompt: str, timeout: int = 180) -> str | None:
    """
    Run a prompt through Codex CLI in non-interactive mode.

    If CODEX_STREAM=1, prints live output to terminal as GPT-5 generates it.
    Returns the agent's text response, or None if Codex is unavailable/fails.
    """
    codex = _find_codex()
    if not codex:
        logger.warning("Codex CLI not found — falling back to API")
        return None

    # Use stdin ("-") to pass prompt — avoids Windows 8191-char CLI arg limit
    cmd = [
        str(codex), "exec",
        "--json",
        "--ephemeral",
        "-s", "read-only",
        "-",  # read prompt from stdin
    ]

    if STREAM_ENABLED:
        return _run_streaming(cmd, timeout, prompt)
    else:
        return _run_batch(cmd, timeout, prompt)


def _run_batch(cmd: list, timeout: int, prompt: str = "") -> str | None:
    """Run Codex and collect output at the end (silent mode)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=prompt,
            encoding="utf-8",
            errors="replace",
        )

        messages = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                event = json.loads(line)
                if (event.get("type") == "item.completed"
                        and event.get("item", {}).get("type") == "agent_message"):
                    messages.append(event["item"]["text"])
            except json.JSONDecodeError:
                continue

        if not messages:
            stderr_snippet = result.stderr[:200] if result.stderr else ""
            logger.warning(f"Codex returned no messages. stderr: {stderr_snippet}")
            return None

        full_response = "\n".join(messages)
        logger.info(f"Codex response: {len(full_response):,} chars")
        return full_response

    except subprocess.TimeoutExpired:
        logger.warning(f"Codex timed out after {timeout}s")
        return None
    except Exception as e:
        logger.warning(f"Codex execution failed: {e}")
        return None


def _run_streaming(cmd: list, timeout: int, prompt: str = "") -> str | None:
    """Run Codex and stream output live to terminal (demo mode)."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        proc.stdin.write(prompt)
        proc.stdin.close()

        print("\n" + "=" * 70)
        print("  CODEX (GPT-5) -- Generating Proposal Draft LIVE")
        print("=" * 70 + "\n")

        messages = []
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                event_type = event.get("type")

                if event_type == "turn.started":
                    print("  [GPT-5 thinking...]\n")

                elif (event_type == "item.completed"
                      and event.get("item", {}).get("type") == "agent_message"):
                    text = event["item"]["text"]
                    messages.append(text)
                    # Print live — show first 500 chars of each message chunk
                    preview = text[:500]
                    print(f"  {preview}")
                    if len(text) > 500:
                        print(f"  [...{len(text) - 500} more chars...]")
                    print()

                elif event_type == "turn.completed":
                    usage = event.get("usage", {})
                    print(f"  [Done — {usage.get('output_tokens', '?')} tokens generated]")

            except json.JSONDecodeError:
                continue

        proc.wait(timeout=timeout)
        print("\n" + "=" * 70 + "\n")

        if not messages:
            logger.warning("Codex streaming returned no messages")
            return None

        full_response = "\n".join(messages)
        logger.info(f"Codex response (streamed): {len(full_response):,} chars")
        return full_response

    except subprocess.TimeoutExpired:
        proc.kill()
        logger.warning(f"Codex timed out after {timeout}s")
        return None
    except Exception as e:
        logger.warning(f"Codex streaming failed: {e}")
        return None


def is_codex_available() -> bool:
    """Check if Codex CLI is installed and authenticated."""
    codex = _find_codex()
    if not codex:
        return False
    try:
        result = subprocess.run(
            [str(codex), "exec", "--json", "--ephemeral", "-s", "read-only", "-"],
            capture_output=True,
            text=True,
            timeout=30,
            input="Reply: OK",
            encoding="utf-8",
            errors="replace",
        )
        return "agent_message" in result.stdout
    except Exception:
        return False
