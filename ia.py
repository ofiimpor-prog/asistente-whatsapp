import os
import json
import requests
from groq import Groq

# CONFIGURACIÓN
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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
    # URL SIN CORCHETES, SIN ESPACIOS, TOTALMENTE LIMPIA
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=" + str(GEMINI_API_KEY)
    
    headers = {"Content-Type": "application/json"}
    prompt = f"Responde SOLO JSON: {{'tipo': 'ingreso/egreso/cita/recordatorio/nota/saludo', 'descripcion': '', 'monto': null, 'fecha_hora': ''}}. Mensaje: '{texto}'"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        # Aquí es donde fallaba por la URL mal escrita
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()

        if "error" in data:
            print(f"Error de API: {data['error']['message']}")
            return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Limpiar markdown por si acaso
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        
        inicio = raw.find("{")
        fin = raw.rfind("}") + 1
        return json.loads(raw[inicio:fin])

    except Exception as e:
        print(f"⚠️ Error final: {e}")
        return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
