import os
from typing import Any, Dict, List
from shared.config import settings
from shared.logging_setup import setup_logger

logger = setup_logger("bq_sync")

# In-memory buffer for local zero-cloud-credentials mode
bq_synced_records: List[Dict[str, Any]] = []


def sync_record_to_bigquery(table_name: str, rows: List[Dict[str, Any]]) -> bool:
    """Streams analytics records to Google BigQuery with local fallback buffer."""
    bq_synced_records.extend(rows)

    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.info(f"[LOCAL BQ MOCK] Buffered {len(rows)} rows to table '{table_name}'")
        return True

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        table_id = f"{settings.GCP_PROJECT_ID}.foodbridge_analytics.{table_name}"
        errors = client.insert_rows_json(table_id, rows)
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            return False
        logger.info(f"Successfully streamed {len(rows)} rows to BigQuery table {table_id}")
        return True
    except Exception as e:
        logger.warning(f"BigQuery streaming error ({e}); preserved in local buffer", exc_info=True)
        return True
