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

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    from_number = form.get("From", "")
    body = form.get("Body", "")
    media_url = form.get("MediaUrl0")

    twiml = MessagingResponse()

    # Seguridad
    if TU_NUMERO and TU_NUMERO not in from_number:
        twiml.message("⛔ No autorizado.")
        return Response(content=str(twiml), media_type="application/xml")

    # Obtener texto
    if media_url:
        texto = transcribir_audio(
            media_url,
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
    else:
        texto = body

    if not texto:
        twiml.message("⚠️ No recibí contenido válido.")
        return Response(content=str(twiml), media_type="application/xml")

    data = interpretar_mensaje(texto)
    tipo = data.get("tipo")
    descripcion = data.get("descripcion", texto)
    monto = data.get("monto")
    fecha_hora = data.get("fecha_hora", "Pendiente")

    try:
        if tipo in ["ingreso", "egreso"]:
            if monto is not None:
                msg = registrar_finanza(
                    tipo.upper(),
                    float(monto),
                    descripcion
                )
                twiml.message(f"💰 {msg}")
            else:
                twiml.message(
                    "❌ No detecté el monto. Ejemplo: 'Gasto 5000 en pan'"
                )

        elif tipo in ["cita", "recordatorio"]:
            msg = registrar_agenda(tipo, descripcion, fecha_hora)
            twiml.message(f"🗓️ {msg}")

        elif tipo == "saludo":
            twiml.message(
                "👋 Hola, dime un gasto, ingreso, cita o envíame un audio."
            )

        else:
            msg = registrar_nota(descripcion)
            twiml.message(msg)

    except Exception as e:
        print("Error general:", e)
        twiml.message("⚠️ Ocurrió un error. Intenta nuevamente.")

    return Response(content=str(twiml), media_type="application/xml")

@app.get("/")
def health():
    return {"status": "Activo"}
