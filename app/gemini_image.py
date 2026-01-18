# app/gemini_image.py
import os
from pathlib import Path

def generar_flyer_con_gemini(producto: dict, out_path: str) -> str:
    """
    Genera un flyer PNG usando Gemini (texto-a-imagen).
    Si Gemini no está disponible para imagen en tu cuenta, levanta excepción.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en .env")

    # Intento con SDK nuevo (google-genai). Si no está, se verá en la excepción.
    from google import genai

    client = genai.Client(api_key=api_key)

    nombre = producto.get("nombre", "Producto")
    precio = producto.get("precio", "")
    # Podés ajustar el estilo acá
    prompt = f"""
Diseñá un flyer cuadrado 1080x1080 para redes sociales.
Estilo: moderno, minimalista, fondo claro, acentos verdes, tipografía grande y legible.
Debe incluir:
- Título corto del producto: "{nombre}"
- Precio destacado: "₲ {precio}"
- Sello pequeño: "Katueté Importados"
- Espacio para foto del producto (centrada y grande)
No pongas texto chiquito. Que todo sea legible desde el celular.
"""

    # ⚠️ MODELO DE IMAGEN:
    # Dependiendo de tu cuenta, el modelo puede variar.
    # Si falla por "model not found" o "not enabled", se maneja en el caller como fallback.
    resp = client.models.generate_images(
        model="imagen-3.0-generate-001",   # si falla, cambiamos al modelo disponible en tu cuenta
        prompt=prompt,
        size="1024x1024",                  # algunos modelos no aceptan 1080 exacto
        number_of_images=1
    )

    # Guardar la primera imagen
    img_bytes = resp.generated_images[0].image_bytes
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(img_bytes)

    return out_path
