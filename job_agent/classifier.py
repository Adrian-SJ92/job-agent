import json
from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

def classifier_prompt(oferta):
    return f"""Analiza esta oferta de empleo y decide si encaja con estos criterios:
- Sueldo MÍNIMO: 20.000€ anuales
- Rol: Frontend Junior preferible, pero flexible en stack
- Ubicación: Málaga, remoto o híbrido en España
- Stack: React, Node.js, JavaScript, Python OK. Evitar legacy (Java viejo, PHP puro)
- Empresa: Startup/Scale-up preferible, evitar consultoras grandes

OFERTA:
Título: {oferta['titulo']}
Empresa: {oferta['empresa']}
Descripción: {oferta['descripcion']}

Responde SOLO en JSON (sin markdown, sin comillas extras):
{{
  "encaja": true/false,
  "score": número 0-10,
  "motivo": "razón en una línea",
  "sueldo_estimado": "estimación o desconocido"
}}"""

def classify_oferta(oferta):
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[
                {"role": "user", "content": classifier_prompt(oferta)}
            ]
        )
        text = response.content[0].text.strip()
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Error clasificando: {e}")
        return {"encaja": False, "score": 0, "motivo": f"Error: {e}"}
