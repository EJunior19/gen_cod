import requests
import os

def descargar_imagen(url, nombre_archivo):
    os.makedirs("output", exist_ok=True)
    ruta = os.path.join("output", nombre_archivo)

    r = requests.get(url, timeout=20)
    r.raise_for_status()

    with open(ruta, "wb") as f:
        f.write(r.content)

    return ruta
