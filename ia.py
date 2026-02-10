import os
import json
import requests
from groq import Groq
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Inicializar clientes forzando la API v1 (la estable de 2026)
client_gemini = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'} 
)
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
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return result.strip()
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        print("Error audio:", e)
        return None

def interpretar_mensaje(texto):
    prompt = f"Analiza y responde SOLO JSON: {{'tipo': 'ingreso/egreso/cita/recordatorio/nota/saludo', 'descripcion': '', 'monto': null, 'fecha_hora': ''}}. Mensaje: '{texto}'"
    
    try:
        # Usamos el nombre base del modelo
        response = client_gemini.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        
        raw = response.text.strip()
        inicio = raw.find("{")
        fin = raw.rfind("}") + 1
        
        if inicio == -1:
            return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": ""}
            
        return json.loads(raw[inicio:fin])

    except Exception as e:
        print(f"❌ Error Gemini corregido: {e}")
        return {
            "tipo": "nota",
            "descripcion": texto,
            "monto": None,
            "fecha_hora": ""
        }
