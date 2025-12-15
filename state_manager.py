"""
State Manager for RAG Pipeline

This module handles the state management for the RAG ingestion pipeline.
It ensures idempotency by tracking which files have already been processed 
using SHA-256 hashing.

It prevents the RAG pipeline from re-ingesting documents that have 
already been vectorized, saving API costs and processing time.

Features:
- **Idempotency:** Uses SHA-256 hashing to uniquely identify file content.
- **Persistence:** Maintains a lightweight JSON database of processed files.
- **Resilience:** Automatically handles missing or corrupted state files 
  by resetting to a safe empty state.

Usage:
    from state_manager import StateManager, compute_file_hash
    
    manager = StateManager()
    file_hash = compute_file_hash("data/document.pdf")
    
    if not manager.is_processed(file_hash):
        # ... process file ...
        manager.add_processed(file_hash, "document.pdf")
"""

import hashlib
import json
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StateManager:
    """
    Manages the persistence layer for tracking processed files.
    
    Attributes:
        state_file (str): Absolute path to the JSON state file.
        state (dict): In-memory cache of processed file hashes.
    """
    state_file: str
    state: dict[str, str]
    
    def __init__(self, state_file: str="state.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.state_file = os.path.join(base_dir, state_file)
        
        self.state = self._load_state()
        
    def _load_state(self) -> dict[str, str]:
        """Loads state from disk, handling missing or corrupted files gracefully."""
        if not os.path.exists(self.state_file):
            logger.info(f"No state file found at {self.state_file}. Starting new state file.")
            return {}
        
        try:
            if os.path.getsize(self.state_file) == 0:
                logger.warning(f"State file {self.state_file} is empty. Resetting state.")
                return {}
            
            with open(self.state_file, "r") as f:
                return json.load(f)
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load state file: {e}. Defaulting to empty state.")
            return {}
    
    def is_processed(self, file_hash: str) -> bool:
        """Checks if a file hash exists in the state."""
        return file_hash in self.state
    
    def add_processed(self, file_hash: str, filename: str) -> None:
        """Updates the state and persists it to disk immediately."""
        self.state[file_hash] = filename
        try:
            with open(self.state_file, "w") as json_file:
                json.dump(self.state, json_file, indent=4)
            logger.info(f"Successfully tracked: {filename}")
        except IOError as e:
            logger.error(f"Failed to save state to state file: {e}")

def compute_file_hash(input_file_path: str, algo: str="sha256", chunk_size: int=4096) -> str | None:
    """Computes the SHA-256 hash of a file efficiently by reading in chunks."""
    hasher = hashlib.new(algo)
    try:
        with open(input_file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    except FileNotFoundError:
        logger.error(f"File not found: {input_file_path}")
        return None
    except ValueError:
        logger.error(f"Unsupported hash algorithm: {algo}")
        return None

def main():
    test_file_path = "./data/ghost.txt"
    # This will likely fail if ghost.txt doesn't exist, which is expected behavior.
    hashed_file = compute_file_hash(test_file_path,"sha256",4096)
    
    if not hashed_file:
        logger.error("Failed to hash file. Exiting.")
        return
    
    manager = StateManager()
    
    if manager.is_processed(hashed_file):
        logger.info(f"File was already processed: {test_file_path}")
    else:
        logger.info(f"New file detected, adding {test_file_path} to state file...")
        manager.add_processed(hashed_file, "test.txt")

if __name__ == "__main__":
    main()