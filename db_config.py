import mysql.connector
from flask import flash
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MySQL Configuration from .env
DB_CONFIG = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'itsdivya'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'canteen')
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        # Note: Flash works here only if called within a Flask request context
        try:
            flash("Database connection error. Please contact administrator.", 'danger')
        except:
            pass
        return None

def fetch_all(query, params=None):
    conn = get_db_connection()
    if not conn: return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        # Convert Decimals to float
        from decimal import Decimal
        for row in result:
            for key, value in row.items():
                if isinstance(value, Decimal):
                    row[key] = float(value)
        return result
    except mysql.connector.Error as err:
        print(f"Database error in fetch_all: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def fetch_one(query, params=None):
    conn = get_db_connection()
    if not conn: return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        if result:
            from decimal import Decimal
            for key, value in result.items():
                if isinstance(value, Decimal):
                    result[key] = float(value)
        return result
    except mysql.connector.Error as err:
        print(f"Database error in fetch_one: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def execute_query(query, params=None, fetch_id=False):
    conn = get_db_connection()
    if not conn: return None
        
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        if fetch_id:
            last_id = cursor.lastrowid
            return last_id
        return True
    except mysql.connector.Error as err:
        print(f"Database error in execute_query: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()