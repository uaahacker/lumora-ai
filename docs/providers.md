# Providers

LumoraAI talks to model providers through small adapters. Today there are two:

| Type | Adapter | Works with |
|---|---|---|
| `openai_compatible` | `OpenAICompatibleProvider` | OpenAI, OpenRouter, vLLM, LM Studio, Together-like, any OpenAI-compatible endpoint |
| `ollama` | `OllamaProvider` | Local Ollama (`http://localhost:11434`) |

A future `anthropic` adapter is planned. The interface is already designed for it (`BaseProvider`).

## Provider config schema

```python
{
    "name":          "openrouter",          # any unique label
    "type":          "openai_compatible",   # or "ollama"
    "base_url":      "https://openrouter.ai/api/v1",
    "api_key":       "sk-or-...",           # OR use api_key_env
    "api_key_env":   "OPENROUTER_API_KEY",  # reads from env at runtime
    "models": {
        "cheap":    "openai/gpt-4o-mini",
        "balanced": "openai/gpt-4o",
        "smart":    "anthropic/claude-3.5-sonnet",
    },
    "timeout":       60.0,
    "extra_headers": {"HTTP-Referer": "https://your-app.example"},
}
```

You can configure **multiple providers** in one client; the router will pick.

## OpenRouter

```python
{
    "name": "openrouter",
    "type": "openai_compatible",
    "base_url": "https://openrouter.ai/api/v1",
    "api_key_env": "OPENROUTER_API_KEY",
    "models": {
        "cheap":    "openai/gpt-4o-mini",
        "balanced": "openai/gpt-4o",
        "smart":    "anthropic/claude-3.5-sonnet",
    },
}
```

## OpenAI (direct)

```python
{
    "name": "openai",
    "type": "openai_compatible",
    "base_url": "https://api.openai.com/v1",
    "api_key_env": "OPENAI_API_KEY",
    "models": {"cheap": "gpt-4o-mini", "balanced": "gpt-4o", "smart": "gpt-4o"},
}
```

## Ollama (local)

```python
{
    "name": "local",
    "type": "ollama",
    "base_url": "http://localhost:11434",
    "models": {"cheap": "ollama/llama3.1", "balanced": "ollama/llama3.1"},
}
```

Make sure Ollama is running and the model is pulled:

```bash
ollama pull llama3.1
ollama serve   # usually auto-starts
```

## vLLM / LM Studio / Together-like

Any service that speaks the OpenAI `/chat/completions` schema works.
Set `type: "openai_compatible"` and point `base_url` at it.

```python
{
    "name": "vllm",
    "type": "openai_compatible",
    "base_url": "http://localhost:8000/v1",
    "api_key": "EMPTY",
    "models": {"balanced": "meta-llama/Meta-Llama-3.1-8B-Instruct"},
}
```

## Adding a new provider

1. Subclass `lumora.providers.BaseProvider`.
2. Implement `chat(messages, model, temperature, max_tokens, timeout) -> ProviderChatResult`.
3. Register it in `lumora.providers.build_provider`.

See `lumora/providers/ollama.py` for a 60-line reference.
