"""Unit tests for JSON extraction and recovery utility functions."""
from __future__ import annotations
import pytest
from zero_g.core.json_utils import extract_json, extract_json_with_retry

def test_extract_json_clean():
    clean_json = '{"name": "zero-gravity", "active": true}'
    result = extract_json(clean_json)
    assert result == {"name": "zero-gravity", "active": True}

def test_extract_json_markdown():
    markdown_json = "Here is the response:\n```json\n{\n  \"status\": \"success\",\n  \"code\": 200\n}\n```\nAnd some extra text."
    result = extract_json(markdown_json)
    assert result == {"status": "success", "code": 200}

def test_extract_json_surrounding_text():
    raw_text = "Some text before {\"value\": 42} and text after."
    result = extract_json(raw_text)
    assert result == {"value": 42}

def test_extract_json_trailing_comma():
    malformed_comma = '{\n  "list": [1, 2, 3,],\n  "nested": {"a": 1,},\n}'
    result = extract_json(malformed_comma)
    assert result == {"list": [1, 2, 3], "nested": {"a": 1}}

def test_extract_json_invalid():
    with pytest.raises(ValueError):
        extract_json("This is purely arbitrary text without brackets.")

def test_extract_json_with_retry_success():
    attempt = 0
    def mock_extract_fn(prompt):
        nonlocal attempt
        attempt += 1
        return '{"correct": true}'
        
    # Fails first, then calls extract_fn
    res = extract_json_with_retry(mock_extract_fn, "garbage-text", max_retries=2)
    assert res == {"correct": True}
    assert attempt == 1

def test_extract_json_with_retry_failure():
    def mock_extract_fn(prompt):
        return "still-garbage"
        
    with pytest.raises(ValueError):
        extract_json_with_retry(mock_extract_fn, "garbage-text", max_retries=2)
