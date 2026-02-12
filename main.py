@app.route("/check-reminders", methods=['GET'])
def check_reminders():
    db = SessionLocal()
    try:
        ahora = datetime.now()
        print(f"Revisando recordatorios a las: {ahora}") # Esto saldrá en tus logs
        
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        twilio_number = os.getenv("TWILIO_NUMBER")

        # Buscamos TODO lo pendiente que ya debería haber salido (<= ahora)
        pendientes = db.query(Recordatorio).filter(
            Recordatorio.estado == "pendiente",
            Recordatorio.fecha_recordatorio <= ahora
        ).all()
        
        enviados = 0
        for rec in pendientes:
            try:
                # Forzamos el formato whatsapp: si no lo tiene
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
        mensaje_final = f"Procesados {enviados} recordatorios."
        print(mensaje_final)
        return mensaje_final, 200
        
    except Exception as e:
        db.rollback()
        print(f"Error crítico: {e}")
        return f"Error: {e}", 500
    finally:
        db.close()
