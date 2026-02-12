import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import SessionLocal, Recordatorio, inicializar_db
from ia import procesar_mensaje_ia, generar_reporte_automatico
from datetime import datetime
from twilio.rest import Client

app = Flask(__name__)

# Iniciamos la base de datos (ya creada correctamente)
inicializar_db()

@app.route("/", methods=['GET'])
def home():
    return "Asistente Financiero Operativo", 200

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
        mi_numero = os.getenv("TU_NUMERO_PERSONAL")
        twilio_number = os.getenv("TWILIO_NUMBER", "whatsapp:+14155238886")

        # 1. Procesar Recordatorios
        pendientes = db.query(Recordatorio).filter(
            Recordatorio.estado == "pendiente",
            Recordatorio.fecha_recordatorio <= ahora
        ).all()
        
        for rec in pendientes:
            client.messages.create(from_=twilio_number, body=f"⏰ RECORDATORIO: {rec.contenido}", to=rec.usuario)
            rec.estado = "completado"

        # 2. Reportes Automáticos (Domingos 20:00)
        if ahora.weekday() == 6 and ahora.hour == 20 and ahora.minute < 10:
            reporte = generar_reporte_automatico(mi_numero, "semana")
            client.messages.create(from_=twilio_number, body=f"🗓️ REPORTE SEMANAL AUTOMÁTICO\n{reporte}", to=mi_numero)

        db.commit()
        return "OK", 200
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}", 500
    finally:
        db.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
