import os
from datetime import datetime
import google.generativeai as genai
from groq import Groq
from database import SessionLocal, Transaccion, Recordatorio

# Configuración de APIs
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def procesar_mensaje_ia(texto, media_url, usuario):
    # Por ahora procesamos solo texto, si es audio manejamos el mensaje
    texto_a_procesar = "Nota de voz recibida (pendiente transcripción)" if media_url else texto

    prompt_sistema = f"""
    Eres un asistente contable y de agenda. Tu objetivo es interpretar mensajes y devolver un JSON estricto.
    Hoy es {datetime.now().strftime('%Y-%m-%d %H:%M')}.
    
    Si el usuario dice un gasto o ingreso, extrae: {{"tipo": "finanzas", "accion": "ingreso|egreso", "monto": float, "descripcion": "str"}}
    Si el usuario dice una cita o recordatorio, extrae: {{"tipo": "agenda", "evento": "str", "fecha": "YYYY-MM-DD HH:MM"}}
    Si el usuario pide un resumen, extrae: {{"tipo": "resumen", "periodo": "dia|mes"}}
    
    Solo responde el JSON, nada más. No agregues texto extra.
    """

    try:
        # Usamos Groq para entender la intención
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": texto_a_procesar}
            ],
            model="llama-3.3-70b-versatile",
            response_format={ "type": "json_object" }
        )
        
        import json
        datos = json.loads(chat_completion.choices[0].message.content)
        return ejecutar_accion(datos, usuario)

    except Exception as e:
        return f"Error en procesamiento de IA: {str(e)}"

def ejecutar_accion(datos, usuario):
    db = SessionLocal()
    try:
        if datos.get('tipo') == 'finanzas':
            nueva_trans = Transaccion(
                usuario=usuario,
                tipo=datos.get('accion'),
                monto=float(datos.get('monto', 0)),
                descripcion=datos.get('descripcion', 'Sin descripción')
            )
            db.add(nueva_trans)
            db.commit()
            return f"✅ Registrado: {datos.get('accion')} de ${datos.get('monto')} por {datos.get('descripcion')}."

        elif datos.get('tipo') == 'agenda':
            # Aquí estaba el error del paréntesis, ahora corregido:
            nuevo_rec = Recordatorio(
                usuario=usuario,
                contenido=datos.get('evento'),
                fecha_recordatorio=datetime.strptime(datos.get('fecha'), '%Y-%m-%d %H:%M')
            )
            db.add(nuevo_rec)
            db.commit()
            return f"📅 Agendado: '{datos.get('evento')}' para el {datos.get('fecha')}."

        elif datos.get('tipo') == 'resumen':
            return "📊 Función de resumen en desarrollo. ¡Pronto verás tus balances aquí!"

        return "Entendido, pero no pude clasificar la acción."
        
    except Exception as e:
        return f"Error al guardar en base de datos: {str(e)}"
    finally:
        db.close()
