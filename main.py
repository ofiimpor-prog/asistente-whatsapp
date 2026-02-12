import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import inicializar_db
from ia import procesar_mensaje_ia

app = Flask(__name__)

# Al arrancar, nos aseguramos de que las tablas existan en PostgreSQL
with app.app_context():
    try:
        inicializar_db()
    except Exception as e:
        print(f"Error al conectar la base de datos: {e}")

@app.route("/", methods=['GET'])
def home():
    return "Asistente Financiero para +56992797684 Operativo", 200

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    # Capturamos la información de Twilio
    incoming_msg = request.values.get('Body', '')
    sender_number = request.values.get('From', '')
    media_url = request.values.get('MediaUrl0') 

    # Pasamos todo al cerebro (ia.py)
    respuesta = procesar_mensaje_ia(incoming_msg, media_url, sender_number)

    # Devolvemos la respuesta a WhatsApp
    resp = MessagingResponse()
    resp.message(respuesta)
    return str(resp)

if __name__ == "__main__":
    # Esto solo se usa si corres el archivo localmente
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
