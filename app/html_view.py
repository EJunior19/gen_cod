def generar_html(productos, mensaje):
    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Productos Generados</title>
        <style>
            body { font-family: Arial; background:#f5f5f5; padding:20px }
            .card {
                background:white;
                padding:15px;
                margin-bottom:20px;
                border-radius:10px;
                display:flex;
                gap:15px;
                box-shadow: 0 2px 8px rgba(0,0,0,.1)
            }
            img { width:180px; border-radius:10px }
            h2 { margin:0 }
            .precio { color:green; font-size:18px; font-weight:bold }
            textarea {
                width:100%;
                height:180px;
                margin-top:20px;
                font-size:14px
            }
        </style>
    </head>
    <body>

    <h1>🛍️ Productos listos para WhatsApp</h1>
    """

    for p in productos:
        html += f"""
        <div class="card">
            <img src="{p['imagen_local']}">
            <div>
                <h2>{p['nombre']}</h2>
                <p>{p['descripcion']}</p>
                <p class="precio">₲ {p['precio']}</p>
            </div>
        </div>
        """

    html += f"""
    <h2>📲 Mensaje para copiar</h2>
    <textarea readonly>{mensaje}</textarea>

    </body>
    </html>
    """

    with open("output/catalogo.html", "w", encoding="utf-8") as f:
        f.write(html)
