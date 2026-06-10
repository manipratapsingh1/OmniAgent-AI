from sqlalchemy import text
from app.db.session import engine

try:
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('004')"))
        conn.commit()
        print('✓ Migration 004 marked as applied')
except Exception as e:
    print(f'Error: {e}')
    if 'duplicate' in str(e).lower():
        print('Migration 004 already marked')
