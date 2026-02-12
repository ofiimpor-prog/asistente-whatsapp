import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from ia import procesar_mensaje_ia

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home():
    return "Asistente de WhatsApp Operativo", 200

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    # Obtener datos de Twilio
    incoming_msg = request.values.get('Body', '').lower()
    media_url = request.values.get('MediaUrl0') # Para notas de voz
    sender_number = request.values.get('From')

    # Si hay audio, enviamos la URL, si no, el texto
    contenido = media_url if media_url else incoming_msg
    es_audio = True if media_url else False

    # Procesar con la IA
    respuesta_ia = procesar_mensaje_ia(contenido, es_audio, sender_number)

    # Responder a través de Twilio
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(respuesta_ia)
    
    return str(resp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
