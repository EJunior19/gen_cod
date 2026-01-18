import os
import textwrap
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(__file__)

FONT_BOLD = os.path.join(BASE_DIR, "assets", "fonts", "Montserrat-Bold.ttf")
FONT_REGULAR = os.path.join(BASE_DIR, "assets", "fonts", "Montserrat-Regular.ttf")

OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# Helpers
# =========================
def load_font_safe(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _fit_text(draw, text, font, max_width, max_lines):
    """
    Corta texto en líneas para que no se salga del ancho.
    """
    if not text:
        return []

    words = text.replace("\r", "").split()
    lines = []
    current = ""

    for w in words:
        test = (current + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
            if len(lines) >= max_lines:
                break

    if len(lines) < max_lines and current:
        lines.append(current)

    # Si sobró, truncar con ...
    if len(lines) == max_lines and len(words) > 0:
        # aseguramos que la última línea no sea larguísima
        while draw.textlength(lines[-1] + "…", font=font) > max_width and len(lines[-1]) > 0:
            lines[-1] = lines[-1][:-1]
        if not lines[-1].endswith("…"):
            lines[-1] = lines[-1].rstrip() + "…"

    return lines


def _download_image(url, timeout=12):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGBA")


# =========================
# Gemini Image (optional)
# =========================
def _gemini_generate_image(prompt: str, out_path: str) -> str:
    """
    Genera una imagen con Gemini (si tu cuenta/modelo lo permite).
    Si falla, levanta excepción para que el caller haga fallback.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("No hay GEMINI_API_KEY")

    # SDK nuevo (si no lo tenés instalado, fallará y hacemos fallback)
    from google import genai
    client = genai.Client(api_key=api_key)

    # ⚠️ El modelo puede variar según disponibilidad de tu cuenta.
    # Si te falla "model not found" o "not enabled", lo cambiamos al que tengas.
    resp = client.models.generate_images(
        model="imagen-3.0-generate-001",
        prompt=prompt,
        size="1024x1024",
        number_of_images=1,
    )

    img_bytes = resp.generated_images[0].image_bytes
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(img_bytes)

    return out_path


# =========================
# Flyer: Gemini (si puede) + Fallback Pillow (si no)
# =========================
def generar_flyer(producto, idx):
    """
    Genera flyer 1080x1080.
    - Si FLYER_ENGINE=gemini y Gemini está disponible → genera imagen IA.
    - Si falla → fallback a Pillow con layout pro y legible.
    """
    engine = os.getenv("FLYER_ENGINE", "pillow").lower()  # "gemini" o "pillow"
    output_path = os.path.join(OUTPUT_DIR, f"flyer_{idx}.png")

    # --------- 1) Intento Gemini imagen ----------
    if engine == "gemini":
        nombre = (producto.get("nombre") or "Producto").strip()
        precio = (producto.get("precio") or "").strip()

        prompt = f"""
Flyer cuadrado para redes sociales (1080x1080), estilo premium y moderno.
Fondo claro con acentos verdes (#0a8f08). Tipografía grande y legible.
Incluí:
- Título: "{nombre}" (arriba)
- Precio GRANDE: "₲ {precio}" (bien destacado)
- Texto pequeño: "Katueté Importados"
Dejá espacio para foto del producto grande (centrada o abajo).
No uses texto pequeño ni mucho contenido.
"""

        try:
            return _gemini_generate_image(prompt, output_path)
        except Exception:
            # fallback automático a Pillow
            pass

    # --------- 2) Fallback Pillow (mejorado) ----------
    # Canvas
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), "#ffffff")
    draw = ImageDraw.Draw(img)

    # Colores
    GREEN = "#0a8f08"
    DARK = "#111111"
    GRAY = "#333333"
    LIGHT_GRAY = "#f3f4f6"

    # Fuentes (más balanceadas)
    title_font = load_font_safe(FONT_BOLD, 44)
    price_font = load_font_safe(FONT_BOLD, 78)
    text_font = load_font_safe(FONT_REGULAR, 30)
    brand_font = load_font_safe(FONT_BOLD, 26)

    # Layout
    padding = 60
    max_text_width = W - padding * 2

    # Header (badge)
    badge_text = "Katueté Importados"
    badge_w = int(draw.textlength(badge_text, font=brand_font)) + 40
    badge_h = 52
    badge_x = W - padding - badge_w
    badge_y = padding
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
        radius=18,
        fill=LIGHT_GRAY
    )
    draw.text((badge_x + 20, badge_y + 12), badge_text, fill=DARK, font=brand_font)

    # Título (auto wrap 2 líneas)
    nombre = (producto.get("nombre") or "").strip()
    title_lines = _fit_text(draw, nombre, title_font, max_text_width, max_lines=2)
    y = padding + 10
    for line in title_lines:
        draw.text((padding, y), line, fill=DARK, font=title_font)
        y += 54

    # Precio (grande)
    precio = (producto.get("precio") or "").strip()
    price_text = f"₲ {precio}"
    draw.text((padding, y + 8), price_text, fill=GREEN, font=price_font)
    y += 110

    # Separador
    draw.line((padding, y, W - padding, y), fill="#e5e7eb", width=3)
    y += 28

    # Descripción (máx 5 líneas)
    desc = (producto.get("descripcion") or "").strip()
    # Limpieza: tu IA trae saltos; mantenemos pero no dejamos un bloque enorme
    desc = desc.replace("\r", "")
    # si trae muchas líneas, lo compactamos para que entre lindo
    desc = "\n".join([l.strip() for l in desc.split("\n") if l.strip()][:6])

    # Convertimos saltos a texto “wrap”
    # 1) Partimos por líneas y hacemos wrap por cada una
    desc_lines = []
    for part in desc.split("\n"):
        wrapped = _fit_text(draw, part, text_font, max_text_width, max_lines=2)
        desc_lines.extend(wrapped)

    desc_lines = desc_lines[:6]  # límite final
    for line in desc_lines:
        draw.text((padding, y), line, fill=GRAY, font=text_font)
        y += 40

    # Zona imagen (cuadro abajo)
    img_box_top = 520
    img_box = (padding, img_box_top, W - padding, H - padding)
    draw.rounded_rectangle(img_box, radius=28, fill="#fafafa", outline="#e5e7eb", width=3)

    # Imagen producto centrada
    try:
        prod_img = _download_image(producto["imagen"])
        # tamaño máximo dentro del box
        box_w = (W - padding) - padding
        box_h = (H - padding) - img_box_top
        prod_img.thumbnail((int(box_w * 0.88), int(box_h * 0.88)))

        px = padding + (box_w - prod_img.width) // 2
        py = img_box_top + (box_h - prod_img.height) // 2
        img.paste(prod_img, (px, py), prod_img)
    except Exception:
        # si falla, no rompe
        pass

    img.save(output_path)
    return output_path
