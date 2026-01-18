import time
import threading
from app.main import build_data

# Cache global
CACHE = {
    "productos": [],
    "last_update": None
}

INTERVALO = 600  # 10 minutos (600 segundos)

def actualizar_cache():
    while True:
        try:
            print("🔄 Actualizando productos automáticamente...")
            productos, _ = build_data()
            CACHE["productos"] = productos
            CACHE["last_update"] = time.strftime("%H:%M:%S")
            print("✅ Productos actualizados")
        except Exception as e:
            print("❌ Error al actualizar:", e)

        time.sleep(INTERVALO)

def iniciar_scheduler():
    t = threading.Thread(target=actualizar_cache, daemon=True)
    t.start()
