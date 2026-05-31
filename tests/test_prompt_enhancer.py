from lumora.enhancement import PromptEnhancer


def test_short_vague_prompt_is_enhanced():
    e = PromptEnhancer()
    r = e.enhance("write email payment")
    assert r.changed is True
    assert "professional" in r.enhanced_prompt.lower()
    assert "subject" in r.enhanced_prompt.lower()


def test_empty_prompt_not_enhanced():
    r = PromptEnhancer().enhance("")
    assert r.changed is False


def test_code_prompt_left_alone():
    code = "```python\ndef foo():\n    return 1\n```\nplease optimize"
    r = PromptEnhancer().enhance(code)
    assert r.changed is False


def test_legal_prompt_left_alone():
    r = PromptEnhancer().enhance("draft an nda for liability")
    assert r.changed is False


def test_long_detailed_prompt_left_alone():
    long_prompt = " ".join(["word"] * 80)
    r = PromptEnhancer().enhance(long_prompt)
    assert r.changed is False
