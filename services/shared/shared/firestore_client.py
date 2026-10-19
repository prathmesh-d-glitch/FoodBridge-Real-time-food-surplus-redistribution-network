import abc
import os
import threading
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


class InMemoryFirestoreClient(BaseFirestoreClient):
    """In-memory mock for Firestore supporting zero-credentials local runs and automated tests."""

    def __init__(self):
        self._collections: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            col = self._collections.get(collection, {})
            doc = col.get(doc_id)
            return dict(doc) if doc else None

    def set_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            if collection not in self._collections:
                self._collections[collection] = {}
            # Clone to prevent reference leakage
            self._collections[collection][doc_id] = dict(data)
            logger.debug(f"InMemoryFirestore: Saved document '{collection}/{doc_id}'")

    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            if collection not in self._collections or doc_id not in self._collections[collection]:
                # If document does not exist, create it
                if collection not in self._collections:
                    self._collections[collection] = {}
                self._collections[collection][doc_id] = {}
            self._collections[collection][doc_id].update(data)
            logger.debug(f"InMemoryFirestore: Updated document '{collection}/{doc_id}'")

    def delete_document(self, collection: str, doc_id: str) -> None:
        with self._lock:
            if collection in self._collections:
                self._collections[collection].pop(doc_id, None)

    def query_collection(
        self,
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            col = self._collections.get(collection, {})
            results = list(col.values())

        # Apply simple filters: list of (field, op, value), e.g. [("status", "==", "available")]
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

        # Apply ordering if requested
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
        # Check if real Firestore or emulator is requested and package available
        emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST") or settings.FIRESTORE_EMULATOR_HOST
        try:
            if emulator_host or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                _firestore_instance = RealFirestoreClient(
                    project_id=settings.GCP_PROJECT_ID,
                    database=settings.FIRESTORE_DATABASE,
                )
            else:
                _firestore_instance = InMemoryFirestoreClient()
        except Exception as e:
            logger.warning(f"Could not initialize Cloud Firestore ({e}); using InMemoryFirestoreClient")
            _firestore_instance = InMemoryFirestoreClient()
    return _firestore_instance
