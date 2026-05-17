import json
import re
from pathlib import Path

import anthropic

CV_BASE_NAMES = ['cv_base.pdf', 'cv_base.docx']

# Keywords to identify sections in DOCX by heading text
_SECTION_KEYWORDS = {
    'resumen': ['resumen', 'perfil', 'sobre mi', 'acerca de', 'summary', 'profile', 'objective'],
    'experiencia': ['experiencia', 'experience', 'trabajo', 'empleo', 'trayectoria'],
    'skills': ['skills', 'habilidades', 'competencias', 'tecnologias', 'conocimientos'],
}


def load_cv_base(cv_dir="cv"):
    """Busca cv_base.pdf o cv_base.docx en cv_dir. Retorna (filepath, extension)."""
    for name in CV_BASE_NAMES:
        path = Path(cv_dir) / name
        if path.exists():
            return str(path), path.suffix.lower()
    raise FileNotFoundError(
        f"CV base no encontrado. Sube tu CV como '{cv_dir}/cv_base.pdf' o '{cv_dir}/cv_base.docx'."
    )


def extract_cv_text(filepath, ext):
    """Extrae texto plano del CV."""
    if ext == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        return '\n'.join(page.extract_text() or '' for page in reader.pages)
    elif ext in ('.docx', '.doc'):
        from docx import Document
        doc = Document(filepath)
        return '\n'.join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"Formato no soportado: {ext}")


def _adapt_with_claude(cv_text, oferta, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""Eres un experto en CVs. Dado el siguiente CV y una oferta de empleo, haz dos cosas:

1. Extrae del CV: nombre completo y datos de contacto (email, telefono, LinkedIn si existe).
2. Adapta SOLO estas secciones:
   - Resumen profesional (3-4 lineas enfocadas en la oferta)
   - Experiencia (selecciona y destaca los proyectos/logros mas relevantes para esta oferta; no inventes nada)
   - Skills (ordena y prioriza los que coincidan con la oferta)

NO cambies: educacion, certificaciones, datos personales.

Responde UNICAMENTE con JSON valido (sin bloques markdown):
{{
  "nombre": "...",
  "contacto": "email | telefono | linkedin",
  "resumen": "...",
  "experiencia": ["bullet 1", "bullet 2", "..."],
  "skills": ["skill1", "skill2", "..."]
}}

CV BASE:
{cv_text}

OFERTA:
Titulo: {oferta.get('titulo', '')}
Empresa: {oferta.get('empresa', '')}
Descripcion: {oferta.get('descripcion', '')}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


def _find_section_body(doc, section):
    """
    Encuentra los indices de parrafos del cuerpo de una seccion en el DOCX,
    buscando el heading por keywords y devolviendo los parrafos hasta el siguiente heading.
    """
    keywords = _SECTION_KEYWORDS.get(section, [])
    all_headings = []

    for i, para in enumerate(doc.paragraphs):
        text_lower = para.text.strip().lower()
        if not text_lower or len(text_lower) > 50:
            continue
        for sec, kws in _SECTION_KEYWORDS.items():
            if any(kw in text_lower for kw in kws):
                all_headings.append((i, sec))
                break

    for idx, (para_idx, sec) in enumerate(all_headings):
        if sec != section:
            continue
        next_heading = all_headings[idx + 1][0] if idx + 1 < len(all_headings) else len(doc.paragraphs)
        return [i for i in range(para_idx + 1, next_heading) if doc.paragraphs[i].text.strip()]

    return []


def _replace_paragraph_text(para, new_text):
    """
    Reemplaza el texto de un parrafo conservando el estilo del primer Run.
    """
    # Captura el estilo del primer run antes de limpiar
    first_run_font = None
    if para.runs:
        r = para.runs[0]
        first_run_font = {
            'name': r.font.name,
            'size': r.font.size,
            'bold': r.bold,
            'italic': r.italic,
            'color': r.font.color.rgb if r.font.color and r.font.color.type else None,
        }

    # Borrar todos los runs
    for run in para.runs:
        run.text = ''

    # Escribir en el primer run (o crear uno nuevo)
    if para.runs:
        run = para.runs[0]
    else:
        run = para.add_run()

    run.text = new_text

    if first_run_font:
        if first_run_font['name']:
            run.font.name = first_run_font['name']
        if first_run_font['size']:
            run.font.size = first_run_font['size']
        if first_run_font['bold'] is not None:
            run.bold = first_run_font['bold']
        if first_run_font['italic'] is not None:
            run.italic = first_run_font['italic']
        if first_run_font['color']:
            run.font.color.rgb = first_run_font['color']


def _modify_docx(src_path, adapted, output_docx_path):
    """
    Abre el DOCX original, reemplaza resumen/experiencia/skills con el contenido adaptado,
    y guarda en output_docx_path conservando el resto del diseño.
    """
    from docx import Document

    doc = Document(src_path)

    # --- Resumen ---
    resumen_paras = _find_section_body(doc, 'resumen')
    if resumen_paras:
        _replace_paragraph_text(doc.paragraphs[resumen_paras[0]], adapted['resumen'])
        # Vaciar parrafos extra del resumen original si los hay
        for i in resumen_paras[1:]:
            _replace_paragraph_text(doc.paragraphs[i], '')

    # --- Experiencia ---
    exp_paras = _find_section_body(doc, 'experiencia')
    new_bullets = adapted.get('experiencia', [])
    for idx, para_idx in enumerate(exp_paras):
        text = new_bullets[idx] if idx < len(new_bullets) else ''
        _replace_paragraph_text(doc.paragraphs[para_idx], text)

    # --- Skills ---
    skills_paras = _find_section_body(doc, 'skills')
    if skills_paras:
        skills_text = '  •  '.join(adapted.get('skills', []))
        _replace_paragraph_text(doc.paragraphs[skills_paras[0]], skills_text)
        for i in skills_paras[1:]:
            _replace_paragraph_text(doc.paragraphs[i], '')

    doc.save(output_docx_path)


def _docx_to_pdf(docx_path, pdf_path):
    """Convierte DOCX a PDF usando LibreOffice via subprocess."""
    import shutil
    import subprocess

    if not shutil.which('libreoffice'):
        raise RuntimeError(
            "LibreOffice no esta instalado. Instálalo con:\n"
            "  sudo apt-get install libreoffice"
        )

    out_dir = str(Path(pdf_path).parent)
    result = subprocess.run(
        ['libreoffice', '--headless', '--convert-to', 'pdf', docx_path, '--outdir', out_dir],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice fallo al convertir: {result.stderr.strip()}")

    # LibreOffice nombra el PDF igual que el DOCX pero con extension .pdf
    expected = Path(out_dir) / (Path(docx_path).stem + '.pdf')
    if expected != Path(pdf_path):
        expected.rename(pdf_path)


def _render_pdf_from_scratch(adapted, output_path):
    """Genera un PDF profesional desde cero con reportlab (fallback para CV en PDF)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable
    from reportlab.lib.enums import TA_CENTER

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    accent = colors.HexColor('#1a1a2e')
    style_name = ParagraphStyle('Name', fontSize=22, fontName='Helvetica-Bold',
                                alignment=TA_CENTER, spaceAfter=4)
    style_contact = ParagraphStyle('Contact', fontSize=10, fontName='Helvetica',
                                   alignment=TA_CENTER, textColor=colors.gray, spaceAfter=14)
    style_heading = ParagraphStyle('Heading', fontSize=11, fontName='Helvetica-Bold',
                                   textColor=accent, spaceBefore=14, spaceAfter=6)
    style_body = ParagraphStyle('Body', fontSize=10, fontName='Helvetica', leading=15, spaceAfter=4)
    style_bullet = ParagraphStyle('Bullet', fontSize=10, fontName='Helvetica',
                                  leading=14, leftIndent=14, spaceAfter=3)

    story = []
    story.append(Paragraph(adapted.get('nombre', ''), style_name))
    story.append(Paragraph(adapted.get('contacto', ''), style_contact))
    story.append(HRFlowable(width='100%', thickness=1.5, color=accent))
    story.append(Paragraph('RESUMEN PROFESIONAL', style_heading))
    story.append(Paragraph(adapted.get('resumen', ''), style_body))
    story.append(Paragraph('EXPERIENCIA', style_heading))
    for bullet in adapted.get('experiencia', []):
        story.append(Paragraph(f'• {bullet}', style_bullet))
    story.append(Paragraph('SKILLS', style_heading))
    story.append(Paragraph('  •  '.join(adapted.get('skills', [])), style_body))

    doc.build(story)


def generate_adapted_cv(oferta, user_config, cv_dir="cv"):
    """
    Genera un CV adaptado a la oferta y lo guarda como PDF.
    - DOCX input: modifica el documento original (preserva diseño) y convierte a PDF via Word.
    - PDF input: extrae texto y genera PDF con plantilla reportlab.
    Retorna la ruta del PDF generado.
    """
    api_key = user_config.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada para este usuario.")

    filepath, ext = load_cv_base(cv_dir)
    cv_text = extract_cv_text(filepath, ext)
    adapted = _adapt_with_claude(cv_text, oferta, api_key)

    Path(cv_dir).mkdir(exist_ok=True)
    output_pdf = str(Path(cv_dir) / f"generated_{oferta['id']}.pdf")

    if ext in ('.docx', '.doc'):
        tmp_docx = str(Path(cv_dir) / f"_tmp_{oferta['id']}.docx")
        try:
            _modify_docx(filepath, adapted, tmp_docx)
            _docx_to_pdf(tmp_docx, output_pdf)
        finally:
            Path(tmp_docx).unlink(missing_ok=True)
    else:
        _render_pdf_from_scratch(adapted, output_pdf)

    return output_pdf
