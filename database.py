import sqlite3

def conectar_db():
    # Creamos la conexión a la base de datos local
    conn = sqlite3.connect("asistente.db")
    cursor = conn.cursor()
    # Creamos la tabla si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            descripcion TEXT,
            monto REAL,
            fecha_hora TEXT
        )
    """)
    conn.commit()
    return conn

def guardar_registro(tipo, descripcion, monto, fecha_hora):
    """Esta es la función que main.py no encontraba"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO registros (tipo, descripcion, monto, fecha_hora) VALUES (?, ?, ?, ?)",
        (tipo, descripcion, monto, fecha_hora)
    )
    conn.commit()
    conn.close()

def obtener_resumen_gastos():
    """Esta función genera los totales para el informe"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Sumar ingresos y egresos
    cursor.execute("SELECT tipo, SUM(monto) FROM registros WHERE monto IS NOT NULL GROUP BY tipo")
    totales = dict(cursor.fetchall())
    
    # Obtener los últimos 5 movimientos
    cursor.execute("SELECT tipo, descripcion, monto FROM registros ORDER BY id DESC LIMIT 5")
    filas = cursor.fetchall()
    
    conn.close()
    
    ingresos = totales.get('ingreso', 0)
    egresos = totales.get('egreso', 0)
    
    detalles = ""
    for f in filas:
        emoji = "💰" if f[0] == "ingreso" else "💸"
        monto_formateado = f"{f[2]:,.0f}".replace(",", ".") # Formato chileno opcional
        detalles += f"{emoji} {f[1]}: ${monto_formateado}\n"
        
    return {
        "total_ingresos": ingresos,
        "total_egresos": egresos,
        "balance": ingresos - egresos,
        "detalles": detalles if detalles else "No hay movimientos registrados."
    }
