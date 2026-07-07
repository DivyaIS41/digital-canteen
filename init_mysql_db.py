from pathlib import Path

from db_config import get_db_connection


def run_sql_file(cursor, file_path):
    script = Path(file_path).read_text(encoding="utf-8")
    for _ in cursor.execute(script, multi=True):
        pass


def initialize_database():
    conn = get_db_connection()
    if not conn:
        raise RuntimeError("Could not connect to the database.")

    try:
        cursor = conn.cursor()
        run_sql_file(cursor, "schema.sql")
        run_sql_file(cursor, "seed.sql")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    initialize_database()
    print("MySQL database initialized successfully.")
