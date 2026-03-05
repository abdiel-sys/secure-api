import sqlite3
from config import Config


def get_db_connection():
    """Esta función la usarás en tus rutas de Flask"""
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Esta función solo se llama al arrancar la app para crear las tablas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'cliente'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS surveys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        created_by INTEGER,
        FOREIGN KEY(created_by) REFERENCES users(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        survey_id INTEGER,
        question TEXT,
        FOREIGN KEY(survey_id) REFERENCES surveys(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        survey_id INTEGER,
        question_id INTEGER,
        answer TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(survey_id) REFERENCES surveys(id),
        FOREIGN KEY(question_id) REFERENCES questions(id)
    )
    """)
    conn.commit()
    conn.close()
    print("Base de datos inicializada con éxito")


if __name__ == "__main__":
    init_db()
