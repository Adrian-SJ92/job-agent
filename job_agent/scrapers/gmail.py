import imaplib
import email
import os
from email.header import decode_header
from datetime import datetime, timedelta
from typing import List, Dict
import re
import hashlib

from bs4 import BeautifulSoup
from dotenv import load_dotenv

JOB_KEYWORDS = [
    'developer', 'engineer', 'react', 'python', 'javascript', 'node',
    'senior', 'junior', 'frontend', 'backend', 'fullstack', 'full stack',
    'programador', 'desarrollador', 'software', 'typescript', 'angular',
    'vue', 'java', 'devops', 'cloud', 'data', 'mobile', 'ios', 'android',
]


def _connect(gmail_user: str, gmail_password: str):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(gmail_user, gmail_password)
        return mail
    except Exception as e:
        print(f"[Gmail] Error de conexión: {e}")
        return None


def _decode_header_value(value: str) -> str:
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            decoded.append(part)
    return ' '.join(decoded)


def _get_body(msg) -> tuple[str, str]:
    """Devuelve (plain_text, html_text) del mensaje."""
    plain, html = '', ''
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == 'text/plain' and not plain:
                payload = part.get_payload(decode=True)
                if payload:
                    plain = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
            elif ct == 'text/html' and not html:
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            text = payload.decode(msg.get_content_charset() or 'utf-8', errors='replace')
            if msg.get_content_type() == 'text/html':
                html = text
            else:
                plain = text
    return plain, html


def _extract_jobs_from_html(html: str) -> List[Dict]:
    """Extrae títulos y URLs de ofertas del HTML del email de LinkedIn."""
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    seen_titles = set()

    # LinkedIn alert emails: job titles are in anchor tags
    for a in soup.find_all('a', href=True):
        href = a['href']
        title = a.get_text(' ', strip=True)

        if not title or len(title) < 5 or len(title) > 150:
            continue
        if not any(kw in title.lower() for kw in JOB_KEYWORDS):
            continue
        if title in seen_titles:
            continue

        # Only keep links that look like LinkedIn job links
        clean_url = ''
        if 'linkedin.com' in href and ('jobs' in href or 'view' in href):
            # Strip tracking params keeping the base job URL
            match = re.search(r'(https?://[^&\s"\']+linkedin\.com/jobs/[^\s"\'&?]+)', href)
            if match:
                clean_url = match.group(1)
            else:
                clean_url = href.split('?')[0]

        seen_titles.add(title)
        jobs.append({'titulo': title, 'url': clean_url})

    return jobs


def _extract_jobs_from_plain(plain: str) -> List[Dict]:
    """Extrae títulos de ofertas del texto plano del email de LinkedIn."""
    jobs = []
    seen_titles = set()
    lines = plain.split('\n')

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5 or len(line) > 150:
            continue
        if not any(kw in line.lower() for kw in JOB_KEYWORDS):
            continue
        # Skip lines that are clearly not job titles
        if line.startswith('http') or '@' in line or line.startswith('*'):
            continue
        if line in seen_titles:
            continue

        seen_titles.add(line)
        jobs.append({'titulo': line, 'url': ''})

    return jobs


def _build_description(plain: str, html: str) -> str:
    """Extrae texto legible para la descripción."""
    if plain:
        clean = re.sub(r'\s+', ' ', plain).strip()
        return clean[:500]
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        text = re.sub(r'\s+', ' ', soup.get_text(' ')).strip()
        return text[:500]
    return ''


def fetch_linkedin_alerts(user_config: Dict) -> List[Dict]:
    """Obtiene alertas de LinkedIn desde Gmail usando credenciales de user_config."""
    username = user_config.get('username', '')
    env_path = os.path.join('config', f'{username}.env')
    load_dotenv(env_path, override=True)

    gmail_user = os.getenv('GMAIL_USER', '')
    gmail_password = os.getenv('GMAIL_PASSWORD', '')

    if not gmail_user or not gmail_password:
        print(f"[Gmail] Sin credenciales en {env_path}")
        return []

    mail = _connect(gmail_user, gmail_password)
    if not mail:
        return []

    ofertas = []
    try:
        mail.select("INBOX")

        # Buscar emails de LinkedIn de los últimos 7 días
        since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        status, messages = mail.search(
            None,
            f'FROM "linkedin-noreply@linkedin.com"',
            f'SINCE {since_date}',
        )
        if status != 'OK':
            print("[Gmail] Error en búsqueda IMAP")
            return []

        email_ids = messages[0].split()
        if not email_ids:
            print("[Gmail] Sin emails de LinkedIn en los últimos 7 días")
            return []

        # Limitar a los 20 más recientes
        email_ids = email_ids[-20:]
        print(f"[Gmail] Procesando {len(email_ids)} emails de LinkedIn...")

        for email_id in email_ids:
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != 'OK' or not msg_data or not msg_data[0]:
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                fecha = msg.get('Date', datetime.now().isoformat())
                plain, html = _get_body(msg)
                descripcion = _build_description(plain, html)

                # Extraer trabajos: preferir HTML (más estructura), complementar con plain
                jobs = _extract_jobs_from_html(html) if html else []
                if not jobs and plain:
                    jobs = _extract_jobs_from_plain(plain)

                for job in jobs:
                    offer_id = hashlib.md5(
                        f"linkedin_{job['titulo']}_{fecha}".encode()
                    ).hexdigest()[:12]

                    ofertas.append({
                        'id': offer_id,
                        'titulo': job['titulo'][:120],
                        'empresa': 'LinkedIn',
                        'url': job['url'],
                        'descripcion': descripcion,
                        'fuente': 'linkedin',
                        'fecha_publicacion': fecha,
                    })

            except Exception as e:
                print(f"[Gmail] Error procesando email {email_id}: {e}")
                continue

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"[Gmail] Error general: {e}")
        try:
            mail.logout()
        except Exception:
            pass

    print(f"[Gmail] {len(ofertas)} ofertas de LinkedIn extraídas")
    return ofertas
