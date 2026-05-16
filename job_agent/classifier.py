import json
import re
from anthropic import Anthropic


def classifier_prompt(oferta, user_config=None):
    cfg = user_config or {}
    sueldo_min = cfg.get('SUELDO_MIN', '20000')
    stack = cfg.get('STACK', 'React, Node.js, JavaScript, Python')
    ubicacion = cfg.get('UBICACION', 'Malaga, remoto o hibrido en Espana')

    return f"""Analiza esta oferta de empleo y decide si encaja con estos criterios:
- Sueldo MINIMO: {sueldo_min} EUR anuales
- Rol: Frontend Junior preferible, pero flexible en stack
- Ubicacion: {ubicacion}
- Stack: {stack}. Evitar legacy (Java viejo, PHP puro)
- Empresa: Startup/Scale-up preferible, evitar consultoras grandes

OFERTA:
Titulo: {oferta['titulo']}
Empresa: {oferta['empresa']}
Descripcion: {oferta['descripcion']}

Responde SOLO en JSON (sin markdown, sin comillas extras):
{{
  "encaja": true/false,
  "score": numero 0-10,
  "motivo": "razon en una linea",
  "sueldo_estimado": "estimacion o desconocido"
}}"""


def classify_oferta(oferta, user_config=None):
    api_key = (user_config or {}).get('ANTHROPIC_API_KEY')
    client = Anthropic(api_key=api_key) if api_key else Anthropic()

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": classifier_prompt(oferta, user_config)}]
        )
        text = response.content[0].text.strip()
        # Eliminar markdown code fences si el modelo los añade
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
            text = text.strip()
        if not text:
            print(f"Error clasificando: respuesta vacía del API (stop_reason={response.stop_reason})")
            return {"encaja": False, "score": 0, "motivo": "Respuesta vacía del API"}
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Error clasificando JSON: {e} | Respuesta: {repr(text)}")
        return {"encaja": False, "score": 0, "motivo": f"JSON inválido: {e}"}
    except Exception as e:
        print(f"Error clasificando: {e}")
        return {"encaja": False, "score": 0, "motivo": f"Error: {e}"}
