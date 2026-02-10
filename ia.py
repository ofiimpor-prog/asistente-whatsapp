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
    # Usamos Gemini 1.5 Flash (El modelo más estable de 2026)
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=" + str(GEMINI_API_KEY)
    
    headers = {"Content-Type": "application/json"}
    prompt = f"Responde SOLO JSON: {{'tipo': 'ingreso/egreso/cita/recordatorio/nota/saludo', 'descripcion': '', 'monto': null, 'fecha_hora': ''}}. Mensaje: '{texto}'"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()

        if "error" in data:
            # Si Gemini falla, intentamos usar Groq con un modelo NUEVO (Llama 3.3)
            return interpretar_con_groq(texto)

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        
        inicio = raw.find("{")
        fin = raw.rfind("}") + 1
        return json.loads(raw[inicio:fin])

    except Exception:
        return interpretar_con_groq(texto)

def interpretar_con_groq(texto):
    """Sistema de respaldo usando el modelo NUEVO de Groq"""
    try:
        # Actualizado a llama-3.3-70b-versatile (Modelo vigente en 2026)
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Responde SOLO JSON válido."},
                {"role": "user", "content": f"Clasifica: {texto}. JSON: {{'tipo': '', 'descripcion': '', 'monto': null, 'fecha_hora': ''}}"}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Fallo total IA: {e}")
        return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
