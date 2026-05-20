"""Unit tests for StateManager, testing locked reads, writes, and stale session recovery."""
from __future__ import annotations
import json
import time
from pathlib import Path
from zero_g.core.state_manager import StateManager

def test_state_manager_write_and_read(tmp_path: Path):
    manager = StateManager(base_dir=tmp_path)
    state = {
        "current_stage": "planning",
        "task_id": "test_123",
        "step_history": ["Started"]
    }
    
    manager.write(state)
    
    # Read and assert fields
    read_state = manager.read()
    assert read_state["current_stage"] == "planning"
    assert read_state["task_id"] == "test_123"
    assert read_state["step_history"] == ["Started"]
    assert "_updated_at" in read_state

def test_state_manager_default_state(tmp_path: Path):
    manager = StateManager(base_dir=tmp_path)
    # File doesn't exist yet, should return default state
    state = manager.read()
    assert state["current_stage"] == "initialized"
    assert state["task_id"] is None
    assert state["step_history"] == []

def test_state_manager_clear(tmp_path: Path):
    manager = StateManager(base_dir=tmp_path)
    state = {"current_stage": "execution", "task_id": "xyz"}
    manager.write(state)
    
    manager.clear()
    cleared = manager.read()
    assert cleared["current_stage"] == "initialized"
    assert cleared["task_id"] is None

def test_state_manager_is_active(tmp_path: Path):
    manager = StateManager(base_dir=tmp_path)
    assert not manager.is_active()
    
    # Active stage
    manager.write({"current_stage": "execution"})
    assert manager.is_active()
    
    # Inactive stages
    manager.write({"current_stage": "completed"})
    assert not manager.is_active()
    
    manager.write({"current_stage": "failed"})
    assert not manager.is_active()

def test_state_manager_cleanup_stale(tmp_path: Path, monkeypatch):
    manager = StateManager(base_dir=tmp_path)
    manager.write({"current_stage": "execution"})
    
    # Initially active
    assert manager.is_active()
    assert not manager.cleanup_stale()
    
    # Mock age_hours check to look stale (> 24 hours) by modifying file mtime
    state_file = manager.get_state_file()
    stale_mtime = time.time() - 25 * 3600
    import os
    os.utime(state_file, (stale_mtime, stale_mtime))
    
    # Should now detect stale active state and clean it up
    assert not manager.is_active()
    assert manager.cleanup_stale()
    
    cleaned = manager.read()
    assert cleaned["current_stage"] == "failed"
    assert cleaned["_stale_cleanup"] is True
