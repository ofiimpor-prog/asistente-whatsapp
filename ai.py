import os
import json
import requests
from groq import Groq
from google import genai

# 🔐 Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 🤖 Clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


# 🎧 AUDIO → TEXTO (GROQ)
def transcribir_audio(media_url, twilio_sid, twilio_token):
    temp_file = "audio.ogg"

    try:
        r = requests.get(
            media_url,
            auth=(twilio_sid, twilio_token),
            timeout=20
        )

        if r.status_code != 200:
            return None

        with open(temp_file, "wb") as f:
            f.write(r.content)

        with open(temp_file, "rb") as audio:
            result = groq_client.audio.transcriptions.create(
                file=(temp_file, audio.read()),
                model="whisper-large-v3",
                response_format="text"
            )

        return result.strip()

    except Exception as e:
        print("❌ Error audio:", e)
        return None

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


# 🧠 TEXTO → INTENCIÓN (GEMINI)
def interpretar_mensaje(texto):
    prompt = f"""
Responde SOLO JSON válido.
Tipos posibles:
ingreso, egreso, cita, recordatorio, saludo, nota

Formato:
{{
  "tipo": "",
  "descripcion": "",
  "monto": null
}}

Mensaje: "{texto}"
"""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-1.5-flash-001",
            contents=prompt
        )

        raw = response.text.strip()

        inicio = raw.find("{")
        fin = raw.rfind("}") + 1

        if inicio == -1 or fin == -1:
            raise ValueError("JSON no encontrado")

        return json.loads(raw[inicio:fin])

    except Exception as e:
        print("❌ Error Gemini:", e)
        return {
            "tipo": "nota",
            "descripcion": texto,
            "monto": None
        }
