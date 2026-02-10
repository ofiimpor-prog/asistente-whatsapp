import os
import json
import requests
from groq import Groq
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Inicializar clientes
# Forzamos la configuración para evitar el error de versión v1beta
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
                transcription = groq_client.audio.transcriptions.create(
                    file=(temp_file, audio.read()),
                    model="whisper-large-v3",
                    response_format="text"
                )
            if os.path.exists(temp_file): os.remove(temp_file)
            return transcription.strip()
    except Exception as e:
        if os.path.exists(temp_file): os.remove(temp_file)
        print(f"Error audio: {e}")
    return None

def interpretar_mensaje(texto):
    # Prompt optimizado para evitar que la IA divague
    prompt = f"""Analiza este mensaje y responde ÚNICAMENTE con un JSON.
    Tipos: 'ingreso', 'egreso', 'cita', 'recordatorio', 'nota', 'saludo'.
    Formato: {{"tipo": "", "descripcion": "", "monto": null, "fecha_hora": ""}}
    Mensaje: "{texto}" """
    
    try:
        # Usamos específicamente 'gemini-1.5-flash' sin prefijos extraños
        response = client_gemini.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        
        raw = response.text.strip()
        # Buscamos el JSON dentro de la respuesta por si Gemini agrega ```json ... ```
        inicio = raw.find("{")
        fin = raw.rfind("}") + 1
        
        if inicio == -1:
            raise ValueError("No se encontró JSON")
            
        return json.loads(raw[inicio:fin])
        
    except Exception as e:
        # Imprimimos el error real en los logs de Render para verlo
        print(f"Error detectado en Gemini: {e}")
        return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
