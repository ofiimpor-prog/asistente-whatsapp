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
    # Intentamos con el nombre de modelo más compatible en la v1
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    prompt = f"Responde SOLO JSON: {{'tipo': 'ingreso/egreso/cita/recordatorio/nota/saludo', 'descripcion': '', 'monto': null, 'fecha_hora': ''}}. Mensaje: '{texto}'"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        data = response.json()

        # Si Gemini falla, saltamos de inmediato a Groq Llama 3.3
        if "error" in data:
            print(f"Gemini falló, saltando a Groq Llama 3.3...")
            return interpretar_con_groq(texto)

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        inicio, fin = raw.find("{"), raw.rfind("}") + 1
        return json.loads(raw[inicio:fin])

    except Exception:
        return interpretar_con_groq(texto)

def interpretar_con_groq(texto):
    """Usando el modelo Llama 3.3 (Vigente en 2026)"""
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Este es el modelo actual que NO está decomisado
            messages=[
                {"role": "system", "content": "Responde SOLO JSON válido."},
                {"role": "user", "content": f"Clasifica: {texto}. JSON: {{'tipo': '', 'descripcion': '', 'monto': null, 'fecha_hora': ''}}"}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error total en ambas IAs: {e}")
        return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
