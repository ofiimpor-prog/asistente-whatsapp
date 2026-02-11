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
    
    # 3. LÓGICA DE INFORMES
    # Agregamos una validación extra para que sea más sensible a tu pedido
    palabras_clave = ["resumen", "balance", "informe", "gastado", "cuánto tengo"]
    es_consulta = any(palabra in incoming_msg.lower() for palabra in palabras_clave)

    if intent == "consulta" or es_consulta:
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
            return str(response) # <-- AQUÍ ESTABA EL ERROR (decía str(res))
        except Exception as e:
            print(f"Error generando resumen: {e}")
            response.message("Tuve un problema al calcular el resumen. ¿Lo intentamos de nuevo?")
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
            response.message("¡Hola Andrés! Soy tu asistente IA con Llama 3.3. ¿Qué registro o informe necesitas?")
        else:
            response.message(f"📝 *Nota guardada:* {incoming_msg}")
            
    except Exception as e:
        print(f"Error al guardar: {e}")
        response.message("No pude guardar el registro, pero lo anotaré como una nota temporal.")

    return str(response)

if __name__ == "__main__":
    app.run(port=10000)
