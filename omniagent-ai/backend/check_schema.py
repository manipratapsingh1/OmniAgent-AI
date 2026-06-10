from sqlalchemy import inspect
from app.db.session import engine

inspector = inspect(engine)
columns = inspector.get_columns('document')
print("Document table columns:")
for col in columns:
    print(f"  {col['name']}: {col['type']}")
