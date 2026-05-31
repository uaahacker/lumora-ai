"""Demonstrates the rule-based prompt enhancer in isolation (no network)."""

from __future__ import annotations

from lumora.enhancement import PromptEnhancer


PROMPTS = [
    "write email payment",
    "summarize this article please",
    "translate hi to spanish",
    "explain transformers",
    "```python\ndef add(a,b): return a+b\n```\nspeed up",  # left alone
    "draft an nda about liability",                         # left alone
]


def main() -> None:
    e = PromptEnhancer()
    for p in PROMPTS:
        r = e.enhance(p)
        print("=" * 70)
        print(f"INPUT   : {p!r}")
        print(f"CHANGED : {r.changed}")
        print(f"REASON  : {r.reason}")
        if r.changed:
            print("ENHANCED:")
            print(r.enhanced_prompt)


if __name__ == "__main__":
    main()
