import os
import json
import requests
from groq import Groq

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

def transcribir_audio(url_audio, twilio_sid, twilio_token):
    try:
        r = requests.get(url_audio, auth=(twilio_sid, twilio_token), timeout=15)
        if r.status_code != 200: return None
        with open("audio.ogg", "wb") as f: f.write(r.content)
        with open("audio.ogg", "rb") as audio:
            text = groq_client.audio.transcriptions.create(
                file=("audio.ogg", audio.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        return text.strip()
    except Exception: return None

def interpretar_mensaje(texto):
    # LLAMADA DIRECTA A LA API (Solución al error 404)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt = f"Responde SOLO JSON: {{'tipo': 'ingreso/egreso/cita/recordatorio/nota/saludo', 'descripcion': '', 'monto': null, 'fecha_hora': ''}}. Mensaje: '{texto}'"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        raw = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        inicio, fin = raw.find("{"), raw.rfind("}") + 1
        return json.loads(raw[inicio:fin])
    except Exception as e:
        print("Error Gemini:", e)
        return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
