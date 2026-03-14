"""Meeting summary generation using Claude API.

Alternative to the Ollama backend — sends transcripts to Anthropic's Claude API
for high-quality, context-aware meeting summaries. Supports meeting-type-specific
prompts tailored for yoga classes, business meetings, board meetings, and training
sessions.

Requires: pip install anthropic
API key:  export ANTHROPIC_API_KEY=sk-ant-...
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from meet.languages import MEETING_TYPE_PROMPTS
from meet.summarize import MeetingSummary, _build_system_prompt

# ─── Constants ──────────────────────────────────────────────────────────────

DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"
DEFAULT_CLAUDE_TIMEOUT = 120  # seconds
DEFAULT_CLAUDE_MAX_TOKENS = 4096


# ─── Configuration ──────────────────────────────────────────────────────────

@dataclass
class ClaudeConfig:
    """Configuration for Claude API summarization."""

    api_key: str = ""
    model: str = DEFAULT_CLAUDE_MODEL
    timeout: int = DEFAULT_CLAUDE_TIMEOUT
    temperature: float = 0.3
    max_tokens: int = DEFAULT_CLAUDE_MAX_TOKENS


# ─── Availability check ────────────────────────────────────────────────────

def is_claude_available() -> bool:
    """Check if the Claude API is available (SDK installed + key set)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


# ─── Core summarization ────────────────────────────────────────────────────

def summarize_claude(
    transcript_text: str,
    config: ClaudeConfig | None = None,
    language: str | None = None,
    meeting_type: str = "general",
) -> MeetingSummary:
    """Generate a meeting summary using Claude API.

    Args:
        transcript_text: Plain-text transcript.
        config: Claude configuration. Uses defaults if not provided.
        language: Language code (e.g. "de", "fa"). Affects prompt language.
        meeting_type: One of "general", "class", "business", "board", "training".

    Returns:
        MeetingSummary with markdown, model name, and timing.

    Raises:
        ImportError: If the anthropic package is not installed.
        RuntimeError: If the API call fails.
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "The 'anthropic' package is required for Claude summaries.\n"
            "Install it with: pip install 'meetscribe-offline[claude]'\n"
            "Or directly:     pip install anthropic"
        )

    if config is None:
        config = ClaudeConfig()

    api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "No Anthropic API key found. Set ANTHROPIC_API_KEY environment variable:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-..."
        )

    # Build system prompt: base (language-aware) + meeting-type suffix
    system_prompt = _build_system_prompt(language)
    type_suffix = MEETING_TYPE_PROMPTS.get(meeting_type, "")
    if type_suffix:
        system_prompt += "\n\n" + type_suffix

    # Build user prompt
    from meet.languages import LANG_NAMES as _LANGUAGE_NAMES
    from meet.summarize import USER_PROMPT_TEMPLATE, USER_PROMPT_TEMPLATE_LANG

    if language and language != "en":
        lang_name = _LANGUAGE_NAMES.get(language, language)
        user_prompt = USER_PROMPT_TEMPLATE_LANG.format(
            language=lang_name, transcript=transcript_text,
        )
    else:
        user_prompt = USER_PROMPT_TEMPLATE.format(transcript=transcript_text)

    client = anthropic.Anthropic(api_key=api_key, timeout=config.timeout)
    t0 = time.time()

    try:
        response = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.AuthenticationError:
        raise RuntimeError(
            "Invalid Anthropic API key. Check your ANTHROPIC_API_KEY:\n"
            "  echo $ANTHROPIC_API_KEY"
        )
    except anthropic.RateLimitError:
        raise RuntimeError(
            "Claude API rate limit exceeded. Wait a moment and try again."
        )
    except anthropic.APITimeoutError:
        raise RuntimeError(
            f"Claude API timed out after {config.timeout}s. "
            "Try again or increase the timeout."
        )
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}")

    elapsed = time.time() - t0

    content = ""
    for block in response.content:
        if block.type == "text":
            content += block.text

    if not content.strip():
        raise RuntimeError("Claude returned an empty response.")

    return MeetingSummary(
        markdown=content.strip(),
        model=config.model,
        elapsed_seconds=elapsed,
    )
