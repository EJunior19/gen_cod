from flask import Flask, render_template_string, send_file
from app.flyer_generator import generar_flyer
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import time

# ⏱ intervalo de actualización automática (10 minutos)
INTERVALO = 600


def iniciar_web(data_provider):
    app = Flask(__name__)

    TEMPLATE = r"""
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Productos WhatsApp</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background:#f3f4f6;
                padding:20px;
            }

            .img-box img{
              pointer-events: none;
              user-select: none;
              -webkit-user-drag: none;
            }

            .topbar {
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:20px;
            }
            h1 { margin:0; font-size:26px; }
            .status { font-size:13px; color:#555; margin-top:6px; }

            button {
                background:#1f2937;
                color:white;
                border:none;
                padding:10px 18px;
                border-radius:10px;
                cursor:pointer;
                font-size:14px;
            }
            button:hover { background:#111827; }

            .grid {
                display:grid;
                grid-template-columns: repeat(auto-fit, minmax(380px,1fr));
                gap:26px;
            }

            .toast {
              position: fixed;
              bottom: 24px;
              right: 24px;
              background: #111827;
              color: #e5e7eb;
              padding: 12px 18px;
              border-radius: 12px;
              font-size: 14px;
              box-shadow: 0 10px 24px rgba(0,0,0,.25);
              opacity: 0;
              transform: translateY(10px);
              transition: all .25s ease;
              z-index: 9999;
              pointer-events: none;
            }
            .toast.show {
              opacity: 1;
              transform: translateY(0);
            }
            .toast.success {
              border-left: 4px solid #22c55e;
            }
            .toast.error {
              border-left: 4px solid #ef4444;
            }

            .card {
                position:relative;
                background:white;
                border-radius:18px;
                padding:20px;
                display:flex;
                flex-direction:column;
                box-shadow:0 10px 24px rgba(0,0,0,.10);
                min-height:460px;
            }
            .sku {
                position:absolute;
                top:12px;
                right:14px;
                font-size:12px;
                background:#e5e7eb;
                padding:5px 10px;
                border-radius:14px;
                color:#374151;
            }
            .img-box {
                display:flex;
                justify-content:center;
                align-items:center;
                background:#fafafa;
                border-radius:14px;
                height:230px;
                margin-bottom:18px;
                overflow:hidden;
            }
            .img-box img {
                max-width:100%;
                max-height:210px;
                object-fit:contain;
            }
            h2 { font-size:18px; margin:0 0 10px 0; font-weight:bold; }
            p {
                font-size:14px;
                color:#444;
                line-height:1.5;
                margin:0 0 16px 0;
                white-space:pre-line;
            }
            .precio {
                font-size:26px;
                font-weight:bold;
                color:#0a8f08;
                margin-top:auto;
            }
            .acciones {
                display:flex;
                gap:12px;
                margin-top:16px;
                flex-wrap:wrap;
            }
        </style>
    </head>
    <body>

        <div class="topbar">
            <div>
                <h1>🛍️ Productos listos para WhatsApp</h1>
                <div class="status">
                    ⏱ Próxima actualización en <strong><span id="countdown"></span></strong>
                </div>
            </div>
            <button type="button" onclick="location.href='/refresh'">🔄 Ejecutar ahora</button>
        </div>

        <div class="grid">
            {% if productos and productos|length %}
              {% for p in productos %}
              <div class="card">
                  <div class="sku">SKU: {{ p.sku }}</div>

                  <div class="img-box">
                      <img src="/img/{{ loop.index0 }}" alt="producto">
                  </div>

                  <h2>{{ p.nombre }}</h2>
                  <p>{{ p.descripcion }}</p>

                  <div class="precio">₲ {{ p.precio }}</div>

                  <div class="acciones">
                      <button type="button" onclick='copiarTexto(event, {{ p.texto_whatsapp | tojson }});'>
                        Copiar texto
                      </button>

                      <button type="button" onclick="copiarImagen(event, {{ loop.index0 }})">
                        Copiar imagen
                      </button>

                      <button type="button" onclick="copiarTodo(event, {{ loop.index0 }}, {{ p.texto_whatsapp | tojson }})">
                        Copiar TODO
                      </button>

                      <button type="button" onclick="window.open('/flyer/{{ loop.index0 }}?t=' + Date.now(), '_blank')">
                        🖼 Generar flyer
                      </button>
                  </div>
              </div>
              {% endfor %}
            {% else %}
              <div style="padding:18px; background:white; border-radius:14px; box-shadow:0 10px 24px rgba(0,0,0,.10);">
                ⚠️ No hay productos para mostrar. Probá “Ejecutar ahora”.
              </div>
            {% endif %}
        </div>

        <script>
          // ===== Toast =====
          function showToast(msg = "Copiado", kind = "success") {
            let t = document.getElementById("toast");
            if (!t) {
              t = document.createElement("div");
              t.id = "toast";
              document.body.appendChild(t);
            }
            t.className = "toast " + (kind === "error" ? "error" : "success");
            t.textContent = msg;
            t.classList.add("show");

            clearTimeout(t._timer);
            t._timer = setTimeout(() => {
              t.classList.remove("show");
            }, 1200);
          }

          // ===== Countdown =====
          const lastUpdate = {{ last_update }};
          const intervalo = {{ intervalo }};

          function updateCountdown() {
            const now = Math.floor(Date.now() / 1000);
            let restante = (lastUpdate + intervalo) - now;
            if (restante < 0) restante = 0;
            document.getElementById("countdown").innerText =
              Math.floor(restante / 60) + "m " + (restante % 60) + "s";
          }
          setInterval(updateCountdown, 1000);
          updateCountdown();

          // ===== Copiar texto =====
          function copiarTexto(ev, texto) {
            ev.preventDefault();
            ev.stopPropagation();

            if (!navigator.clipboard) {
              showToast("Portapapeles no disponible", "error");
              return;
            }

            navigator.clipboard.writeText(texto)
              .then(() => showToast("Texto copiado"))
              .catch((err) => {
                console.error(err);
                showToast("No se pudo copiar el texto", "error");
              });
          }

          // ===== Convertir imagen a PNG (si viene JPEG/WebP) =====
          function convertirBlobAPng(blob) {
            return new Promise((resolve, reject) => {
              const img = new Image();
              const objectUrl = URL.createObjectURL(blob);

              img.onload = () => {
                try {
                  const canvas = document.createElement("canvas");
                  canvas.width = img.naturalWidth;
                  canvas.height = img.naturalHeight;
                  const ctx = canvas.getContext("2d");
                  ctx.drawImage(img, 0, 0);

                  canvas.toBlob((outBlob) => {
                    URL.revokeObjectURL(objectUrl);
                    if (!outBlob) return reject(new Error("No se pudo convertir a PNG"));
                    resolve(outBlob);
                  }, "image/png");
                } catch (err) {
                  URL.revokeObjectURL(objectUrl);
                  reject(err);
                }
              };

              img.onerror = () => {
                URL.revokeObjectURL(objectUrl);
                reject(new Error("No se pudo cargar la imagen para convertir"));
              };

              img.src = objectUrl;
            });
          }

          // ===== Copiar imagen =====
          async function copiarImagen(ev, idx) {
            ev.preventDefault();
            ev.stopPropagation();

            if (!navigator.clipboard || !window.ClipboardItem) {
              showToast("Tu navegador no permite copiar imágenes", "error");
              return;
            }

            try {
              const url = `/img/${idx}?t=${Date.now()}`;
              const res = await fetch(url, { cache: "no-store" });
              if (!res.ok) throw new Error("fetch failed");

              const blob = await res.blob();

              // Chromium en Linux suele aceptar mejor PNG
              let pngBlob = blob;
              if (blob.type !== "image/png") {
                pngBlob = await convertirBlobAPng(blob);
              }

              await navigator.clipboard.write([
                new ClipboardItem({ "image/png": pngBlob })
              ]);

              showToast("Imagen copiada");
            } catch (e) {
              console.error(e);
              showToast("No se pudo copiar la imagen", "error");
            }
          }

          // ===== Copiar TODO (imagen + texto) =====
          async function copiarTodo(ev, idx, texto) {
            ev.preventDefault();
            ev.stopPropagation();

            if (!navigator.clipboard || !window.ClipboardItem) {
              showToast("No puedo copiar imágenes", "error");
              return;
            }

            try {
              const url = `/img/${idx}?t=${Date.now()}`;
              const res = await fetch(url, { cache: "no-store" });
              if (!res.ok) throw new Error("fetch failed");

              const blob = await res.blob();
              let pngBlob = blob;
              if (blob.type !== "image/png") {
                pngBlob = await convertirBlobAPng(blob);
              }

              await navigator.clipboard.write([
                new ClipboardItem({ "image/png": pngBlob })
              ]);

              await navigator.clipboard.writeText(texto);

              showToast("Imagen + texto copiados");
            } catch (e) {
              console.error(e);
              showToast("No se pudo copiar TODO", "error");
            }
          }
        </script>

    </body>
    </html>
    """

    state = {
        "productos": [],
        "imagenes_bin": [],
        "imagenes_type": [],
        "last_update": int(time.time())
    }

    def placeholder_png(texto="SIN IMAGEN"):
        img = Image.new("RGB", (900, 600), "#f3f4f6")
        d = ImageDraw.Draw(img)
        d.rectangle([30, 30, 870, 570], outline="#cbd5e1", width=6)
        d.text((60, 260), texto, fill="#334155")
        bio = BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        return bio

    def refresh_data():
        productos, _ = data_provider()
        state["productos"] = productos or []
        state["imagenes_bin"] = []
        state["imagenes_type"] = []
        state["last_update"] = int(time.time())

        for p in state["productos"]:
            url = p.get("imagen")
            if not url:
                state["imagenes_bin"].append(b"")
                state["imagenes_type"].append("")
                continue

            try:
                r = requests.get(
                    url,
                    timeout=20,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                r.raise_for_status()
                ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
                if not ctype.startswith("image/"):
                    raise ValueError(f"Content-Type no es imagen: {ctype}")

                state["imagenes_bin"].append(r.content)
                state["imagenes_type"].append(ctype or "image/jpeg")
            except Exception:
                state["imagenes_bin"].append(b"")
                state["imagenes_type"].append("")

    @app.route("/")
    def index():
        if not state["productos"]:
            refresh_data()

        return render_template_string(
            TEMPLATE,
            productos=state["productos"],
            last_update=state["last_update"],
            intervalo=INTERVALO
        )

    @app.route("/refresh")
    def refresh():
        refresh_data()
        return index()

    @app.route("/img/<int:i>")
    def img(i):
        if i < 0 or i >= len(state["productos"]):
            return send_file(placeholder_png("INDICE INVALIDO"), mimetype="image/png")

        data = state["imagenes_bin"][i] if i < len(state["imagenes_bin"]) else b""
        mime = state["imagenes_type"][i] if i < len(state["imagenes_type"]) else ""

        if not data:
            nombre = state["productos"][i].get("nombre", "SIN IMAGEN")
            return send_file(placeholder_png(nombre[:40]), mimetype="image/png")

        return send_file(BytesIO(data), mimetype=mime or "image/jpeg")

    @app.route("/flyer/<int:i>")
    def flyer(i):
        if i < 0 or i >= len(state["productos"]):
            return send_file(placeholder_png("INDICE INVALIDO"), mimetype="image/png")

        producto = state["productos"][i]

        path = generar_flyer({
            "nombre": producto.get("nombre", ""),
            "descripcion": producto.get("descripcion", ""),
            "precio": producto.get("precio", ""),
            "imagen": producto.get("imagen", "")
        }, i)

        return send_file(path, mimetype="image/png")

    return app
