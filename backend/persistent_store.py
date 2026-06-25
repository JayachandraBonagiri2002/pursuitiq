"""
persistent_store.py — Cloud-synced pursuit store (Azure Blob Storage).

Architecture:
  - Primary: Azure Blob Storage (container: "pursuits") — single source of truth
  - Fallback: Local JSON files (./data/pursuits/) — works when Azure is unavailable
  - In-memory cache for fast reads during pipeline execution

Any server, any location → same pursuit data.
Writes go to cloud + local. Reads from memory (loaded from cloud on startup).

Debounce: Mutations mark the entry dirty. Flush happens at explicit save() calls
or via a 5-second debounce timer (whichever comes first). This avoids hammering
Azure Blob on every single field update during the pipeline.
"""

import json
import os
import logging
import threading
from typing import Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "pursuits")
BLOB_CONTAINER = "pursuits"


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _path_for(rfp_id: str) -> str:
    safe_id = rfp_id.replace("/", "_").replace("\\", "_")
    return os.path.join(DATA_DIR, f"{safe_id}.json")


def _blob_name(rfp_id: str) -> str:
    safe_id = rfp_id.replace("/", "_").replace("\\", "_")
    return f"{safe_id}.json"


def _get_blob_container():
    """Get Azure Blob container client for pursuits."""
    try:
        from azure.storage.blob import BlobServiceClient
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "https://stpursuitiq.blob.core.windows.net")

        if conn_str:
            service = BlobServiceClient.from_connection_string(conn_str)
        else:
            from azure.identity import DefaultAzureCredential
            service = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())

        container = service.get_container_client(BLOB_CONTAINER)
        if not container.exists():
            container.create_container()
            logger.info(f"Created blob container: {BLOB_CONTAINER}")
        return container
    except Exception as e:
        logger.warning(f"Azure Blob unavailable, using local-only: {e}")
        return None


class _TrackedDict(dict):
    """A dict that marks dirty on mutation; flush happens on save() or debounce timer."""

    def __init__(self, data: dict, store: "PursuitStore", rfp_id: str):
        super().__init__(data)
        self._store = store
        self._rfp_id = rfp_id

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._store._mark_dirty(self._rfp_id)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._store._mark_dirty(self._rfp_id)


class PursuitStore:
    """
    Cloud-synced persistent store.
    Reads from memory (fast). Writes to Azure Blob + local disk (durable + synced).
    On startup, loads from Azure Blob (cloud truth) with local fallback.

    Debounce: Mutations mark dirty. Flush occurs on explicit save(), shutdown,
    or after a 5-second debounce timer per rfp_id. Thread-safe with per-id locks.
    """

    DEBOUNCE_SECONDS = 5.0

    def __init__(self):
        _ensure_dir()
        self._cache: dict[str, dict[str, Any]] = {}
        self._container = _get_blob_container()
        self._dirty: set[str] = set()
        self._locks: dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()
        self._timers: dict[str, threading.Timer] = {}
        self._load_all()

    def _get_lock(self, rfp_id: str) -> threading.Lock:
        """Get or create a per-rfp_id lock (thread-safe)."""
        with self._global_lock:
            if rfp_id not in self._locks:
                self._locks[rfp_id] = threading.Lock()
            return self._locks[rfp_id]

    def _mark_dirty(self, rfp_id: str):
        """Mark an rfp_id as dirty and schedule a debounced flush."""
        self._dirty.add(rfp_id)
        # Cancel existing timer for this rfp_id, start a new one
        with self._global_lock:
            existing = self._timers.get(rfp_id)
            if existing:
                existing.cancel()
            timer = threading.Timer(self.DEBOUNCE_SECONDS, self._debounce_flush, args=[rfp_id])
            timer.daemon = True
            timer.start()
            self._timers[rfp_id] = timer

    def _debounce_flush(self, rfp_id: str):
        """Called by the debounce timer — flush if still dirty."""
        if rfp_id in self._dirty:
            self._flush(rfp_id)

    def save(self, rfp_id: str = None):
        """
        Explicitly flush dirty data to storage.
        If rfp_id is given, flush only that entry. Otherwise flush all dirty entries.
        """
        if rfp_id:
            if rfp_id in self._dirty:
                self._flush(rfp_id)
        else:
            for rid in list(self._dirty):
                self._flush(rid)

    def flush_all(self):
        """Flush all dirty entries — call on shutdown."""
        for rid in list(self._dirty):
            self._flush(rid)

    def _load_all(self):
        """Load all pursuits — try cloud first, fall back to local."""
        cloud_count = 0
        local_count = 0

        # Try loading from Azure Blob (single source of truth)
        if self._container:
            try:
                for blob in self._container.list_blobs():
                    if blob.name.endswith(".json"):
                        try:
                            blob_client = self._container.get_blob_client(blob.name)
                            content = blob_client.download_blob().readall()
                            data = json.loads(content.decode("utf-8"))
                            rfp_id = data.get("rfp_id", blob.name.replace(".json", ""))
                            self._cache[rfp_id] = _TrackedDict(data, self, rfp_id)
                            # Also cache locally for speed
                            self._write_local(rfp_id, data)
                            cloud_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to load blob {blob.name}: {e}")
                if cloud_count:
                    logger.info(f"Loaded {cloud_count} pursuits from Azure Blob (cloud-synced)")
                return
            except Exception as e:
                logger.warning(f"Cloud load failed, falling back to local: {e}")

        # Fallback: load from local disk
        _ensure_dir()
        for fname in os.listdir(DATA_DIR):
            if fname.endswith(".json"):
                fpath = os.path.join(DATA_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    rfp_id = data.get("rfp_id", fname.replace(".json", ""))
                    self._cache[rfp_id] = _TrackedDict(data, self, rfp_id)
                    local_count += 1
                except Exception as e:
                    logger.warning(f"Failed to load {fname}: {e}")
        if local_count:
            logger.info(f"Loaded {local_count} pursuits from local disk (offline mode)")

    def _flush(self, rfp_id: str):
        """Write to Azure Blob (primary) + local disk (cache). Thread-safe per rfp_id."""
        lock = self._get_lock(rfp_id)
        with lock:
            data = self._cache.get(rfp_id)
            if data is None:
                return

            # Clear dirty flag and cancel pending timer
            self._dirty.discard(rfp_id)
            with self._global_lock:
                timer = self._timers.pop(rfp_id, None)
                if timer:
                    timer.cancel()

            content = json.dumps(dict(data), indent=2, default=str)

            # Write to Azure Blob (primary — makes it available everywhere)
            if self._container:
                try:
                    blob_client = self._container.get_blob_client(_blob_name(rfp_id))
                    blob_client.upload_blob(
                        content.encode("utf-8"),
                        overwrite=True,
                        metadata={"rfp_id": rfp_id, "status": data.get("status", "unknown")},
                    )
                except Exception as e:
                    logger.warning(f"Blob write failed for {rfp_id}: {e}")

            # Write to local disk (fast reads, offline fallback)
            self._write_local(rfp_id, data)

    def _write_local(self, rfp_id: str, data: dict):
        """Write to local disk cache."""
        fpath = _path_for(rfp_id)
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(dict(data), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Local write failed for {rfp_id}: {e}")

    def __contains__(self, key: str) -> bool:
        return key in self._cache

    def __getitem__(self, key: str) -> dict[str, Any]:
        return self._cache[key]

    def __setitem__(self, key: str, value: dict[str, Any]):
        value.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
        self._cache[key] = _TrackedDict(value, self, key)
        self._flush(key)

    def __len__(self) -> int:
        return len(self._cache)

    def get(self, key: str, default=None):
        return self._cache.get(key, default)

    def values(self):
        return self._cache.values()

    def keys(self):
        return self._cache.keys()

    def items(self):
        return self._cache.items()

    def update_pursuit(self, rfp_id: str, **kwargs):
        """Update fields and flush to cloud + disk."""
        if rfp_id in self._cache:
            self._cache[rfp_id].update(kwargs)
            self._cache[rfp_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._flush(rfp_id)

    def mark_outcome(self, rfp_id: str, outcome: str):
        """Mark a pursuit as WON or LOST for learning."""
        if rfp_id not in self._cache:
            return False
        self._cache[rfp_id]["outcome"] = outcome.upper()
        self._cache[rfp_id]["outcome_date"] = datetime.now(timezone.utc).isoformat()
        self._flush(rfp_id)
        return True

    def get_completed(self) -> list[dict]:
        """Get all completed pursuits."""
        return [p for p in self._cache.values() if p.get("status") == "complete"]

    def get_stats(self) -> dict:
        """Get aggregate stats."""
        total = len(self._cache)
        completed = sum(1 for p in self._cache.values() if p.get("status") == "complete")
        won = sum(1 for p in self._cache.values() if p.get("outcome") == "WON")
        lost = sum(1 for p in self._cache.values() if p.get("outcome") == "LOST")
        return {
            "total_pursuits": total,
            "completed": completed,
            "won": won,
            "lost": lost,
            "win_rate": won / (won + lost) if (won + lost) > 0 else None,
            "pending_outcome": completed - won - lost,
        }
