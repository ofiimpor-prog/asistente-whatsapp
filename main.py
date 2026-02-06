from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from ai import get_ai_response
from db import create_table, save_message

app = FastAPI()

# --- CONFIGURACIÓN DE NOTIFICACIONES ---
# Asegúrate de poner tus códigos AC... y Token reales entre las comillas
TWILIO_ACCOUNT_SID = 'POR_CONFIGURAR'
TWILIO_AUTH_TOKEN = 'POR_CONFIGURAR'
TU_NUMERO_PERSONAL = 'whatsapp:+56992797684'  # Tu número guardado
NUMERO_TWILIO = 'whatsapp:+14155238886'       # Número del Sandbox de Twilio
# ---------------------------------------

# Crear tabla al iniciar
create_table()

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        # 1. Recibir datos de Twilio
        form = await request.form()
        body = form.get("Body", "").strip()
        phone = form.get("From", "")

        print(f"📱 Mensaje de {phone}: {body}")

        # 2. Obtener respuesta de ai.py
        respuesta = get_ai_response(body)

        # 3. Guardar en Base de Datos
        save_message(phone, body, respuesta[:30].replace('\n', ' '))

        # 4. Lógica de Alerta para el Administrador
        # Si el usuario escribe 4, o palabras clave de ayuda
        palabras_ayuda = ["4", "persona", "humano", "ayuda"]
        if any(palabra in body.lower() for palabra in palabras_ayuda):
            try:
                client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                client.messages.create(
                    from_=NUMERO_TWILIO,
                    body=f"🚨 *ALERTA:* El cliente {phone} quiere hablar contigo. Mensaje: {body}",
                    to=TU_NUMERO_PERSONAL
                )
                print(f"✅ Notificación enviada con éxito a {TU_NUMERO_PERSONAL}")
            except Exception as e_notif:
                print(f"⚠️ Error al enviar notificación: {e_notif}")

        # 5. Responder al cliente
        twilio_response = MessagingResponse()
        twilio_response.message(respuesta)

        return Response(
            content=str(twilio_response),
            media_type="application/xml"
        )
        
    except Exception as e:
        print(f"❌ Error crítico en el Webhook: {e}")
        return Response(content="Error", status_code=500)