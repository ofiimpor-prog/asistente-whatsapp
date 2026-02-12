import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import inicializar_db, SessionLocal, Recordatorio
from ia import procesar_mensaje_ia, generar_reporte_automatico # Nueva función
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
    db = SessionLocal()
    ahora = datetime.now()
    
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    mi_numero = os.getenv("TU_NUMERO_PERSONAL") # Tu número guardado en Render
    twilio_number = os.getenv("TWILIO_NUMBER", "whatsapp:+14155238886")

    # 1. REVISAR RECORDATORIOS (Lo que ya tenías)
    pendientes = db.query(Recordatorio).filter(
        Recordatorio.estado == "pendiente",
        Recordatorio.fecha_recordatorio <= ahora
    ).all()
    
    for rec in pendientes:
        client.messages.create(from_=twilio_number, body=f"⏰ RECORDATORIO: {rec.contenido}", to=rec.usuario)
        rec.estado = "completado"

    # 2. REPORTES AUTOMÁTICOS (Nueva lógica)
    # Domingo a las 20:00 (o la primera vez que pase el cron después de esa hora)
    if ahora.weekday() == 6 and ahora.hour == 20 and ahora.minute < 10:
        reporte = generar_reporte_automatico(mi_numero, "semana")
        client.messages.create(from_=twilio_number, body=f"🗓️ REPORTE SEMANAL AUTOMÁTICO\n{reporte}", to=mi_numero)

    # Fin de mes (Día 1 a las 08:00 AM sobre el mes anterior)
    if ahora.day == 1 and ahora.hour == 8 and ahora.minute < 10:
        reporte = generar_reporte_automatico(mi_numero, "mes")
        client.messages.create(from_=twilio_number, body=f"🏁 BALANCE MENSUAL AUTOMÁTICO\n{reporte}", to=mi_numero)

    db.commit()
    db.close()
    return "OK", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
