import os
import sqlite3

from flask import flash

from config import build_sqlite_path

DB_PATH = build_sqlite_path()


def validate_db_config():
    """Checks that the SQLite database path is usable."""
    if not DB_PATH:
        return False, "Missing SQLITE_DB_PATH"
    return True, "OK"


def prepare_query(query):
    return (
        query.replace("%s", "?")
        .replace("CURDATE()", "DATE('now', 'localtime')")
    )


def get_db_connection():
    try:
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as err:
        print(f"Error connecting to SQLite: {err}")
        try:
            flash("Database connection error. Please contact administrator.", "danger")
        except Exception:
            pass
        return None


def fetch_all(query, params=None):
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(prepare_query(query), params or ())
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as err:
        print(f"Database error in fetch_all: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute(prepare_query(query), params or ())
        result = cursor.fetchone()
        return dict(result) if result else None
    except sqlite3.Error as err:
        print(f"Database error in fetch_one: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


def execute_query(query, params=None, fetch_id=False):
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute(prepare_query(query), params or ())
        conn.commit()
        if fetch_id:
            return cursor.lastrowid
        return True
    except sqlite3.Error as err:
        print(f"Database error in execute_query: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def initialize_database(schema_path="schema.sql", seed_path="seed.sql"):
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with open(schema_path, "r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())

        if os.path.exists(seed_path):
            with open(seed_path, "r", encoding="utf-8") as seed_file:
                conn.executescript(seed_file.read())

        conn.commit()
        return True
    except (OSError, sqlite3.Error) as err:
        print(f"Database initialization error: {err}")
        conn.rollback()
        return False
    finally:
        conn.close()
