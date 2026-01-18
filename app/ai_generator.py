from openai import OpenAI

client = OpenAI()

def generar_texto(nombre_original: str, precio: str):
    prompt = f"""
Creá un mensaje listo para enviar por WhatsApp para este producto:

Producto: {nombre_original}
Precio: ₲ {precio}

Tenés que usar **UNO SOLO** de los siguientes formatos.
Elegí el formato de manera ALEATORIA en cada generación.

========================
FORMATO A
========================
[Emoji + Nombre en negrita]

[Línea descriptiva 1]
[Línea descriptiva 2]

💰🔥 *PRECIO ESPECIAL* 🔥💰
👉👉 *₲ {precio}* 👈👈

📦 Katueté Importados

========================
FORMATO B
========================
[Emoji][Emoji] *Nombre atractivo del producto*

✨ [Beneficio principal]
🎵 [Uso o ventaja destacada]

💸 *₲ {precio}*
📦 Katueté Importados

========================
FORMATO C
========================
🔥 *Nombre comercial impactante* 🔥

✔️ [Característica clave]
✔️ [Característica secundaria]

💰 *Precio: ₲ {precio}*
📦 Katueté Importados

========================

REGLAS OBLIGATORIAS:
- Usar emojis
- Usar *negritas* compatibles con WhatsApp
- Máximo 6 líneas visibles
- Mensaje bien espaciado y estético
- Tono moderno, vendedor, producto importado
- No repetir exactamente frases entre productos
- No explicar nada
- Devolver SOLO el mensaje final
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Sos un experto en marketing digital para ventas por WhatsApp."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.95,   # 🔥 más creatividad
        max_tokens=220
    )

    return response.choices[0].message.content.strip()
