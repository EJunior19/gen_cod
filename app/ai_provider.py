import os
from openai import OpenAI

def texto_openai(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"Sos un experto en marketing digital para ventas por WhatsApp."},
            {"role":"user","content":prompt},
        ],
        temperature=0.95,
        max_tokens=220,
    )
    return resp.choices[0].message.content.strip()

def texto_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY")

    # SDK nuevo
    from google import genai
    client = genai.Client(api_key=api_key)

    resp = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
    return (resp.text or "").strip()

def generar_texto_whatsapp(prompt: str, provider: str = "openai") -> str:
    if provider == "gemini":
        return texto_gemini(prompt)
    return texto_openai(prompt)
