def get_ai_response(user_message: str) -> str:
    # Limpiamos el mensaje (quitamos espacios y pasamos a minúsculas)
    msg = user_message.strip().lower()

    if msg in ["1", "información", "informacion"]:
        return "📄 *Información:* Somos una empresa dedicada a crear asistentes inteligentes con Python. ¿Te gustaría saber más?"
    
    elif msg in ["2", "horarios"]:
        return "⏰ *Horarios:* Atendemos de Lunes a Viernes de 09:00 a 18:00 hrs. ¡Escríbenos en ese bloque!"
    
    elif msg in ["3", "contacto"]:
        return "📞 *Contacto:* Puedes llamarnos al +56912345678 o enviarnos un correo a soporte@tuempresa.com."
    
    elif msg in ["4", "hablar", "persona"]:
        return "🧑‍💻 *Humano:* He avisado al equipo. Un agente se pondrá en contacto contigo a la brevedad."
    
    else:
        # Si no marca una opción válida, mostramos el menú de nuevo
        return (
            "Esa opción no la conozco 🤔. Por favor, elige una:\n\n"
            "1️⃣ Información\n"
            "2️⃣ Horarios\n"
            "3️⃣ Contacto\n"
            "4️⃣ Hablar con una persona"
        )