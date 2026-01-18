import random
from app.cache import fue_usado, marcar_usado


def seleccionar_productos(productos, cantidad):
    random.shuffle(productos)
    seleccionados = []

    for p in productos:
        product_id = str(p.get("id") or p.get("sku"))

        if fue_usado(product_id):
            continue

        seleccionados.append(p)
        marcar_usado(product_id)

        if len(seleccionados) == cantidad:
            break

    return seleccionados
