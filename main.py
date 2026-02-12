import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import inicializar_db, SessionLocal, Recordatorio
from ia import procesar_mensaje_ia
from datetime import datetime
from twilio.rest import Client

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

@app.route("/check-reminders", methods=['GET'])
def check_reminders():
    # Esta ruta la llama el Cron-job externo
    db = SessionLocal()
    ahora = datetime.now()
    # Busca recordatorios pendientes cuya hora ya pasó
    pendientes = db.query(Recordatorio).filter(
        Recordatorio.estado == "pendiente",
        Recordatorio.fecha_recordatorio <= ahora
    ).all()
    
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    
    for rec in pendientes:
        client.messages.create(
            from_=os.getenv("TWILIO_NUMBER", "whatsapp:+14155238886"),
            body=f"⏰ RECORDATORIO: {rec.contenido}",
            to=rec.usuario
        )
        rec.estado = "completado"
    
    db.commit()
    db.close()
    return "OK", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
