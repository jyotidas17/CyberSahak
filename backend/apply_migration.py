"""Apply the checked-in additive migration without touching existing records."""
from pathlib import Path

from db import get_db_connection

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "database" / "migrations"
connection = get_db_connection()
try:
    with connection.cursor() as cursor:
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            cursor.execute(migration.read_text(encoding="utf-8"))
            print(f"Applied {migration.name}")
    connection.commit()
except Exception:
    connection.rollback()
    raise
finally:
    connection.close()
