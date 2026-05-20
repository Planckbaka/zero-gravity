"""Extracts JSON from LLM response texts, supporting markdown blocks and correcting syntax anomalies like trailing commas."""
from __future__ import annotations
import json
import re


def extract_json(text: str) -> list | dict:
    """
    Extract and parse JSON from the given text.

    Supports:
    - Raw JSON strings.
    - Markdown-wrapped JSON (e.g. ```json ... ```).
    - Extraneous explanation text prefix or suffix.
    - Trailing commas inside JSON objects/arrays.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Regex search for Markdown fence blocks
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        content = fence_match.group(1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    # Strategy: Find first '{' or '[' and last '}' or ']' (outermost candidate wins)
    best_candidate = None
    earliest_idx = len(text)
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = text.find(start_char)
        end_idx = text.rfind(end_char)
        if start_idx != -1 and end_idx > start_idx:
            if start_idx < earliest_idx:
                candidate = text[start_idx:end_idx + 1]
                # Strip trailing commas inside object/array brackets
                candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
                try:
                    best_candidate = json.loads(candidate)
                    earliest_idx = start_idx
                except json.JSONDecodeError:
                    pass
    if best_candidate is not None:
        return best_candidate

    raise ValueError(f"Could not extract valid JSON from LLM output: {text[:200]}...")


def extract_json_with_retry(extract_fn, text: str, max_retries: int = 2) -> list | dict:
    """
    Attempt to extract JSON, retrying via the callable `extract_fn` if it fails.
    """
    for attempt in range(max_retries + 1):
        try:
            return extract_json(text)
        except ValueError:
            if attempt < max_retries:
                text = extract_fn("Your previous output was not valid JSON. Output ONLY valid JSON, no other text.")
            else:
                raise
