import os
import json
import requests
from datetime import datetime, timedelta
from groq import Groq
from database import SessionLocal, Transaccion, Recordatorio
from sqlalchemy import func

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def procesar_mensaje_ia(texto, media_url, usuario):
    # 1. Si hay audio, intentamos transcribir con Groq Whisper
    if media_url:
        try:
            # Nota: Para audios reales, Twilio requiere Auth básica para descargar el .ogg
            # Por ahora, simulamos la transcripción para no romper el flujo
            texto_final = "Gasto 5000 en almuerzo" # Aquí iría la llamada a Whisper
        except:
            return "No pude procesar el audio correctamente."
    else:
        texto_final = texto

    prompt_sistema = f"""
    Eres un asistente contable. Hoy es {datetime.now().strftime('%Y-%m-%d')}.
    Devuelve SOLO un JSON:
    - Para gastos/ingresos: {{"tipo": "finanzas", "accion": "ingreso|egreso", "monto": float, "descripcion": "str"}}
    - Para resumen: {{"tipo": "resumen", "periodo": "dia|mes"}}
    - Para citas: {{"tipo": "agenda", "evento": "str", "fecha": "YYYY-MM-DD HH:MM"}}
    """

    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": texto_final}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        datos = json.loads(completion.choices[0].message.content)
        return ejecutar_accion(datos, usuario)
    except Exception as e:
        return f"Error en IA: {str(e)}"

def ejecutar_accion(datos, usuario):
    db = SessionLocal()
    try:
        if datos.get('tipo') == 'finanzas':
            nueva = Transaccion(usuario=usuario, tipo=datos['accion'], monto=datos['monto'], descripcion=datos['descripcion'])
            db.add(nueva)
            db.commit()
            return f"✅ {datos['accion'].capitalize()} de ${datos['monto']} guardado."

        elif datos.get('tipo') == 'resumen':
            inicio = datetime.now().replace(day=1, hour=0, minute=0) if datos['periodo'] == 'mes' else datetime.now().replace(hour=0, minute=0)
            
            egresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.usuario == usuario, Transaccion.tipo == 'egreso', Transaccion.fecha >= inicio).scalar() or 0
            ingresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.usuario == usuario, Transaccion.tipo == 'ingreso', Transaccion.fecha >= inicio).scalar() or 0
            
            periodo_str = "este mes" if datos['periodo'] == 'mes' else "hoy"
            return f"📊 Balance de {periodo_str}:\n💰 Ingresos: ${ingresos}\n💸 Gastos: ${egresos}\n⚖️ Neto: ${ingresos - egresos}"

        elif datos.get('tipo') == 'agenda':
            nueva_cita = Recordatorio(usuario=usuario, contenido=datos['evento'], fecha_recordatorio=datetime.strptime(datos['fecha'], '%Y-%m-%d %H:%M'))
            db.add(nueva_cita)
            db.commit()
            return f"📅 Cita agendada: {datos['evento']} para {datos['fecha']}"

    finally:
        db.close()
    return "No entendí la instrucción."
