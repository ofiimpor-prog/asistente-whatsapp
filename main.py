import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import SessionLocal, Recordatorio, inicializar_db
from ia import procesar_mensaje_ia, generar_reporte_automatico
from datetime import datetime
from twilio.rest import Client

# 1. Definimos la aplicación PRIMERO
app = Flask(__name__)

# 2. Iniciamos la base de datos
inicializar_db()

@app.route("/", methods=['GET'])
def home():
    return "Asistente Financiero y de Citas Activo 🚀", 200

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    msg = request.values.get('Body', '')
    sender = request.values.get('From', '')
    media = request.values.get('MediaUrl0') 
    respuesta = procesar_mensaje_ia(msg, media, sender)
    resp = MessagingResponse()
    resp.message(respuesta)
    return str(resp)

@app.route("/check-reminders", methods=['GET'])
def check_reminders():
    db = SessionLocal()
    try:
        ahora = datetime.now()
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        twilio_number = os.getenv("TWILIO_NUMBER", "whatsapp:+14155238886")

        # Buscamos todo lo pendiente que ya debería haber salido (<= ahora)
        pendientes = db.query(Recordatorio).filter(
            Recordatorio.estado == "pendiente",
            Recordatorio.fecha_recordatorio <= ahora
        ).all()
        
        enviados = 0
        for rec in pendientes:
            try:
                # Aseguramos formato correcto del número
                to_number = rec.usuario if "whatsapp:" in rec.usuario else f"whatsapp:{rec.usuario}"
                
                client.messages.create(
                    from_=twilio_number, 
                    body=f"⏰ *RECORDATORIO:* {rec.contenido}", 
                    to=to_number
                )
                rec.estado = "completado"
                enviados += 1
            except Exception as e:
                print(f"Error enviando WhatsApp: {e}")

        db.commit()
        return f"Procesados {enviados} recordatorios.", 200
        
    except Exception as e:
        db.rollback()
        return f"Error crítico: {str(e)}", 500
    finally:
        db.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
