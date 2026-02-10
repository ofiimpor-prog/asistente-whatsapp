import os
import json
import requests
from groq import Groq

# CONFIGURACIÓN
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

def transcribir_audio(url_audio, twilio_sid, twilio_token):
    temp_file = "audio.ogg"
    try:
        r = requests.get(url_audio, auth=(twilio_sid, twilio_token), timeout=15)
        if r.status_code != 200: return None
        with open(temp_file, "wb") as f: f.write(r.content)
        with open(temp_file, "rb") as audio:
            res = groq_client.audio.transcriptions.create(
                file=(temp_file, audio.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        return res.strip() if isinstance(res, str) else res.text
    except Exception: return None
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

def interpretar_mensaje(texto):
    """
    USO EXCLUSIVO DE GROQ LLAMA 3.3
    Eliminamos Gemini para evitar el error 404 de Google.
    """
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "Eres un asistente contable. Responde SOLO con un objeto JSON válido. Tipos: ingreso, egreso, cita, recordatorio, nota, saludo."
                },
                {
                    "role": "user", 
                    "content": f"Mensaje: '{texto}'. JSON: {{'tipo': '', 'descripcion': '', 'monto': null, 'fecha_hora': ''}}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content)

    except Exception as e:
        print(f"❌ Error en Groq: {e}")
        return {
            "tipo": "nota",
            "descripcion": texto,
            "monto": None,
            "fecha_hora": None
        }
