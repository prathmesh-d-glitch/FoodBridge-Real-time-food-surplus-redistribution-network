import abc
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from shared.config import settings
from shared.logging_setup import setup_logger

logger = setup_logger("firestore_client")


class BaseFirestoreClient(abc.ABC):
    @abc.abstractmethod
    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def set_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        pass

    @abc.abstractmethod
    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        pass

    @abc.abstractmethod
    def delete_document(self, collection: str, doc_id: str) -> None:
        pass

    @abc.abstractmethod
    def query_collection(
        self,
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        pass


def _resolve_db_file_path() -> Path:
    env_path = os.getenv("FOODBRIDGE_DB_PATH")
    if env_path:
        return Path(env_path)
    # Default to foodbridge/.foodbridge_db.json
    here = Path(__file__).resolve()
    # traverse up to find foodbridge folder
    for parent in [here.parent, here.parent.parent, here.parent.parent.parent, here.parent.parent.parent.parent]:
        if (parent / "services").exists():
            return parent / ".foodbridge_db.json"
    return here.parent / ".foodbridge_db.json"


class PersistentInMemoryFirestoreClient(BaseFirestoreClient):
    """Zero-credentials, file-backed persistent store for local and simulation runs.
    Syncs across multiple microservice processes via .foodbridge_db.json so that
    state (listings, offers, approvals, routes) persists across browser refreshes and restarts.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._collections: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self._db_path = db_path or _resolve_db_file_path()
        self._last_mtime = 0.0
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        try:
            if self._db_path.exists():
                mtime = self._db_path.stat().st_mtime
                if mtime > self._last_mtime:
                    with open(self._db_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            self._collections = data
                            self._last_mtime = mtime
        except Exception as e:
            logger.debug(f"Could not load persistent database from {self._db_path}: {e}")

    def _save_to_disk(self) -> None:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._db_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._collections, f, indent=2, default=str)
            # Atomic replacement
            os.replace(tmp_path, self._db_path)
            self._last_mtime = self._db_path.stat().st_mtime
        except Exception as e:
            logger.warning(f"Could not save persistent database to {self._db_path}: {e}")

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._load_from_disk()
            col = self._collections.get(collection, {})
            doc = col.get(doc_id)
            return dict(doc) if doc else None

    def set_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            self._load_from_disk()
            if collection not in self._collections:
                self._collections[collection] = {}
            self._collections[collection][doc_id] = dict(data)
            self._save_to_disk()
            logger.debug(f"PersistentStore: Saved document '{collection}/{doc_id}'")

    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            self._load_from_disk()
            if collection not in self._collections:
                self._collections[collection] = {}
            if doc_id not in self._collections[collection]:
                self._collections[collection][doc_id] = {}
            self._collections[collection][doc_id].update(data)
            self._save_to_disk()
            logger.debug(f"PersistentStore: Updated document '{collection}/{doc_id}'")

    def delete_document(self, collection: str, doc_id: str) -> None:
        with self._lock:
            self._load_from_disk()
            if collection in self._collections:
                self._collections[collection].pop(doc_id, None)
                self._save_to_disk()

    def query_collection(
        self,
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            self._load_from_disk()
            col = self._collections.get(collection, {})
            results = list(col.values())

        if filters:
            for field, op, val in filters:
                if op == "==":
                    results = [r for r in results if r.get(field) == val]
                elif op == "!=":
                    results = [r for r in results if r.get(field) != val]
                elif op == "in":
                    results = [r for r in results if r.get(field) in val]
                elif op == "<":
                    results = [r for r in results if r.get(field) is not None and r.get(field) < val]
                elif op == "<=":
                    results = [r for r in results if r.get(field) is not None and r.get(field) <= val]
                elif op == ">":
                    results = [r for r in results if r.get(field) is not None and r.get(field) > val]
                elif op == ">=":
                    results = [r for r in results if r.get(field) is not None and r.get(field) >= val]

        if order_by:
            descending = order_by.startswith("-")
            field_name = order_by.lstrip("-")
            results.sort(
                key=lambda x: (x.get(field_name) is None, x.get(field_name)),
                reverse=descending,
            )

        if limit:
            results = results[:limit]

        return [dict(r) for r in results]

    def clear(self):
        with self._lock:
            self._collections.clear()
            self._save_to_disk()


# Alias for backward compatibility
InMemoryFirestoreClient = PersistentInMemoryFirestoreClient


class RealFirestoreClient(BaseFirestoreClient):
    """Google Cloud Firestore client implementation."""

    def __init__(self, project_id: str, database: str = "(default)"):
        from google.cloud import firestore
        self.db = firestore.Client(project=project_id, database=database)

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.db.collection(collection).document(doc_id)
        snapshot = doc_ref.get()
        return snapshot.to_dict() if snapshot.exists else None

    def set_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        doc_ref = self.db.collection(collection).document(doc_id)
        doc_ref.set(data)

    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        doc_ref = self.db.collection(collection).document(doc_id)
        doc_ref.update(data)

    def delete_document(self, collection: str, doc_id: str) -> None:
        doc_ref = self.db.collection(collection).document(doc_id)
        doc_ref.delete()

    def query_collection(
        self,
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        query = self.db.collection(collection)
        if filters:
            for field, op, val in filters:
                query = query.where(field, op, val)
        if order_by:
            from google.cloud.firestore import Query
            direction = Query.DESCENDING if order_by.startswith("-") else Query.ASCENDING
            field_name = order_by.lstrip("-")
            query = query.order_by(field_name, direction=direction)
        if limit:
            query = query.limit(limit)

        docs = query.stream()
        return [d.to_dict() for d in docs]


_firestore_instance: Optional[BaseFirestoreClient] = None


def get_firestore_client() -> BaseFirestoreClient:
    global _firestore_instance
    if _firestore_instance is None:
        emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST") or settings.FIRESTORE_EMULATOR_HOST
        try:
            if emulator_host or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                _firestore_instance = RealFirestoreClient(
                    project_id=settings.GCP_PROJECT_ID,
                    database=settings.FIRESTORE_DATABASE,
                )
            else:
                _firestore_instance = PersistentInMemoryFirestoreClient()
        except Exception as e:
            logger.warning(f"Could not initialize Cloud Firestore ({e}); using PersistentInMemoryFirestoreClient")
            _firestore_instance = PersistentInMemoryFirestoreClient()
    return _firestore_instance
