import os
import json
import requests
from groq import Groq
from google import genai # Nueva librería de Google

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Inicializar clientes
client_gemini = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

def transcribir_audio(url_audio, twilio_sid, twilio_token):
    temp_file = "temp_audio.ogg"
    try:
        r = requests.get(url_audio, auth=(twilio_sid, twilio_token), timeout=15)
        if r.status_code == 200:
            with open(temp_file, "wb") as f:
                f.write(r.content)
            with open(temp_file, "rb") as audio:
                transcription = groq_client.audio.transcriptions.create(
                    file=(temp_file, audio.read()),
                    model="whisper-large-v3",
                    response_format="text"
                )
            if os.path.exists(temp_file): os.remove(temp_file)
            return transcription.strip()
    except Exception as e:
        if os.path.exists(temp_file): os.remove(temp_file)
        print(f"Error audio: {e}")
    return None

def interpretar_mensaje(texto):
    prompt = f"""
    Actúa como clasificador de mensajes para un asistente personal.
    Responde ÚNICAMENTE con un JSON válido. No incluyas explicaciones ni markdown.
    Tipos: 'ingreso', 'egreso', 'cita', 'recordatorio', 'nota', 'saludo'.
    Formato JSON: {{"tipo": "", "descripcion": "", "monto": null, "fecha_hora": ""}}
    Mensaje: "{texto}"
    """
    try:
        # Usamos el modelo flash-1.5 que es el más estable y gratuito
        response = client_gemini.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        raw = response.text.strip()
        inicio = raw.find("{")
        fin = raw.rfind("}") + 1
        return json.loads(raw[inicio:fin])
    except Exception as e:
        print(f"Error IA corregido: {e}")
        return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
