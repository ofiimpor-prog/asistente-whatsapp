import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import SessionLocal, Recordatorio, inicializar_db, Base, engine
from ia import procesar_mensaje_ia, generar_reporte_automatico
from datetime import datetime
from twilio.rest import Client

app = Flask(__name__)

# --- LINEA DE LIMPIEZA TEMPORAL ---
# Esto borrará las tablas viejas para que se creen de nuevo con la columna 'contenido'
Base.metadata.drop_all(bind=engine) 
# ----------------------------------

inicializar_db()

@app.route("/", methods=['GET'])
def home():
    return "Asistente Operativo", 200

@app.route("/check-reminders", methods=['GET'])
def check_reminders():
    db = SessionLocal()
    try:
        ahora = datetime.now()
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        mi_numero = os.getenv("TU_NUMERO_PERSONAL")
        twilio_number = os.getenv("TWILIO_NUMBER", "whatsapp:+14155238886")

        pendientes = db.query(Recordatorio).filter(
            Recordatorio.estado == "pendiente",
            Recordatorio.fecha_recordatorio <= ahora
        ).all()
        
        for rec in pendientes:
            client.messages.create(from_=twilio_number, body=f"⏰ RECORDATORIO: {rec.contenido}", to=rec.usuario)
            rec.estado = "completado"

        db.commit()
        return "OK", 200
    except Exception as e:
        return f"Error: {e}", 500
    finally:
        db.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
