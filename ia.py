import os
import json
import requests
from groq import Groq

# Configuración de llaves desde Render
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

def transcribir_audio(url_audio, twilio_sid, twilio_token):
    """Transcribe notas de voz usando Groq Whisper"""
    try:
        r = requests.get(url_audio, auth=(twilio_sid, twilio_token), timeout=15)
        if r.status_code != 200: 
            return None
            
        with open("audio.ogg", "wb") as f: 
            f.write(r.content)
            
        with open("audio.ogg", "rb") as audio:
            text = groq_client.audio.transcriptions.create(
                file=("audio.ogg", audio.read()),
                model="whisper-large-v3",
                # response_format="text" # Algunas versiones de la librería prefieren esto
            )
        
        # Ajuste para obtener el texto según la versión de la librería Groq
        return text.text if hasattr(text, 'text') else str(text).strip()
        
    except Exception as e:
        print(f"Error en transcripción: {e}")
        return None

def interpretar_mensaje(texto):
    """Analiza el texto con Gemini 1.5 Flash usando la API Estable v1"""
    
    # URL Forzada a versión 1 (Estable) para evitar el error 404
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = (
        f"Actúa como un asistente contable. Analiza el mensaje y responde ÚNICAMENTE un objeto JSON válido.\n"
        f"Tipos permitidos: 'ingreso', 'egreso', 'cita', 'recordatorio', 'nota', 'saludo'.\n"
        f"Mensaje: '{texto}'\n"
        f"Formato esperado: {{\"tipo\": \"\", \"descripcion\": \"\", \"monto\": null, \"fecha_hora\": \"\"}}"
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        
        # Verificación de respuesta exitosa
        if 'candidates' not in res_json:
            print(f"⚠️ Google API Error: {res_json}")
            return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}

        # Extraer el texto crudo
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Limpiar posibles bloques de código Markdown (```json ... ```)
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        
        # Buscar los límites del JSON por seguridad
        inicio = raw_text.find("{")
        fin = raw_text.rfind("}") + 1
        
        if inicio == -1:
            return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
            
        return json.loads(raw_text[inicio:fin])
        
    except Exception as e:
        print(f"❌ Error al procesar con Gemini: {e}")
        return {
            "tipo": "nota", 
            "descripcion": texto, 
            "monto": None, 
            "fecha_hora": None
        }
