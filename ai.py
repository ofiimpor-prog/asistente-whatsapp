import os
import json
import requests
from groq import Groq
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
                result = groq_client.audio.transcriptions.create(
                    file=(temp_file, audio.read()),
                    model="whisper-large-v3",
                    response_format="text"
                )

            os.remove(temp_file)
            return result.strip()
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        print("Error audio:", e)
        return None

def interpretar_mensaje(texto):
    prompt = f"""
    Analiza el mensaje y responde SOLO JSON.
    Tipos posibles: ingreso, egreso, cita, recordatorio, nota, saludo.
    Formato exacto:
    {{
      "tipo": "",
      "descripcion": "",
      "monto": null,
      "fecha_hora": ""
    }}

    Mensaje: "{texto}"
    """

    try:
        response = client_gemini.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        raw = response.text.strip()
        inicio = raw.find("{")
        fin = raw.rfind("}") + 1

        if inicio == -1:
            raise ValueError("JSON no encontrado")

        return json.loads(raw[inicio:fin])

    except Exception as e:
        print("Error Gemini:", e)
        return {
            "tipo": "nota",
            "descripcion": texto,
            "monto": None,
            "fecha_hora": None
        }
