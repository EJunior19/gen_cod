import json
import os
import time

CACHE_FILE = "data/cache.json"
TTL_SECONDS = 60 * 60 * 24 * 3  # 3 días


def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def limpiar_cache_expirado():
    cache = _load_cache()
    ahora = time.time()

    cache_limpio = {
        k: v for k, v in cache.items()
        if ahora - v < TTL_SECONDS
    }

    _save_cache(cache_limpio)
    return cache_limpio


def fue_usado(product_id: str) -> bool:
    cache = limpiar_cache_expirado()
    return product_id in cache


def marcar_usado(product_id: str):
    cache = limpiar_cache_expirado()
    cache[str(product_id)] = time.time()
    _save_cache(cache)
