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
    """
    Usamos Groq Llama 3.3 como cerebro principal 
    porque Google está dando problemas de modelos.
    """
    try:
        # Usamos el modelo más nuevo y estable de Groq en 2026
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "Eres un asistente contable. Responde SOLO con un objeto JSON válido."
                },
                {
                    "role": "user", 
                    "content": f"Clasifica el siguiente mensaje: '{texto}'. \nFormato: {{'tipo': 'ingreso/egreso/cita/recordatorio/nota/saludo', 'descripcion': '', 'monto': null, 'fecha_hora': ''}}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        # Extraer y convertir a JSON
        respuesta = json.loads(completion.choices[0].message.content)
        return respuesta

    except Exception as e:
        print(f"Error en Groq: {e}")
        # Si Groq falla, intentamos una última vez con Gemini (como respaldo)
        return interpretar_con_gemini_fallback(texto)

def interpretar_con_gemini_fallback(texto):
    """Respaldo final en caso de que Groq falle"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": f"Responde solo JSON: {{'tipo': 'nota', 'descripcion': '{texto}', 'monto': null, 'fecha_hora': ''}}"}]}]}
    try:
        response = requests.post(url, json=payload, timeout=5)
        raw = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        inicio, fin = raw.find("{"), raw.rfind("}") + 1
        return json.loads(raw[inicio:fin])
    except:
        return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
