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
    # Usamos la URL más estable de Google
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # Prompt simplificado al máximo para evitar que la IA se bloquee
    prompt = (
        f"Clasifica este mensaje de WhatsApp y responde estrictamente en JSON. "
        f"Tipos: ingreso, egreso, cita, recordatorio, nota, saludo. "
        f"Mensaje: '{texto}'. "
        f"Formato: {{\"tipo\": \"\", \"descripcion\": \"\", \"monto\": null, \"fecha_hora\": \"\"}}"
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        
        # Validación de seguridad: si no hay respuesta, devolvemos nota
        if 'candidates' not in res_json or not res_json['candidates']:
            print("Google no devolvió candidatos:", res_json)
            return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}

        raw = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Limpieza de markdown por si Gemini manda ```json ... ```
        inicio = raw.find("{")
        fin = raw.rfind("}") + 1
        if inicio == -1: return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
        
        return json.loads(raw[inicio:fin])
        
    except Exception as e:
        print(f"Error interpretando: {e}")
        return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
