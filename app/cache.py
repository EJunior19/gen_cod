import os
import json
import time

BASE_DIR = os.path.dirname(__file__)

# Cache en: <raiz_proyecto>/data/cache.json
CACHE_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "cache.json"))


def _load() -> dict:
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CACHE_PATH)


def fue_usado(product_id: str, dias: int = 3) -> bool:
    data = _load()
    pid = str(product_id)

    ts = data.get(pid)
    if ts is None:
        return False

    try:
        ts = int(ts)
    except Exception:
        # cache corrupto -> limpiar
        data.pop(pid, None)
        _save(data)
        return False

    ahora = int(time.time())
    ttl = int(dias) * 86400

    # si ya expiró, ya no cuenta como usado
    if (ahora - ts) >= ttl:
        data.pop(pid, None)
        _save(data)
        return False

    return True


def marcar_usado(product_id: str) -> None:
    data = _load()
    data[str(product_id)] = int(time.time())
    _save(data)


def limpiar_cache() -> None:
    """Borra completamente el cache."""
    if os.path.exists(CACHE_PATH):
        os.remove(CACHE_PATH)
