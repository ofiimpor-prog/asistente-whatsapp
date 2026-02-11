import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import guardar_registro, obtener_resumen_gastos
from ia import interpretar_mensaje, transcribir_audio

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    media_url = request.values.get('MediaUrl0')
    
    response = MessagingResponse()

    # 1. Manejo de Audio
    if media_url:
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        texto_audio = transcribir_audio(media_url, twilio_sid, twilio_token)
        if texto_audio:
            incoming_msg = texto_audio
        else:
            response.message("No pude procesar el audio. ¿Podrías repetirlo?")
            return str(response)

    # 2. IA interpreta la intención
    datos = interpretar_mensaje(incoming_msg)
    intent = datos.get("tipo", "nota")
    
    # 3. DETECTOR DE INFORMES (Mejorado)
    # Si el mensaje contiene cualquiera de estas palabras, saltamos directo al informe
    palabras_informe = ["resumen", "balance", "informe", "gastado", "cuánto", "gastos", "ingresos"]
    pide_informe = any(p in incoming_msg.lower() for p in palabras_informe)

    if intent == "consulta" or pide_informe:
        try:
            resumen = obtener_resumen_gastos()
            msg_resumen = (
                f"📊 *INFORME DE FINANZAS*\n\n"
                f"💰 *Ingresos:* ${resumen['total_ingresos']}\n"
                f"💸 *Gastos:* ${resumen['total_egresos']}\n"
                f"📉 *Balance:* ${resumen['balance']}\n\n"
                f"*Últimos movimientos:*\n{resumen['detalles']}"
            )
            response.message(msg_resumen)
            return str(response) 
        except Exception as e:
            print(f"Error en resumen: {e}")
            response.message("Error al calcular el balance. Verifica la base de datos.")
            return str(response)

    # 4. LÓGICA DE REGISTRO
    try:
        guardar_registro(
            tipo=intent,
            descripcion=datos.get("descripcion", ""),
            monto=datos.get("monto"),
            fecha_hora=datos.get("fecha_hora")
        )

        if intent == "ingreso":
            response.message(f"💰 *INGRESO* guardado: ${datos['monto']} - {datos['descripcion']}")
        elif intent == "egreso":
            response.message(f"💸 *EGRESO* registrado: ${datos['monto']} - {datos['descripcion']}")
        elif intent == "saludo":
            response.message("¡Hola Andrés! Soy tu asistente. Pídeme un 'resumen' o registra un gasto.")
        else:
            # Si no es ninguna de las anteriores, lo guardamos como nota
            response.message(f"📝 *Nota guardada:* {incoming_msg}")
            
    except Exception as e:
        print(f"Error al guardar: {e}")
        response.message("Lo siento, no pude procesar ese mensaje.")

    return str(response)

if __name__ == "__main__":
    app.run(port=10000)
