import random
from collections import defaultdict
from app.cache import fue_usado, marcar_usado


def _cat_key(p: dict) -> str:
    """
    Clave de categoría para balancear.
    Toma la primera categoría con slug/name válido.
    Si hay varias, intenta usar la última (a veces es la más específica).
    """
    cats = p.get("categories") or []
    if isinstance(cats, list) and cats:
        # Preferir la última por si viene ordenado desde general -> específico
        for c in reversed(cats):
            if not isinstance(c, dict):
                continue
            slug = c.get("slug") or c.get("name")
            if slug:
                return str(slug).strip().lower()
    return "sin_categoria"


def _has_image(p: dict) -> bool:
    imgs = p.get("images") or []
    if not isinstance(imgs, list) or not imgs:
        return False
    src = (imgs[0] or {}).get("src")
    return bool(src)


def seleccionar_productos(
    productos,
    cantidad: int = 10,
    dias_cache: int = 3,
    max_por_categoria: int = 2,
):
    """
    Selecciona 'cantidad' productos:
    - No repite (cache por dias_cache)
    - Balancea por categoría (max_por_categoria por categoría)
    - Prioriza productos con imagen
    - Evita duplicados dentro del mismo lote
    """

    productos = list(productos or [])
    if not productos:
        return []

    # Mezclar entrada
    random.shuffle(productos)

    # 1) filtrar NO usados (según cache)
    candidatos = []
    for p in productos:
        pid = p.get("id")
        if pid is None:
            continue
        if fue_usado(str(pid), dias_cache):
            continue
        candidatos.append(p)

    # 2) Si no hay suficientes NO usados:
    #    completar con usados, pero sin repetir los ya elegibles
    if len(candidatos) < cantidad:
        usados = []
        ids_en_candidatos = {str(x.get("id")) for x in candidatos if x.get("id") is not None}

        for p in productos:
            pid = p.get("id")
            if pid is None:
                continue
            spid = str(pid)
            if spid in ids_en_candidatos:
                continue
            # acá permitimos usados
            usados.append(p)

        random.shuffle(usados)
        candidatos.extend(usados)

    # 3) agrupar por categoría
    buckets = defaultdict(list)
    for p in candidatos:
        buckets[_cat_key(p)].append(p)

    # 4) dentro de cada categoría: primero con imagen
    for k in list(buckets.keys()):
        buckets[k].sort(key=lambda x: 0 if _has_image(x) else 1)

    # 5) selección balanceada (round-robin) con límite por categoría
    seleccionados = []
    usados_por_cat = defaultdict(int)
    ids_ya_seleccionados = set()

    cats = list(buckets.keys())
    random.shuffle(cats)

    while len(seleccionados) < cantidad and cats:
        progreso = False

        for cat in list(cats):
            if len(seleccionados) >= cantidad:
                break

            if usados_por_cat[cat] >= max_por_categoria:
                cats.remove(cat)
                continue

            # sacar hasta encontrar uno no repetido (por si acaso)
            while buckets[cat]:
                p = buckets[cat].pop(0)
                pid = p.get("id")
                if pid is None:
                    continue
                spid = str(pid)
                if spid in ids_ya_seleccionados:
                    continue

                seleccionados.append(p)
                ids_ya_seleccionados.add(spid)
                usados_por_cat[cat] += 1
                progreso = True
                break

            if not buckets[cat] and cat in cats:
                # si quedó vacío, remover
                try:
                    cats.remove(cat)
                except ValueError:
                    pass

        if not progreso:
            break

    # 6) si todavía faltan, completar con lo que quede (sin límite por categoría)
    if len(seleccionados) < cantidad:
        resto = []
        for _, items in buckets.items():
            resto.extend(items)
        random.shuffle(resto)

        for p in resto:
            if len(seleccionados) >= cantidad:
                break
            pid = p.get("id")
            if pid is None:
                continue
            spid = str(pid)
            if spid in ids_ya_seleccionados:
                continue
            seleccionados.append(p)
            ids_ya_seleccionados.add(spid)

    # 7) marcar usados en cache (solo los que tengan id)
    for p in seleccionados:
        pid = p.get("id")
        if pid is not None:
            marcar_usado(str(pid))

    return seleccionados
