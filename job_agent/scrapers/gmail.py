import imaplib
import email
from email.header import decode_header
from typing import List, Dict
import re
import hashlib

def connect_gmail(gmail_user: str, gmail_password: str):
    """Conecta a Gmail vía IMAP"""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(gmail_user, gmail_password)
        return mail
    except Exception as e:
        print(f"[ERROR] Gmail conexión: {e}")
        return None

def fetch_linkedin_alerts(gmail_user: str, gmail_password: str) -> List[Dict]:
    """Obtiene alertas de LinkedIn desde Gmail"""
    mail = connect_gmail(gmail_user, gmail_password)
    if not mail:
        return []
    
    try:
        # Seleccionar inbox
        mail.select("INBOX")
        
        # Buscar emails de LinkedIn de hoy (puedes ajustar esto)
        status, messages = mail.search(None, 'FROM "linkedin-noreply@linkedin.com"', 'UNSEEN')
        
        ofertas = []
        email_ids = messages[0].split()
        
        for email_id in email_ids[-10:]:  # Últimos 10 emails
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            # Extraer texto
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = msg.get_payload(decode=True).decode()
            
            # Parsear la alerta de LinkedIn (básico)
            # LinkedIn envía emails con estructura tipo "Título - Empresa"
            lines = body.split('\n')
            for line in lines:
                if "job" in line.lower() or "position" in line.lower():
                    # Generar ID único
                    offer_id = hashlib.md5(f"linkedin_{line}".encode()).hexdigest()[:12]
                    
                    oferta = {
                        'id': offer_id,
                        'titulo': line.strip()[:100],
                        'empresa': 'LinkedIn Alert',
                        'url': 'Ver en LinkedIn',
                        'descripcion': body[:500],
                        'fuente': 'linkedin',
                        'fecha_publicacion': msg['Date']
                    }
                    ofertas.append(oferta)
        
        mail.close()
        mail.logout()
        print(f"[Gmail] {len(ofertas)} alertas de LinkedIn encontradas")
        return ofertas
        
    except Exception as e:
        print(f"[ERROR] Gmail parsing: {e}")
        return []