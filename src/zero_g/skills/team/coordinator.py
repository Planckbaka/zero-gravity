"""Team coordinator: file-lock-based partition management for parallel workers.

Prevents race conditions when multiple L1 Agents modify files concurrently.
Workers claim exclusive file partitions and release them on completion.
"""
from __future__ import annotations
import json
import fcntl
from pathlib import Path


class TeamCoordinator:
    """Coordinates file access for parallel workers."""

    def __init__(self, team_name: str, base_dir: Path | None = None):
        self.coord_dir = (base_dir or Path(".zg/coord")) / team_name
        self.coord_dir.mkdir(parents=True, exist_ok=True)

    def _lock_file(self) -> Path:
        return self.coord_dir / "partitions.json"

    def claim_partition(self, worker_id: str, files: list[str]) -> bool:
        """Worker claims exclusive access to a set of files.

        Returns False if any file is already claimed by another worker.
        """
        lock_file = self._lock_file()
        with open(lock_file, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.seek(0)
                content = f.read()
                partitions = json.loads(content) if content else {}

                # Check for conflicts
                for claimed_file in files:
                    current_owner = partitions.get(claimed_file)
                    if current_owner and current_owner != worker_id:
                        return False

                # Claim ownership
                for file_path in files:
                    partitions[file_path] = worker_id

                f.seek(0)
                f.truncate()
                json.dump(partitions, f, indent=2)
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

        return True

    def release_partition(self, worker_id: str) -> None:
        """Release all files claimed by a worker."""
        lock_file = self._lock_file()
        if not lock_file.exists():
            return

        with open(lock_file, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                content = f.read()
                partitions = json.loads(content) if content else {}
                partitions = {k: v for k, v in partitions.items() if v != worker_id}
                f.seek(0)
                f.truncate()
                json.dump(partitions, f, indent=2)
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def get_partitions(self) -> dict[str, str]:
        """Return current partition map (file -> worker_id)."""
        lock_file = self._lock_file()
        if not lock_file.exists():
            return {}
        with open(lock_file, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                content = f.read()
                return json.loads(content) if content else {}
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def clear(self) -> None:
        """Remove all partition data."""
        lock_file = self._lock_file()
        if lock_file.exists():
            lock_file.unlink()
