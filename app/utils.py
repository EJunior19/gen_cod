def obtener_precio_base(producto: dict) -> float:
    """
    Obtiene el precio base REAL del producto desde la API.
    Compatible con WooCommerce PY (guaraníes).
    """

    prices = producto.get("prices", {})

    # Prioridad: price
    price_raw = prices.get("price")

    if not price_raw:
        return 0

    try:
        precio = float(price_raw)
    except ValueError:
        return 0

    # 🔴 REGLA CLAVE:
    # Si el precio es mayor a 10.000 asumimos que YA está en guaraníes
    if precio > 10_000:
        return precio

    # Caso raro: APIs que devuelven centavos
    return precio / 100


def calcular_precio_con_margen(precio_base: float, margen: float = 0.15) -> int:
    """
    Aplica margen comercial y redondea.
    """
    precio = precio_base * (1 + margen)
    return int(round(precio))
