import os
import json
import requests
from datetime import datetime
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
                with open("/tmp/audio.ogg", "wb") as f:
                    f.write(audio_data.content)
                with open("/tmp/audio.ogg", "rb") as audio_file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=("/tmp/audio.ogg", audio_file.read()),
                        model="whisper-large-v3",
                        response_format="text"
                    )
                texto_final = transcription
        except Exception as e:
            return "No pude procesar tu audio. ¿Podrías repetirlo?"

    prompt_sistema = f"""
    Eres un asistente contable y de agenda personal. Hoy es {datetime.now().strftime('%Y-%m-%d %H:%M')}.
    Responde UNICAMENTE un JSON:
    - Finanzas: {{"tipo": "finanzas", "accion": "ingreso|egreso", "monto": float, "descripcion": "str"}}
    - Resumen: {{"tipo": "resumen", "periodo": "dia|mes"}}
    - Agenda: {{"tipo": "agenda", "evento": "str", "fecha": "YYYY-MM-DD HH:MM"}}
    - Saludo: {{"tipo": "charla", "mensaje": "str"}}
    """

    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": texto_final}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        datos = json.loads(completion.choices[0].message.content)
        
        if datos.get("tipo") == "charla":
            return "¡Hola! Soy tu asistente. Puedo anotar tus gastos (voz o texto), darte balances o agendar tus citas. ¿Qué hacemos hoy?"
            
        return ejecutar_accion(datos, usuario)
    except Exception as e:
        return f"Error en procesamiento: {str(e)}"

def ejecutar_accion(datos, usuario):
    db = SessionLocal()
    try:
        if datos.get('tipo') == 'finanzas':
            nueva = Transaccion(usuario=usuario, tipo=datos['accion'], monto=datos['monto'], descripcion=datos['descripcion'])
            db.add(nueva)
            db.commit()
            return f"✅ {datos['accion'].capitalize()} de ${datos['monto']} guardado por '{datos['descripcion']}'."

        elif datos.get('tipo') == 'resumen':
            inicio = datetime.now().replace(day=1, hour=0, minute=0) if datos['periodo'] == 'mes' else datetime.now().replace(hour=0, minute=0)
            egresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.usuario == usuario, Transaccion.tipo == 'egreso', Transaccion.fecha >= inicio).scalar() or 0
            ingresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.usuario == usuario, Transaccion.tipo == 'ingreso', Transaccion.fecha >= inicio).scalar() or 0
            periodo_str = "este mes" if datos['periodo'] == 'mes' else "hoy"
            return f"📊 Balance de {periodo_str}:\n💰 Ingresos: ${ingresos}\n💸 Gastos: ${egresos}\n⚖️ Neto: ${ingresos - egresos}"

        elif datos.get('tipo') == 'agenda':
            fecha_dt = datetime.strptime(datos['fecha'], '%Y-%m-%d %H:%M')
            nueva_cita = Recordatorio(usuario=usuario, contenido=datos['evento'], fecha_recordatorio=fecha_dt)
            db.add(nueva_cita)
            db.commit()
            return f"📅 He agendado '{datos['evento']}' para el {datos['fecha']}. Te avisaré por aquí en ese momento."
    finally:
        db.close()
    return "Recibido."
