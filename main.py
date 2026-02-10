import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from twilio.twiml.messaging_response import MessagingResponse
import requests

from ia import transcribir_audio, interpretar_mensaje
from db import guardar_registro

app = FastAPI()

# =========================
# VARIABLES DE ENTORNO
# =========================
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# =========================
# HEALTHCHECK
# =========================
@app.get("/")
def healthcheck():
    return {
        "status": "online",
        "asistente": "Gemini + Groq activo"
    }

# =========================
# WEBHOOK WHATSAPP
# =========================
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):

    try:
        form = await request.form()
        mensaje = form.get("Body", "").strip()
        audio_url = form.get("MediaUrl0")
