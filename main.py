import os
from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from ia import interpretar_mensaje, transcribir_audio
from db import init_db, registrar_finanza, registrar_agenda, registrar_nota

app = FastAPI()
init_db()

TU_NUMERO = os.getenv("TU_NUMERO_PERSONAL")

@app.get("/")
def home(): return {"status": "OK"}

@app.post("/whatsapp")
async def whatsapp(request: Request):
    form = await request.form()
    from_number = form.get("From", "")
    body = form.get("Body", "").strip()
    media_url = form.get("MediaUrl0")

    if TU_NUMERO and TU_NUMERO not in from_number:
        return Response(content="Prohibido", status_code=403)

    texto = transcribir_audio(media_url, os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")) if media_url else body
    
    data = interpretar_mensaje(texto)
    tipo = data.get("tipo")
    monto = data.get("monto")
    desc = data.get("descripcion", texto)

    # Lógica de respuesta
    if tipo == "ingreso" and monto: msg = registrar_finanza("INGRESO", monto, desc)
    elif tipo == "egreso" and monto: msg = registrar_finanza("EGRESO", monto, desc)
    elif tipo in ["cita", "recordatorio"]: msg = registrar_agenda(tipo, desc, data.get("fecha_hora") or "Pendiente")
    elif tipo == "saludo": msg = "👋 ¡Hola! ¿Qué quieres registrar hoy?"
    else: msg = registrar_nota(desc)

    twiml = MessagingResponse()
    twiml.message(msg)
    return Response(content=str(twiml), media_type="application/xml")
