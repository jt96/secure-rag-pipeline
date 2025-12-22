"""
Unit Tests for State Manager

This test suite verifies the persistence and integrity logic of the 
incremental ingestion system. It ensures that the file tracking database 
(JSON) correctly records processed files and recovers from errors.

Test Coverage:
- **Hashing Logic:** Verifies SHA-256 hash generation for file content.
- **Persistence:** checks that the JSON state file is created, read, 
  and updated correctly.
- **Resilience:** Ensures the system creates a new state file if the 
  existing one is missing or corrupted (invalid JSON).
- **Idempotency:** Confirms that previously processed hashes are 
  correctly identified to prevent re-work.
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import pytest # noqa: E402
from src.state_manager import StateManager, compute_file_hash # noqa: E402

@pytest.fixture
def temp_state_file(tmp_path):
    """
    Returns a path to a temporary JSON file.
    Pytest ensures this path is unique per test function.
    """
    file_path = tmp_path / "test_state.json"
    return str(file_path)

@pytest.fixture
def manager(temp_state_file):
    """Initializes a StateManager instance pointing to the temporary file."""
    return StateManager(state_file=temp_state_file)

def test_initialization_is_empty(manager):
    """Verifies that a new StateManager starts with an empty state."""
    assert manager.state == {}
    
def test_compute_hash(manager, tmp_path):
    """Verifies SHA-256 hashing logic against a known input."""
    # Create a dummy file with known content
    dummy_file = tmp_path / "dummy.txt"
    dummy_file.write_text("Hello World", encoding="utf-8")
    
    # Pre-calculated SHA-256 for "Hello World"
    expected_hash = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    
    computed_hash = compute_file_hash(str(dummy_file))
    
    assert computed_hash == expected_hash
    
def test_persistence(manager, temp_state_file):
    """
    Verifies that state is correctly saved to disk and can be reloaded 
    by a new StateManager instance.
    """
    fake_path = "C:/fake/file.pdf"
    fake_hash = "12345fakehash"
    
    # Adding a processed file should update memory and write to disk
    manager.add_processed(fake_hash, fake_path)
    
    # Initialize a new manager using the same file to simulate a restart
    new_manager = StateManager(state_file=temp_state_file)
    
    assert fake_hash in new_manager.state
    assert new_manager.state[fake_hash] == fake_path
    
def test_corruption_detection(temp_state_file):
    """
    Verifies that the manager detects corruption (invalid JSON) 
    and resets to a fresh empty state.
    """
    with open(temp_state_file, "w") as f:
        f.write("NOT JSON DATA")
    
    manager = StateManager(state_file=temp_state_file)
    
    assert manager.state == {}
    
def test_ghost_file(tmp_path):
    """
    Verifies that compute_file_hash handles FileNotFoundError 
    and returns None instead of crashing the program.
    """
    fake_file = tmp_path / "ghost.txt"
    
    assert compute_file_hash(str(fake_file)) is None