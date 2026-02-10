import os
import json
import requests
from groq import Groq

# ======================
# CONFIGURACIÓN
# ======================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

# ======================
# AUDIO → TEXTO (Groq Whisper)
# ======================

def transcribir_audio(url_audio, twilio_sid, twilio_token):
    temp_file = "audio.ogg"
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
            resultado = groq_client.audio.transcriptions.create(
                file=(temp_file, audio.read()),
                model="whisper-large-v3",
                response_format="text"
            )

        return resultado.strip() if isinstance(resultado, str) else resultado.text

    except Exception as e:
        print("❌ Error transcripción Groq:", e)
        return None

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

# ======================
# TEXTO → INTENCIÓN (Gemini PRO estable)
# ======================

def interpretar_mensaje(texto):
    url = (
        "https://generativelanguage.googleapis.com/v1/"
        f"models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    )

    headers = {"Content-Type": "application/json"}

    prompt = f"""
Devuelve SOLO un JSON válido.
NO agregues texto adicional.

Tipos permitidos:
ingreso, egreso, cita, recordatorio, nota, saludo

Formato EXACTO:
{{
  "tipo": "",
  "descripcion": "",
  "monto": null,
  "fecha_hora": null
}}

Mensaje:
"{texto}"
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15
        )

        data = response.json()

        if "error" in data:
            print("⚠️ Error Gemini:", data["error"])
            raise ValueError("Gemini error")

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        inicio = raw.find("{")
        fin = raw.rfind("}") + 1

        if inicio == -1:
            raise ValueError("JSON no encontrado")

        return json.loads(raw[inicio:fin])

    except Exception as e:
        print("⚠️ Gemini falló, usando NOTA:", e)
        return {
            "tipo": "nota",
            "descripcion": texto,
            "monto": None,
            "fecha_hora": None
        }
