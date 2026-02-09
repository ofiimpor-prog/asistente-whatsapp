import os
import json
import requests
from groq import Groq
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
groq_client = Groq(api_key=GROQ_API_KEY)

def transcribir_audio(url_audio, twilio_sid, twilio_token):
    temp_file = "temp_audio.ogg"

    if not url_audio:
        return None

    try:
        r = requests.get(
            url_audio,
            auth=(twilio_sid, twilio_token),
            timeout=15
        )

        if r.status_code != 200 or not r.content:
            return None

        with open(temp_file, "wb") as f:
            f.write(r.content)

        with open(temp_file, "rb") as audio:
            transcription = groq_client.audio.transcriptions.create(
                file=(temp_file, audio.read()),
                model="whisper-large-v3",
                response_format="text"
            )

        return transcription.strip()

    except Exception as e:
        print("Error audio:", e)
        return None

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def interpretar_mensaje(texto):
    if not texto:
        return {"tipo": "nota", "descripcion": ""}

    prompt = f"""
Actúa como clasificador de mensajes para un asistente personal.
Responde ÚNICAMENTE con JSON válido.

Tipos posibles:
ingreso, egreso, cita, recordatorio, nota, saludo

Formato:
{{
  "tipo": "",
  "descripcion": "",
  "monto": null,
  "fecha_hora": null
}}

Mensaje: "{texto}"
"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        inicio = raw.find("{")
        fin = raw.rfind("}") + 1

        if inicio == -1 or fin == -1:
            raise ValueError("Respuesta sin JSON")

        data = json.loads(raw[inicio:fin])

        if "tipo" not in data:
            raise ValueError("JSON inválido")

        return data

    except Exception as e:
        print("Error IA:", e)
        return {
            "tipo": "nota",
            "descripcion": texto,
            "monto": None,
            "fecha_hora": None
        }
