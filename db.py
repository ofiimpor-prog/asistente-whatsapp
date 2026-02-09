import sqlite3
from datetime import datetime

DB_NAME = "assistant.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Finanzas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS finanzas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        monto REAL NOT NULL,
        descripcion TEXT,
        fecha TEXT
    )""")

    # Agenda (citas y recordatorios)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        descripcion TEXT,
        fecha_hora TEXT,
        fecha_creacion TEXT
    )""")

    # Notas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        texto TEXT,
        fecha TEXT
    )""")

    conn.commit()
    conn.close()

def registrar_finanza(tipo, monto, descripcion):
    conn = get_connection()
    cursor = conn.cursor()
    fecha = datetime.now().isoformat()

    cursor.execute(
        "INSERT INTO finanzas (tipo, monto, descripcion, fecha) VALUES (?, ?, ?, ?)",
        (tipo, monto, descripcion, fecha)
    )

    conn.commit()
    conn.close()
    return f"{tipo} registrado: ${monto} - {descripcion}"

def registrar_agenda(tipo, descripcion, fecha_hora):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO agenda (tipo, descripcion, fecha_hora, fecha_creacion) VALUES (?, ?, ?, ?)",
        (tipo, descripcion, fecha_hora, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()
    return f"{tipo.capitalize()} guardado: {descripcion} ({fecha_hora})"

def registrar_nota(texto):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO notas (texto, fecha) VALUES (?, ?)",
        (texto, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()
    return "📝 Nota guardada correctamente"
