import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import guardar_registro, obtener_resumen_gastos
from ia import interpretar_mensaje, transcribir_audio

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    sender_number = request.values.get('From', '')
    media_url = request.values.get('MediaUrl0')
    
    # 1. Manejo de Audio
    if media_url:
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        texto_audio = transcribir_audio(media_url, twilio_sid, twilio_token)
        if texto_audio:
            incoming_msg = texto_audio
        else:
            res = MessagingResponse()
            res.message("No pude procesar el audio. ¿Podrías repetirlo?")
            return str(res)

    # 2. IA interpreta la intención
    datos = interpretar_mensaje(incoming_msg)
    intent = datos.get("tipo", "nota")
    
    response = MessagingResponse()

    # 3. LÓGICA DE INFORMES (Nueva)
    if intent == "consulta" or "resumen" in incoming_msg.lower() or "informe" in incoming_msg.lower():
        resumen = obtener_resumen_gastos()
        # Le enviamos el resumen crudo a la IA para que lo redacte bonito
        # (Por ahora lo enviamos directo, luego podemos mejorar la redacción)
        msg_resumen = (
            f"📊 *INFORME DE FINANZAS*\n\n"
            f"💰 *Ingresos:* ${resumen['total_ingresos']}\n"
            f"💸 *Gastos:* ${resumen['total_egresos']}\n"
            f"📉 *Balance:* ${resumen['balance']}\n\n"
            f"Últimos movimientos:\n" + resumen['detalles']
        )
        response.message(msg_resumen)
        return str(res)

    # 4. LÓGICA DE REGISTRO (La que ya tenías)
    guardar_registro(
        tipo=intent,
        descripcion=datos.get("descripcion", ""),
        monto=datos.get("monto"),
        fecha_hora=datos.get("fecha_hora")
    )

    # Respuestas personalizadas
    if intent == "ingreso":
        response.message(f"💰 *INGRESO* guardado: ${datos['monto']} - {datos['descripcion']}")
    elif intent == "egreso":
        response.message(f"💸 *EGRESO* registrado: ${datos['monto']} - {datos['descripcion']}")
    elif intent == "saludo":
        response.message("¡Hola Andrés! Soy tu asistente IA. ¿En qué puedo ayudarte hoy?")
    else:
        response.message(f"📝 Nota guardada: {incoming_msg}")

    return str(response)

if __name__ == "__main__":
    app.run(port=10000)
