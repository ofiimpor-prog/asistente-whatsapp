import sqlite3
from datetime import datetime

def create_table():
    conn = sqlite3.connect('messages.db')
    cursor = conn.cursor()
    # Agregamos la columna 'chosen_option'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            message TEXT,
            chosen_option TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_message(phone, message, chosen_option="N/A"):
    try:
        conn = sqlite3.connect('messages.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (phone, message, chosen_option, created_at) VALUES (?, ?, ?, ?)",
            (phone, message, chosen_option, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al guardar en DB: {e}")