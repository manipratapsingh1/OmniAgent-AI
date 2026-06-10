"""Add missing columns to document and conversation tables."""
from sqlalchemy import inspect, text
from app.db.session import engine
import structlog

log = structlog.get_logger(__name__)


def _ensure_missing_columns() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    schema_updates = {
        "document": [
            ("embedding_status", "VARCHAR DEFAULT 'pending'"),
            ("chunk_count", "INTEGER DEFAULT 0"),
            ("error_message", "VARCHAR(500)"),
            ("last_indexed_at", "TIMESTAMP"),
            ("vector_ids_prefix", "VARCHAR DEFAULT ''"),
            ("is_knowledge_base", "BOOLEAN DEFAULT false"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ],
        "documentchunk": [
            ("vector_id", "VARCHAR DEFAULT ''"),
        ],
        "conversation": [
            ("is_pinned", "BOOLEAN DEFAULT false"),
            ("is_shared", "BOOLEAN DEFAULT false"),
            ("folder_name", "VARCHAR"),
        ],
    }

    with engine.begin() as conn:
        for table_name, columns in schema_updates.items():
            if table_name not in existing_tables:
                log.info("db.schema.table_missing", table=table_name)
                continue

            existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
            for column_name, column_definition in columns:
                if column_name in existing_columns:
                    continue
                try:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))
                    log.info("db.schema.column_added", table=table_name, column=column_name)
                except Exception as e:
                    message = str(e).lower()
                    if "already exists" in message or "duplicate" in message:
                        log.info("db.schema.column_already_present", table=table_name, column=column_name)
                        continue
                    log.error("db.schema.column_add_failed", table=table_name, column=column_name, error=str(e))


if __name__ == "__main__":
    try:
        _ensure_missing_columns()
        print("✅ Database schema updated successfully!")
    except Exception as e:
        log.exception("Failed to update schema", error=str(e))
        print(f"❌ Error: {e}")
