"""Rule-based prompt enhancement.

Goal: improve weak, vague prompts before sending them to small or local models,
without distorting meaning and without invoking another expensive LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class EnhancementResult:
    original_prompt: str
    enhanced_prompt: str
    changed: bool
    reason: str


_SENSITIVE_HINTS = re.compile(
    r"```|def\s+\w+\(|class\s+\w+|select\s+.+\s+from|"
    r"\b(legal|contract|nda|liability|diagnos|prescription|dosage|patient|symptom)\b",
    re.IGNORECASE,
)


class PromptEnhancer:
    """Lightweight heuristic enhancer. Safe defaults, no LLM calls."""

    def __init__(
        self,
        min_words: int = 8,
        max_words_for_enhancement: int = 60,
    ) -> None:
        self.min_words = min_words
        self.max_words_for_enhancement = max_words_for_enhancement

    def enhance(self, prompt: str) -> EnhancementResult:
        original = prompt or ""
        stripped = original.strip()

        if not stripped:
            return EnhancementResult(original, original, False, "empty prompt; nothing to enhance")

        if _SENSITIVE_HINTS.search(stripped):
            return EnhancementResult(
                original,
                original,
                False,
                "sensitive content detected (code/legal/medical); leaving prompt untouched",
            )

        word_count = len(stripped.split())
        if word_count > self.max_words_for_enhancement:
            return EnhancementResult(
                original,
                original,
                False,
                "prompt already detailed; skipping enhancement",
            )

        if word_count >= self.min_words and self._looks_structured(stripped):
            return EnhancementResult(
                original,
                original,
                False,
                "prompt already structured; skipping enhancement",
            )

        intent = self._guess_intent(stripped)
        enhanced = self._wrap(stripped, intent)
        return EnhancementResult(
            original,
            enhanced,
            True,
            f"applied rule-based enhancement for intent='{intent}'",
        )

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _looks_structured(text: str) -> bool:
        markers = ["- ", "* ", "1.", "2.", "format:", "constraints:", "output:", "tone:"]
        lower = text.lower()
        return sum(1 for m in markers if m in lower) >= 2

    @staticmethod
    def _guess_intent(text: str) -> str:
        t = text.lower()
        if any(k in t for k in ("email", "message", "letter", "reply")):
            return "write_email"
        if any(k in t for k in ("summari", "tl;dr", "summary")):
            return "summarize"
        if any(k in t for k in ("translate", "translation")):
            return "translate"
        if any(k in t for k in ("explain", "what is", "how does", "why does")):
            return "explain"
        if any(k in t for k in ("plan", "checklist", "steps to")):
            return "plan"
        if any(k in t for k in ("idea", "brainstorm", "suggest")):
            return "brainstorm"
        return "general"

    @staticmethod
    def _wrap(prompt: str, intent: str) -> str:
        templates = {
            "write_email": (
                "You are a professional writing assistant.\n"
                "Task: {p}\n"
                "Requirements:\n"
                "- Write a clear, polite, concise email.\n"
                "- Include a short subject line and a short body.\n"
                "- Keep a respectful tone; avoid sounding aggressive.\n"
                "Output format: 'Subject: ...' on the first line, then the email body."
            ),
            "summarize": (
                "You are a concise summarization assistant.\n"
                "Task: {p}\n"
                "Requirements:\n"
                "- Capture the key points faithfully.\n"
                "- Prefer short paragraphs or 3-7 bullet points.\n"
                "- Do not add information that is not present in the source."
            ),
            "translate": (
                "You are a precise translation assistant.\n"
                "Task: {p}\n"
                "Requirements:\n"
                "- Preserve meaning, tone, and named entities.\n"
                "- Do not add commentary; output only the translation."
            ),
            "explain": (
                "You are a clear technical explainer.\n"
                "Task: {p}\n"
                "Requirements:\n"
                "- Use simple language and a short example.\n"
                "- Keep it under ~200 words unless more is clearly needed."
            ),
            "plan": (
                "You are a pragmatic planning assistant.\n"
                "Task: {p}\n"
                "Requirements:\n"
                "- Produce an ordered checklist of concrete steps.\n"
                "- Each step should be actionable in one sitting."
            ),
            "brainstorm": (
                "You are a creative brainstorming partner.\n"
                "Task: {p}\n"
                "Requirements:\n"
                "- Produce 5-8 diverse, concrete ideas.\n"
                "- One short line per idea."
            ),
            "general": (
                "You are a helpful, careful assistant.\n"
                "Task: {p}\n"
                "Requirements:\n"
                "- Be clear, structured, and concise.\n"
                "- If the request is ambiguous, state the assumption you made.\n"
                "- Preserve the original intent of the user."
            ),
        }
        return templates[intent].format(p=prompt.strip())
