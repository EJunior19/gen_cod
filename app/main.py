from dotenv import load_dotenv
load_dotenv()
from app.api_client import get_products
from app.selector import seleccionar_productos
from app.ai_generator import generar_texto
from app.utils import obtener_precio_base, calcular_precio_con_margen
from app.web_view import iniciar_web


def build_data():
    # 1️⃣ Obtener productos de la API
    productos_api = get_products(30)

    # 2️⃣ Seleccionar productos SIN repetir (cache 3 días)
    seleccionados = seleccionar_productos(productos_api, 3)

    productos_finales = []

    for p in seleccionados:
        # 3️⃣ Obtener precio base correcto
        precio_base = obtener_precio_base(p)
        if precio_base <= 0:
            continue

        # 4️⃣ Aplicar margen comercial
        precio_final = calcular_precio_con_margen(precio_base)

        # 5️⃣ Formato PY
        precio_str = f"{precio_final:,}".replace(",", ".")

        # 6️⃣ Mensaje IA WhatsApp
        texto_whatsapp = generar_texto(
            nombre_original=p["name"],
            precio=precio_str
        )

        # 7️⃣ Armar producto final
        productos_finales.append({
            "nombre": p["name"],
            "descripcion": texto_whatsapp,
            "precio": precio_str,
            "imagen": p["images"][0]["src"],
            "sku": p.get("sku") or str(p.get("id")),
            "texto_whatsapp": texto_whatsapp
        })

    return productos_finales, ""


# 🔥 ESTA LÍNEA ES LA CLAVE PARA GUNICORN
app = iniciar_web(build_data)

if __name__ == "__main__":
    # Para desarrollo local
    app.run(host="127.0.0.1", port=5000, debug=True)

