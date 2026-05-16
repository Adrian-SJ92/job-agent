"""Script de diagnóstico: muestra remitentes y asuntos de emails de LinkedIn en Gmail."""
import imaplib
import email
import os
from dotenv import load_dotenv

load_dotenv('config/adrian.env', override=True)
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login(GMAIL_USER, GMAIL_PASSWORD)
mail.select("INBOX")

print("=== Buscando cualquier email de LinkedIn (sin filtro de fecha) ===")
status, messages = mail.search(None, 'FROM "linkedin"')
ids = messages[0].split()
print(f"Emails encontrados: {len(ids)}")

for eid in ids[-10:]:
    _, msg_data = mail.fetch(eid, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])
    print(f"  FROM: {msg.get('From')}")
    print(f"  DATE: {msg.get('Date')}")
    print(f"  SUBJ: {msg.get('Subject')}")
    print()

mail.close()
mail.logout()
