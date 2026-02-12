import os
import re
from datetime import datetime
import google.generativeai as genai
from groq import Groq
from database import SessionLocal, Transaccion, Recordatorio

# Configuración de APIs desde tus variables de entorno en Render
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Inicializar Clientes
genai.configure(api_key=GENAI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

def procesar_mensaje_ia(texto, media_url, usuario):
    """
    Cerebro del asistente: Transcribe audio, analiza texto y guarda en DB.
    """
    
    # 1. Manejo de Notas de Voz (Whisper vía Groq)
    if media_url:
        # Aquí se integraría la descarga del audio de Twilio y envío a Groq Whisper
        # Por ahora, procesamos el texto. Si necesitas el código de descarga de audio, avísame.
        texto_a_procesar = "[Nota de voz recibida: Procesando transcripción...]"
    else:
        texto_a_procesar = texto

    # 2. Prompt Maestro para extraer datos estructurados
    prompt_sistema = f"""
    Eres un asistente contable y de agenda. Tu objetivo es interpretar mensajes y devolver un JSON estricto.
    Hoy es {datetime.now().strftime('%Y-%m-%d %H:%M')}.
    
    Si el usuario dice un gasto o ingreso, extrae: {{"tipo": "finanzas", "accion": "ingreso|egreso", "monto": float, "descripcion": "str"}}
    Si el usuario dice una cita o recordatorio, extrae: {{"tipo": "agenda", "evento": "str", "fecha": "YYYY-MM-DD HH:MM"}}
    Si el usuario pide un resumen, extrae: {{"tipo": "resumen", "periodo": "dia|mes"}}
    
    Solo responde el JSON, nada más.
    """

    try:
        # Usamos Groq Llama 3 para extraer la intención rápidamente
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": texto_a_procesar}
            ],
            model="llama-3.3-70b-versatile",
            response_format={ "type": "json_object" }
        )
        
        datos = eval(chat_completion.choices[0].message.content)
        return ejecutar_accion(datos, usuario)

    except Exception as e:
        return f"Error al procesar: {str(e)}"

def ejecutar_accion(datos, usuario):
    """
    Guarda la información en la base de datos PostgreSQL de Render.
    """
    db = SessionLocal()
    try:
        if datos['tipo'] == 'finanzas':
            nueva_trans = Transaccion(
                usuario=usuario,
                tipo=datos['accion'],
                monto=datos['monto'],
                descripcion=datos['descripcion']
            )
            db.add(nueva_trans)
            db.commit()
            return f"✅ Registré un {datos['accion']} de ${datos['monto']} por: {datos['descripcion']}."

        elif datos['tipo'] == 'agenda':
            nuevo_rec = Recordatorio(
                usuario=usuario,
                contenido=datos['evento'],
                fecha_recordatorio=datetime.strptime
