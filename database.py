def obtener_resumen_gastos():
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Sumar ingresos y egresos
    cursor.execute("SELECT tipo, SUM(monto) FROM registros WHERE monto IS NOT NULL GROUP BY tipo")
    totales = dict(cursor.fetchall())
    
    # Obtener los últimos 5 movimientos para dar contexto
    cursor.execute("SELECT tipo, descripcion, monto FROM registros ORDER BY id DESC LIMIT 5")
    filas = cursor.fetchall()
    
    conn.close()
    
    ingresos = totales.get('ingreso', 0)
    egresos = totales.get('egreso', 0)
    
    detalles = ""
    for f in filas:
        emoji = "💰" if f[0] == "ingreso" else "💸"
        detalles += f"{emoji} {f[1]}: ${f[2]}\n"
        
    return {
        "total_ingresos": ingresos,
        "total_egresos": egresos,
        "balance": ingresos - egresos,
        "detalles": detalles
    }
