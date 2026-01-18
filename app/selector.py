import random
from app.cache import fue_usado, marcar_usado

def seleccionar_productos(productos, cantidad: int = 3, dias_cache: int = 3):
    productos = list(productos or [])
    random.shuffle(productos)

    seleccionados = []

    for p in productos:
        product_id = str(p.get("id") or p.get("sku"))
        if not product_id:
            continue

        if fue_usado(product_id, dias_cache):
            continue

        seleccionados.append(p)
        marcar_usado(product_id)

        if len(seleccionados) >= cantidad:
            break

    return seleccionados
