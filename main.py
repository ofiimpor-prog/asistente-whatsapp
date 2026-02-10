import os
from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from ai import interpretar_mensaje, transcribir_audio
from db import init_db, registrar_finanza, registrar_agenda, registrar_nota

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

TU_NUMERO = os.getenv("TU_NUMERO_PERSONAL")

# ENDPOINT PARA RENDER (Quita el error 404)
@app.get("/")
async def root():
    return {"status": "online", "asistente": "Gemini + Groq activo"}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    from_number = form.get("From", "")
    media_url = form.get("MediaUrl0")
    
    twiml = MessagingResponse()

    if TU_NUMERO and TU_NUMERO not in from_number:
        twiml.message("⛔ No autorizado.")
        return Response(content=str(twiml), media_type="application/xml")

    texto = transcribir_audio(media_url, os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")) if media_url else form.get("Body", "")

    if not texto:
        return Response(content=str(twiml), media_type="application/xml")

    data = interpretar_mensaje(texto)
    tipo = data.get("tipo")
    
    try:
        if tipo in ["ingreso", "egreso"]:
            monto = data.get("monto")
            if monto:
                msg = registrar_finanza(tipo.upper(), float(monto), data.get("descripcion", texto))
                twiml.message(f"💰 {msg}")
            else:
                twiml.message("❌ No detecté el monto. Ejemplo: 'Gasto 5000 en pan'")

        elif tipo in ["cita", "recordatorio"]:
            msg = registrar_agenda(tipo, data.get("descripcion", texto), data.get("fecha_hora", "Pendiente"))
            twiml.message(f"🗓️ {msg}")

        elif tipo == "saludo":
            twiml.message("👋 ¡Hola! Estoy operativo. ¿Qué deseas registrar hoy?")

        else:
            msg = registrar_nota(texto)
            twiml.message(msg)

    except Exception as e:
        print(f"Error en main: {e}")
        twiml.message("⚠️ Ocurrió un error al procesar tu solicitud.")

    return Response(content=str(twiml), media_type="application/xml")
