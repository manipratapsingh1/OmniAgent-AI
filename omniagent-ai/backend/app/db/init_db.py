from sqlalchemy import inspect, text
from sqlmodel import SQLModel
from app.db.base import metadata  # noqa: F401
from app.db.session import engine, test_db_connection
import structlog

log = structlog.get_logger("db")


def _ensure_missing_columns() -> None:
    """Add missing columns for rolling schema updates without destructive migrations."""
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
                    log.info(
                        "db.schema.column_added",
                        table=table_name,
                        column=column_name,
                        definition=column_definition,
                    )
                except Exception as e:
                    message = str(e).lower()
                    if "already exists" in message or "duplicate" in message:
                        log.info(
                            "db.schema.column_already_present",
                            table=table_name,
                            column=column_name,
                        )
                        continue
                    log.warning(
                        "db.schema.column_add_failed",
                        table=table_name,
                        column=column_name,
                        error=str(e),
                    )


def init_db() -> None:
    """Initialize database: test connection, create tables, and update missing schema fields."""
    try:
        log.info("db.init.starting")
        if not test_db_connection():
            log.error("db.init.failed", reason="Cannot connect to database")
            raise Exception("Database connection failed during initialization")

        log.info("db.init.creating_tables")
        SQLModel.metadata.create_all(engine)
        log.info("db.init.updating_schema")
        _ensure_missing_columns()
        log.info("db.init.success", status="tables_ready")

    except Exception as e:
        log.exception(
            "db.init.critical_error",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise