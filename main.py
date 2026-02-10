import os
from fastapi import FastAPI, Request
from twilio.twiml.messaging_response import MessagingResponse
from ia import interpretar_mensaje, transcribir_audio

app = FastAPI()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    texto = form.get("Body", "").strip()
    num_media = int(form.get("NumMedia", 0))

    # 📌 Si viene audio
    if num_media > 0:
        media_url = form.get("MediaUrl0")
        texto = transcribir_audio(media_url, TWILIO_SID, TWILIO_TOKEN)
        if not texto:
            return responder("❌ No pude entender el audio")

    # 🧠 Interpretar con IA
    resultado = interpretar_mensaje(texto)

    tipo = resultado.get("tipo")
    descripcion = resultado.get("descripcion", "")
    monto = resultado.get("monto")

    # 🗣️ Respuestas dinámicas
    if tipo == "ingreso":
        respuesta = f"💰 Ingreso registrado: {descripcion} (${monto})"
    elif tipo == "egreso":
        respuesta = f"💸 Gasto registrado: {descripcion} (${monto})"
    elif tipo == "cita":
        respuesta = f"📅 Cita registrada: {descripcion}"
    elif tipo == "recordatorio":
        respuesta = f"⏰ Recordatorio guardado: {descripcion}"
    elif tipo == "saludo":
        respuesta = "👋 Hola, dime qué quieres registrar"
    else:
        respuesta = f"📝 Nota guardada: {descripcion}"

    return responder(respuesta)

def responder(texto):
    resp = MessagingResponse()
    resp.message(texto)
    return str(resp)

@app.get("/")
def root():
    return {"status": "ok"}
