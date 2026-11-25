import os
import mysql.connector


# Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="cv_backend",
        password=os.environ["CV_DB_PASSWORD"],
        database="CV_Tool"
    )


# Read Database Records
def fetch_all(query, params=()):
    conn = get_db_connection()

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        conn.close()


# Read Single Record
def fetch_one(query, params=()):
    conn = get_db_connection()

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    finally:
        conn.close()


# Insert, Update and Delete Records
def execute_query(query, params=()):
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            record_id = cursor.lastrowid
            conn.commit()
            return record_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()