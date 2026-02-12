import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import SessionLocal, Recordatorio, inicializar_db
from ia import procesar_mensaje_ia
from datetime import datetime
from twilio.rest import Client

# 1. Configuración de la App
app = Flask(__name__)
inicializar_db()

# Configuración de números (Asegúrate de tener estas variables en Render o se usarán estos defaults)
# Tu número personal para finanzas y avisos de sistema
MI_NUMERO = "whatsapp:+56992797684" 
# El número donde llegan las citas agendadas
NUMERO_DESTINO_CITAS = "whatsapp:+56962959718"

@app.route("/", methods=['GET'])
def home():
    return "Asistente de Andrés: Activo y en línea 🚀", 200

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    msg = request.values.get('Body', '')
    sender = request.values.get('From', '')
    media = request.values.get('MediaUrl0') 
    
    # La IA procesa el mensaje
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

        # 1. Recordatorio de mantenimiento (Lunes y Jueves a las 10:00 AM)
        if ahora.weekday() in [0, 3] and ahora.hour == 10 and ahora.minute < 5:
            client.messages.create(
                from_=twilio_number,
                body="🔔 *RECORDATORIO DE SISTEMA*\n\nAndrés, hoy toca renovar el Sandbox de Twilio.\nEnvía *join late-nothing* desde el celular de citas.",
                to=MI_NUMERO
            )

        # 2. Buscar recordatorios para enviar
        # Filtramos por estado pendiente y que la hora ya haya llegado o pasado
        pendientes = db.query(Recordatorio).filter(
            Recordatorio.estado == "pendiente",
            Recordatorio.fecha_recordatorio <= ahora
        ).all()
        
        enviados = 0
        for rec in pendientes:
            try:
                # Si el registro no tiene el prefijo whatsapp:, se lo ponemos
                destinatario = rec.usuario if "whatsapp:" in rec.usuario else f"whatsapp:{rec.usuario}"
                
                client.messages.create(
                    from_=twilio_number, 
                    body=f"⏰ *RECORDATORIO:* {rec.contenido}", 
                    to=destinatario
                )
                rec.estado = "completado"
                enviados += 1
            except Exception as e:
                print(f"Error enviando mensaje: {e}")

        db.commit()
        return f"Procesados {enviados} recordatorios correctamente.", 200
        
    except Exception as e:
        db.rollback()
        return f"Error en el sistema: {str(e)}", 500
    finally:
        db.close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
