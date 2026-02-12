import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import inicializar_db
from ia import procesar_mensaje_ia

app = Flask(__name__)

with app.app_context():
    inicializar_db()

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    msg = request.values.get('Body', '')
    sender = request.values.get('From', '')
    media = request.values.get('MediaUrl0') 
    
    respuesta = procesar_mensaje_ia(msg, media, sender)

    resp = MessagingResponse()
    resp.message(respuesta)
    return str(resp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
