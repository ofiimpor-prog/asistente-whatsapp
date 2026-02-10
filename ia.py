def interpretar_mensaje(texto):
    # La URL con el nombre exacto del modelo que Google espera en v1
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}

    prompt = f"""
    Responde SOLO JSON. 
    Tipos: ingreso, egreso, cita, recordatorio, nota, saludo.
    Mensaje: "{texto}"
    Formato: {{"tipo": "", "descripcion": "", "monto": null, "fecha_hora": null}}
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()

        # Si esto vuelve a dar 404, imprimiremos TODA la respuesta para ver qué modelos tienes
        if "error" in data:
            print(f"DEBUG GOOGLE: {data}")
            raise ValueError(data["error"]["message"])

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Limpieza básica de JSON
        inicio = raw.find("{")
        fin = raw.rfind("}") + 1
        return json.loads(raw[inicio:fin])

    except Exception as e:
        print("⚠️ Fallo Gemini:", e)
        return {"tipo": "nota", "descripcion": texto, "monto": None, "fecha_hora": None}
