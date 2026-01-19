import os
import requests

BASE_URL = os.getenv("MAPY_STORE_API", "https://mapy.com.py/wp-json/wc/store/v1/products")

# Si tu código filtra por una categoría fija, dejalo acá.
# Si no querés forzar una sola categoría, podés comentar CATEGORY_ID o pasar category_id=None.
CATEGORY_ID = os.getenv("MAPY_CATEGORY_ID")  # ej: "10817"


def get_products(per_page=50, category_id=None, page=1):
    """
    WooCommerce Store API (wc/store/v1):
    - NO usar status=publish (puede dar 400)
    - per_page suele tener límite (recomendado <= 100)
    """
    per_page = int(per_page or 50)
    if per_page > 100:
        per_page = 100

    params = {
        "per_page": per_page,
        "page": int(page),
    }

    cid = category_id if category_id is not None else CATEGORY_ID
    if cid:
        params["category"] = str(cid)

    r = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    r.raise_for_status()
    return r.json()
