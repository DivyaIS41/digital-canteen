import mysql.connector
from flask import flash

from config import build_mysql_config


def validate_db_config():
    config = build_mysql_config()
    required_keys = ("host", "user", "password", "database")
    missing = [key.upper() for key in required_keys if not config.get(key)]
    if missing:
        return False, f"Missing database settings: {', '.join(missing)}"
    return True, "OK"


def get_db_connection(include_database=True):
    db_settings = build_mysql_config()
    connection_kwargs = {
        "host": db_settings["host"],
        "port": db_settings["port"],
        "user": db_settings["user"],
        "password": db_settings["password"],
    }

    if include_database:
        connection_kwargs["database"] = db_settings["database"]

    ssl_mode = db_settings.get("ssl_mode")
    if ssl_mode:
        connection_kwargs["ssl_disabled"] = False
        connection_kwargs["ssl_verify_cert"] = ssl_mode.upper() in {"VERIFY_CA", "VERIFY_IDENTITY"}
        connection_kwargs["ssl_verify_identity"] = ssl_mode.upper() == "VERIFY_IDENTITY"
        if db_settings.get("ssl_ca"):
            connection_kwargs["ssl_ca"] = db_settings["ssl_ca"]

    try:
        return mysql.connector.connect(**connection_kwargs)
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        try:
            flash("Database connection error. Please contact administrator.", "danger")
        except Exception:
            pass
        return None


def fetch_all(query, params=None):
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Database error in fetch_all: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Database error in fetch_one: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


def execute_query(query, params=None, fetch_id=False):
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        conn.commit()
        if fetch_id:
            return cursor.lastrowid
        return True
    except mysql.connector.Error as err:
        print(f"Database error in execute_query: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
