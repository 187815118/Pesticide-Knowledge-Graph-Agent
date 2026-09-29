import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Optional

from agent.agent_harness import AgentState


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "agent_checkpoints.sqlite3"


class CheckpointStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or os.environ.get("AGENT_CHECKPOINT_DB") or DEFAULT_DB_PATH)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._memory_connection = sqlite3.connect(self.db_path, check_same_thread=False) if self.db_path == ":memory:" else None
        self._initialize()

    def _connect(self):
        return self._memory_connection or sqlite3.connect(self.db_path, timeout=30)

    def _initialize(self) -> None:
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS agent_checkpoints (
                        task_id TEXT PRIMARY KEY,
                        original_query TEXT NOT NULL,
                        current_query TEXT NOT NULL,
                        state_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        step_count INTEGER NOT NULL,
                        final_answer TEXT NOT NULL,
                        version INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                connection.commit()
            finally:
                if connection is not self._memory_connection:
                    connection.close()

    def save(self, state: AgentState) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            connection = self._connect()
            try:
                row = connection.execute("SELECT version, created_at FROM agent_checkpoints WHERE task_id = ?", (state.task_id,)).fetchone()
                version = (row[0] if row else 0) + 1
                created_at = row[1] if row else now
                state.checkpoint_version = version
                if state.tool_history:
                    state.tool_history[-1]["checkpoint_version"] = version
                state_json = json.dumps(state.to_dict(), ensure_ascii=False, separators=(",", ":"), default=str)
                connection.execute("""
                    INSERT OR REPLACE INTO agent_checkpoints (
                        task_id, original_query, current_query, state_json, status,
                        step_count, final_answer, version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (state.task_id, state.original_query, state.current_query, state_json, state.status, state.step_count, state.final_answer, version, created_at, now))
                connection.commit()
                return version
            finally:
                if connection is not self._memory_connection:
                    connection.close()

    def load(self, task_id: str) -> AgentState:
        with self._lock:
            connection = self._connect()
            try:
                row = connection.execute("SELECT state_json, version FROM agent_checkpoints WHERE task_id = ?", (task_id,)).fetchone()
            finally:
                if connection is not self._memory_connection:
                    connection.close()
        if row is None:
            raise KeyError(f"Checkpoint task_id 不存在: {task_id}")
        state = AgentState.from_dict(json.loads(row[0]))
        state.checkpoint_version = int(row[1])
        return state

    def close(self) -> None:
        if self._memory_connection is not None:
            self._memory_connection.close()
            self._memory_connection = None
