# Prompt Enhancement

`PromptEnhancer` rewrites weak prompts into clearer ones **without** calling another LLM.
It is rule-based, deterministic, and safe by default.

## Behavior

| Input characteristic | Behavior |
|---|---|
| Empty | left alone |
| Contains code (` ``` `, `def `, `class `, SQL) | **left alone** |
| Contains legal/medical keywords (NDA, liability, diagnosis, dosage, patient, symptom) | **left alone** |
| Already structured (bullets, "format:", "constraints:", "output:") | left alone |
| Long (> 60 words) | left alone |
| Short and vague | **enhanced** with role + requirements + output format |

The original meaning is always preserved. The enhancer never invents facts.

## Usage

Standalone:

```python
from lumora.enhancement import PromptEnhancer

r = PromptEnhancer().enhance("write email payment")
print(r.changed)              # True
print(r.reason)               # "applied rule-based enhancement for intent='write_email'"
print(r.enhanced_prompt)
```

Via client:

```python
resp = client.chat(
    messages=[{"role": "user", "content": "write email payment"}],
    enhance_prompt=True,      # one-shot; or set enhance_prompt_default=True on the client
)
```

## Intent templates

The enhancer detects one of: `write_email`, `summarize`, `translate`, `explain`,
`plan`, `brainstorm`, `general`. Each maps to a small, safe template that adds
a clear role, requirements, and an output format hint.

## When to turn it off

- You are sending prompts that are already engineered.
- You are passing code, queries, legal/medical text.
- You need byte-perfect prompts (e.g. evals, regression tests).

Just leave `enhance_prompt=False` (the default).
