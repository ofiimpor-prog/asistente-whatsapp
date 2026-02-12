import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import inicializar_db, SessionLocal
from ia import procesar_mensaje_ia

app = Flask(__name__)

# Creamos las tablas al iniciar
inicializar_db()

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    incoming_msg = request.values.get('Body', '')
    sender_number = request.values.get('From')
    media_url = request.values.get('MediaUrl0') # Para las notas de voz

    # Lógica de respuesta
    respuesta_ia = procesar_mensaje_ia(incoming_msg, media_url, sender_number)

    resp = MessagingResponse()
    resp.message(respuesta_ia)
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
