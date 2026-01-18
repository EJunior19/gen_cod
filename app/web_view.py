from flask import Flask, render_template_string, send_file
import requests
from io import BytesIO
import time

# ⏱ intervalo de actualización automática (10 minutos)
INTERVALO = 600

def iniciar_web(data_provider):
    app = Flask(__name__)

    TEMPLATE = """
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

            .topbar {
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:20px;
            }

            h1 {
                margin:0;
                font-size:26px;
            }

            .status {
                font-size:13px;
                color:#555;
                margin-top:6px;
            }

            button {
                background:#1f2937;
                color:white;
                border:none;
                padding:10px 18px;
                border-radius:10px;
                cursor:pointer;
                font-size:14px;
            }

            button:hover {
                background:#111827;
            }

            .grid {
                display:grid;
                grid-template-columns: repeat(auto-fit, minmax(380px,1fr));
                gap:26px;
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
            }

            .img-box img {
                max-width:100%;
                max-height:210px;
                object-fit:contain;
            }

            h2 {
                font-size:18px;
                margin:0 0 10px 0;
                font-weight:bold;
            }

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
            }

            .toast {
                position:fixed;
                bottom:25px;
                right:25px;
                background:#111827;
                color:white;
                padding:12px 18px;
                border-radius:12px;
                opacity:0;
                transform:translateY(20px);
                transition:all .3s ease;
                font-size:14px;
            }

            .toast.show {
                opacity:1;
                transform:translateY(0);
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
            <button onclick="location.href='/refresh'">🔄 Ejecutar ahora</button>
        </div>

        <div class="grid">
            {% for p in productos %}
            <div class="card">
                <div class="sku">SKU: {{ p.sku }}</div>

                <div class="img-box">
                    <img src="/img/{{ loop.index0 }}">
                </div>

                <h2>{{ p.nombre }}</h2>
                <p>{{ p.descripcion }}</p>

                <div class="precio">₲ {{ p.precio }}</div>

                <div class="acciones">
                    <button onclick="copiarTexto(`{{ p.texto_whatsapp }}`)">Copiar texto</button>
                    <button onclick="copiarImagen('/img/{{ loop.index0 }}')">Copiar imagen</button>
                </div>
            </div>
            {% endfor %}
        </div>

        <div id="toast" class="toast"></div>

        <script>
            const lastUpdate = {{ last_update }};
            const intervalo = {{ intervalo }};

            function updateCountdown(){
                const now = Math.floor(Date.now() / 1000);
                let restante = (lastUpdate + intervalo) - now;
                if (restante < 0) restante = 0;

                const min = Math.floor(restante / 60);
                const sec = restante % 60;
                document.getElementById("countdown").innerText = min + "m " + sec + "s";
            }

            setInterval(updateCountdown, 1000);
            updateCountdown();

            function showToast(msg){
                const t = document.getElementById("toast");
                t.innerText = msg;
                t.classList.add("show");
                setTimeout(() => t.classList.remove("show"), 2000);
            }

            function copiarTexto(texto){
                navigator.clipboard.writeText(texto);
                showToast("Texto copiado");
            }

            function copiarImagen(url){
                const img = new Image();
                img.crossOrigin = "anonymous";
                img.src = url;

                img.onload = () => {
                    const canvas = document.createElement("canvas");
                    canvas.width = img.naturalWidth;
                    canvas.height = img.naturalHeight;

                    const ctx = canvas.getContext("2d");
                    ctx.drawImage(img, 0, 0);

                    canvas.toBlob(async (blob) => {
                        if (!blob) {
                            showToast("No se pudo copiar la imagen");
                            return;
                        }
                        try {
                            await navigator.clipboard.write([
                                new ClipboardItem({ "image/png": blob })
                            ]);
                            showToast("Imagen copiada");
                        } catch {
                            showToast("Permiso denegado");
                        }
                    });
                };

                img.onerror = () => showToast("Error cargando imagen");
            }
        </script>

    </body>
    </html>
    """

    state = {
        "productos": [],
        "imagenes_bin": [],
        "last_update": int(time.time())
    }

    def refresh_data():
        productos, _ = data_provider()
        state["productos"] = productos
        state["imagenes_bin"] = []
        state["last_update"] = int(time.time())

        for p in productos:
            r = requests.get(p["imagen"], timeout=10)
            state["imagenes_bin"].append(r.content)

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
        return send_file(BytesIO(state["imagenes_bin"][i]), mimetype="image/jpeg")

    app.run(
        host="0.0.0.0",  # aceptar conexiones externas
        port=8083,  # puerto libre
        debug=False
    )

