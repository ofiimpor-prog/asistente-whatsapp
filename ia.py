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

        # Manejo flexible del retorno de Groq
        return resultado.strip() if isinstance(resultado, str) else resultado.text

    except Exception as e:
        print(f"❌ Error transcripción Groq: {e}")
        return None

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

# ======================
# TEXTO → INTENCIÓN (Gemini 1.5 Flash Estable)
# ======================

def interpretar_mensaje(texto):
    # Usamos v1 (estable) y 1.5-flash (el más moderno y rápido)
    url = f"[https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=){GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    prompt = f"""
Actúa como un extractor de datos profesional. 
Analiza el mensaje y devuelve ÚNICAMENTE un objeto JSON válido.
Tipos: ingreso, egreso, cita, recordatorio, nota, saludo.

Mensaje: "{texto}"

Formato JSON:
{{
  "tipo": "",
  "descripcion": "",
  "monto": null,
  "fecha_hora": null
}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.95,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()

        if "error" in data:
            print(f"⚠️ Error Gemini API: {data['error']['message']}")
            raise ValueError(data['error']['message'])

        # Extraer texto y limpiar posibles marcas de Markdown
        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Limpieza de bloques ```json ... ```
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        inicio = raw.find("{")
        fin = raw.rfind("}") + 1

        if inicio == -1:
            raise ValueError("JSON no encontrado en la respuesta")

        return json.loads(raw[inicio:fin])

    except Exception as e:
        print(f"⚠️ Fallo en interpretación: {e}")
        # Fallback seguro para no perder la información del usuario
        return {
            "tipo": "nota",
            "descripcion": texto,
            "monto": None,
            "fecha_hora": None
        }
