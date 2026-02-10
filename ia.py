import os
import json
import requests
from groq import Groq

# ======================
# CONFIGURACIÓN
# ======================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# ======================
# AUDIO → TEXTO (Whisper Groq)
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
        print("❌ Error audio:", e)
        return None

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

# ======================
# TEXTO → INTENCIÓN (Groq LLM)
# ======================

def interpretar_mensaje(texto):
    prompt = f"""
Devuelve SOLO un JSON válido.
No expliques nada.

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

    try:
        completion = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "Eres un clasificador de mensajes para un asistente personal."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        raw = completion.choices[0].message.content.strip()

        inicio = raw.find("{")
        fin = raw.rfind("}") + 1

        if inicio == -1:
            raise ValueError("JSON no encontrado")

        return json.loads(raw[inicio:fin])

    except Exception as e:
        print("⚠️ Groq LLM falló:", e)
        return {
            "tipo": "nota",
            "descripcion": texto,
            "monto": None,
            "fecha_hora": None
        }
