"""SQLite storage for attack history, prompts, and cached data"""

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class HistoryEntry:
    id: int
    timestamp: datetime
    module: str
    target_type: str
    target_url: str
    success: bool
    confidence: float
    payload: str
    response: str
    details: dict[str, Any]


@dataclass
class TargetProfile:
    name: str
    target_type: str
    url: str
    config: dict[str, Any]
    created_at: datetime


def get_data_dir() -> Path:
    """Get or create the Akira data directory"""
    data_dir = Path.home() / ".akira"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    return get_data_dir() / "akira.db"


class Storage:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or get_db_path()
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS attack_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                module TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_url TEXT NOT NULL,
                success INTEGER NOT NULL,
                confidence REAL NOT NULL,
                payload TEXT,
                response TEXT,
                details_json TEXT
            );

            CREATE TABLE IF NOT EXISTS prompt_cache (
                key TEXT PRIMARY KEY,
                prompt_text TEXT NOT NULL,
                source TEXT,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS target_profiles (
                name TEXT PRIMARY KEY,
                target_type TEXT NOT NULL,
                url TEXT NOT NULL,
                config_json TEXT,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS response_cache (
                request_hash TEXT PRIMARY KEY,
                response TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL
            );

            CREATE INDEX IF NOT EXISTS idx_history_timestamp ON attack_history(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_history_module ON attack_history(module);
            CREATE INDEX IF NOT EXISTS idx_history_success ON attack_history(success);
            CREATE INDEX IF NOT EXISTS idx_cache_expires ON response_cache(expires_at);
        """)
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # Attack History

    def save_history(
        self,
        module: str,
        target_type: str,
        target_url: str,
        success: bool,
        confidence: float,
        payload: str = "",
        response: str = "",
        details: dict[str, Any] | None = None,
    ) -> int:
        """Save an attack result to history. Returns the entry ID."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            INSERT INTO attack_history
            (timestamp, module, target_type, target_url, success, confidence, payload, response, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                time.time(),
                module,
                target_type,
                target_url,
                int(success),
                confidence,
                payload[:10000] if payload else "",
                response[:10000] if response else "",
                json.dumps(details or {}),
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0

    def get_history(
        self,
        limit: int = 50,
        module: str | None = None,
        success_only: bool = False,
    ) -> list[HistoryEntry]:
        """Retrieve attack history with optional filters."""
        conn = self._get_conn()
        query = "SELECT * FROM attack_history WHERE 1=1"
        params: list[Any] = []

        if module:
            query += " AND module LIKE ?"
            params.append(f"%{module}%")
        if success_only:
            query += " AND success = 1"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        return [
            HistoryEntry(
                id=row["id"],
                timestamp=datetime.fromtimestamp(row["timestamp"]),
                module=row["module"],
                target_type=row["target_type"],
                target_url=row["target_url"],
                success=bool(row["success"]),
                confidence=row["confidence"],
                payload=row["payload"],
                response=row["response"],
                details=json.loads(row["details_json"] or "{}"),
            )
            for row in rows
        ]

    def get_history_entry(self, entry_id: int) -> HistoryEntry | None:
        """Get a specific history entry by ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM attack_history WHERE id = ?", (entry_id,)
        ).fetchone()
        if not row:
            return None
        return HistoryEntry(
            id=row["id"],
            timestamp=datetime.fromtimestamp(row["timestamp"]),
            module=row["module"],
            target_type=row["target_type"],
            target_url=row["target_url"],
            success=bool(row["success"]),
            confidence=row["confidence"],
            payload=row["payload"],
            response=row["response"],
            details=json.loads(row["details_json"] or "{}"),
        )

    def clear_history(self, before_days: int | None = None) -> int:
        """Clear history. Optionally only entries older than N days. Returns count deleted."""
        conn = self._get_conn()
        if before_days:
            cutoff = time.time() - (before_days * 86400)
            cursor = conn.execute(
                "DELETE FROM attack_history WHERE timestamp < ?", (cutoff,)
            )
        else:
            cursor = conn.execute("DELETE FROM attack_history")
        conn.commit()
        return cursor.rowcount

    # Prompt Cache

    def cache_prompt(self, key: str, prompt_text: str, source: str = "") -> None:
        """Cache a prompt by key."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO prompt_cache (key, prompt_text, source, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (key, prompt_text, source, time.time()),
        )
        conn.commit()

    def get_cached_prompt(self, key: str) -> str | None:
        """Get a cached prompt by key."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT prompt_text FROM prompt_cache WHERE key = ?", (key,)
        ).fetchone()
        return row["prompt_text"] if row else None

    def list_cached_prompts(self) -> list[tuple[str, str, datetime]]:
        """List all cached prompts. Returns (key, source, updated_at) tuples."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT key, source, updated_at FROM prompt_cache ORDER BY updated_at DESC"
        ).fetchall()
        return [(r["key"], r["source"], datetime.fromtimestamp(r["updated_at"])) for r in rows]

    def delete_cached_prompt(self, key: str) -> bool:
        """Delete a cached prompt. Returns True if deleted."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM prompt_cache WHERE key = ?", (key,))
        conn.commit()
        return cursor.rowcount > 0

    # Target Profiles

    def save_target_profile(
        self, name: str, target_type: str, url: str, config: dict[str, Any] | None = None
    ) -> None:
        """Save a target profile for reuse."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO target_profiles (name, target_type, url, config_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, target_type, url, json.dumps(config or {}), time.time()),
        )
        conn.commit()

    def get_target_profile(self, name: str) -> TargetProfile | None:
        """Get a saved target profile."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM target_profiles WHERE name = ?", (name,)
        ).fetchone()
        if not row:
            return None
        return TargetProfile(
            name=row["name"],
            target_type=row["target_type"],
            url=row["url"],
            config=json.loads(row["config_json"] or "{}"),
            created_at=datetime.fromtimestamp(row["created_at"]),
        )

    def list_target_profiles(self) -> list[TargetProfile]:
        """List all saved target profiles."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM target_profiles ORDER BY name"
        ).fetchall()
        return [
            TargetProfile(
                name=row["name"],
                target_type=row["target_type"],
                url=row["url"],
                config=json.loads(row["config_json"] or "{}"),
                created_at=datetime.fromtimestamp(row["created_at"]),
            )
            for row in rows
        ]

    def delete_target_profile(self, name: str) -> bool:
        """Delete a target profile. Returns True if deleted."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM target_profiles WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0

    # Response Cache

    def cache_response(
        self, request_data: str, response: str, ttl_seconds: int = 3600
    ) -> None:
        """Cache a response with optional TTL."""
        request_hash = hashlib.sha256(request_data.encode()).hexdigest()
        conn = self._get_conn()
        expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else None
        conn.execute(
            """
            INSERT OR REPLACE INTO response_cache (request_hash, response, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (request_hash, response, time.time(), expires_at),
        )
        conn.commit()

    def get_cached_response(self, request_data: str) -> str | None:
        """Get a cached response if not expired."""
        request_hash = hashlib.sha256(request_data.encode()).hexdigest()
        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT response FROM response_cache
            WHERE request_hash = ? AND (expires_at IS NULL OR expires_at > ?)
            """,
            (request_hash, time.time()),
        ).fetchone()
        return row["response"] if row else None

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries. Returns count deleted."""
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM response_cache WHERE expires_at IS NOT NULL AND expires_at < ?",
            (time.time(),),
        )
        conn.commit()
        return cursor.rowcount

    # Stats

    def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        conn = self._get_conn()
        history_count = conn.execute("SELECT COUNT(*) FROM attack_history").fetchone()[0]
        success_count = conn.execute(
            "SELECT COUNT(*) FROM attack_history WHERE success = 1"
        ).fetchone()[0]
        prompt_count = conn.execute("SELECT COUNT(*) FROM prompt_cache").fetchone()[0]
        profile_count = conn.execute("SELECT COUNT(*) FROM target_profiles").fetchone()[0]
        cache_count = conn.execute("SELECT COUNT(*) FROM response_cache").fetchone()[0]

        return {
            "history_entries": history_count,
            "successful_attacks": success_count,
            "success_rate": (success_count / history_count * 100) if history_count else 0,
            "cached_prompts": prompt_count,
            "target_profiles": profile_count,
            "cached_responses": cache_count,
            "db_size_kb": self.db_path.stat().st_size // 1024 if self.db_path.exists() else 0,
        }


# Global storage instance
_storage: Storage | None = None


def get_storage() -> Storage:
    """Get the global storage instance."""
    global _storage
    if _storage is None:
        _storage = Storage()
    return _storage
