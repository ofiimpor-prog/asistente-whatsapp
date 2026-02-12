import os
import json
import requests
from datetime import datetime, timedelta
from groq import Groq
from database import SessionLocal, Transaccion, Recordatorio
from sqlalchemy import func

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

def procesar_mensaje_ia(texto, media_url, usuario):
    texto_final = texto
    if media_url:
        try:
            audio_data = requests.get(media_url, auth=(TWILIO_SID, TWILIO_TOKEN))
            if audio_data.status_code == 200:
                with open("/tmp/audio.ogg", "wb") as f: f.write(audio_data.content)
                with open("/tmp/audio.ogg", "rb") as audio_file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=("/tmp/audio.ogg", audio_file.read()),
                        model="whisper-large-v3", response_format="text"
                    )
                texto_final = transcription
        except: return "Error procesando audio."

    prompt_sistema = f"""
    Eres un asistente contable. Hoy es {datetime.now().strftime('%Y-%m-%d %H:%M')}.
    Responde UNICAMENTE un JSON:
    - Finanzas: {{"tipo": "finanzas", "accion": "ingreso|egreso", "monto": float, "descripcion": "str"}}
    - Resumen: {{"tipo": "resumen", "periodo": "dia|mes|semana"}}
    - Agenda: {{"tipo": "agenda", "evento": "str", "fecha": "YYYY-MM-DD HH:MM"}}
    - Saludo: {{"tipo": "charla", "mensaje": "str"}}
    """
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": texto_final}],
            model="llama-3.3-70b-versatile", response_format={"type": "json_object"}
        )
        datos = json.loads(completion.choices[0].message.content)
        if datos.get("tipo") == "charla": return "¡Hola! ¿En qué puedo ayudarte hoy?"
        return ejecutar_accion(datos, usuario)
    except Exception as e: return f"Error: {str(e)}"

def ejecutar_accion(datos, usuario):
    db = SessionLocal()
    try:
        if datos.get('tipo') == 'finanzas':
            nueva = Transaccion(usuario=usuario, tipo=datos['accion'], monto=datos['monto'], descripcion=datos['descripcion'])
            db.add(nueva)
            db.commit()
            return f"✅ {datos['accion'].capitalize()} de ${datos['monto']} guardado."
        elif datos.get('tipo') == 'resumen':
            return generar_reporte_automatico(usuario, datos['periodo'])
        elif datos.get('tipo') == 'agenda':
            nueva_cita = Recordatorio(usuario=usuario, contenido=datos['evento'], fecha_recordatorio=datetime.strptime(datos['fecha'], '%Y-%m-%d %H:%M'))
            db.add(nueva_cita)
            db.commit()
            return f"📅 Cita agendada para {datos['fecha']}."
    finally: db.close()
    return "OK"

def generar_reporte_automatico(usuario, periodo):
    db = SessionLocal()
    ahora = datetime.now()
    if periodo == 'mes':
        inicio = ahora.replace(day=1, hour=0, minute=0)
        txt = "del mes"
    elif periodo == 'semana':
        inicio = ahora - timedelta(days=7)
        txt = "de los últimos 7 días"
    else:
        inicio = ahora.replace(hour=0, minute=0)
        txt = "de hoy"

    egresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.usuario == usuario, Transaccion.tipo == 'egreso', Transaccion.fecha >= inicio).scalar() or 0
    ingresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.usuario == usuario, Transaccion.tipo == 'ingreso', Transaccion.fecha >= inicio).scalar() or 0
    
    top_gastos = db.query(Transaccion).filter(Transaccion.usuario == usuario, Transaccion.tipo == 'egreso', Transaccion.fecha >= inicio).order_by(Transaccion.monto.desc()).limit(3).all()
    detalle = ""
    if top_gastos:
        detalle = "\n\n🔝 Gastos mayores:\n" + "\n".join([f"• {g.descripcion}: ${g.monto}" for g in top_gastos])
    
    db.close()
    return f"📊 Balance {txt}:\n💰 Ingresos: ${ingresos}\n💸 Gastos: ${egresos}\n⚖️ Neto: ${ingresos - egresos}{detalle}"
