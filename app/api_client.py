import requests
from app.config import API_URL, CATEGORY_ID

def get_products(per_page=50):
    params = {
        "category": CATEGORY_ID,
        "per_page": per_page,
        "status": "publish"
    }

    r = requests.get(API_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()
