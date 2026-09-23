"""Keep .env.example aligned with docs/configuration.md (#78)."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Mentioned in the configuration guide but not application .env keys:
# CI publish secrets and a Python symbol in tests/eval/dataset.py.
DOC_KEYS_NOT_APP_ENV = {
    "DOCKERHUB_USERNAME",
    "DOCKERHUB_TOKEN",
    "KNOWN_LIMITATION_PAIRS",
}


def _env_example_keys(text: str) -> set[str]:
    return set(re.findall(r"^[ \t]*#?[ \t]*([A-Z][A-Z0-9_]+)=", text, re.M))


def _documented_env_keys(text: str) -> set[str]:
    return {
        key
        for key in re.findall(r"`([A-Z][A-Z0-9_]+)`", text)
        if key not in DOC_KEYS_NOT_APP_ENV
    }


def test_env_example_has_no_inline_comments_on_value_lines():
    for i, line in enumerate((ROOT / ".env.example").read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        assert "#" not in line, (
            f".env.example:{i} has an inline comment on a value line: {line!r}"
        )


def test_documented_configuration_vars_appear_in_env_example():
    env_keys = _env_example_keys((ROOT / ".env.example").read_text(encoding="utf-8"))
    doc_keys = _documented_env_keys(
        (ROOT / "docs" / "configuration.md").read_text(encoding="utf-8")
    )
    missing = sorted(doc_keys - env_keys)
    assert not missing, (
        "docs/configuration.md documents env vars missing from .env.example: "
        + ", ".join(missing)
    )


def test_mongo_uri_notes_that_setting_it_disables_bundled_db():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert re.search(r"^[ \t]*#?[ \t]*MONGO_URI=", text, re.M)
    assert "disables the bundled database" in text


def test_optional_documented_knobs_are_commented_out():
    """Optional knobs must not be set to empty values that override defaults."""
    optional = [
        "APP_ENV",
        "APP_IMAGE",
        "COVERAGE_REVIEW_THRESHOLD",
        "MINDMAP_BATCH_SIZE",
        "MINDMAP_EXCERPT_PER_CHARS",
        "MINDMAP_EXCERPT_TOTAL_CHARS",
        "MINDMAP_EXCERPT_TOTAL_CHARS_HOSTED",
        "MINDMAP_MAX_WINDOWS",
        "MINDMAP_REVIEW_MAX_TOKENS",
        "MINDMAP_SAMPLES",
        "NUMPY_FALLBACK_MAX_DOCS",
        "MONGO_URI",
        "SESSION_SECRET",
        "ENCRYPTION_KEY",
        "OLLAMA_MAX_NUM_CTX",
        "WARDENIQ_REUSE_SIM_API",
        "WARDENIQ_REUSE_SIM_GENERAL",
    ]
    lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    assignments = {}
    for line in lines:
        match = re.match(r"^([ \t]*#?[ \t]*)([A-Z][A-Z0-9_]+)=(.*)$", line)
        if match:
            assignments[match.group(2)] = line
    for key in optional:
        assert key in assignments, f"{key} missing from .env.example"
        assert assignments[key].lstrip().startswith("#"), (
            f"{key} should be commented out as an optional override: {assignments[key]!r}"
        )
