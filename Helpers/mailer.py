import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from premailer import transform
from datetime import datetime

from Helpers.token_loader import load_token
from Helpers.printlog import printlog

token_data = load_token()
Mail = token_data.get("mail_og")
password = token_data.get("password_mail_og")

# ruta de Reportes, fuera del folder actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # carpeta actual
REPORTES_DIR = os.path.join(os.path.dirname(BASE_DIR), "Reportes")
os.makedirs(REPORTES_DIR, exist_ok=True)

async def enviar_correo(destinatario, asunto, cuerpo_html):
    """
    Envía un correo electrónico utilizando SMTP de Gmail con multipart (texto + HTML).
    """
    printlog("Configurando envío de correo...")

    # Crear mensaje en formato multipart/alternative
    msg = MIMEMultipart("alternative")
    msg["From"] = Mail
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg["Reply-To"] = Mail
    msg["MIME-Version"] = "1.0"
    msg["Content-Language"] = "es"

    # Versión texto plano (fallback para evitar spam)
    texto_plano = "Hola!\n\nEste es el contenido del correo en texto plano.\n\nSi no ves el formato, revisa en un navegador."
    
    # Optimizar el HTML con premailer (inlining de estilos)
    printlog("Generando cuerpo del correo...")
    html = transform(cuerpo_html)

     # Guardar copia del HTML en Reportes
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fechaReporte = datetime.now().strftime("%Y-%m-%d")
    safe_asunto = "".join(c for c in asunto if c.isalnum() or c in (" ", "_")).strip()
    filename = f"reporte_{fechaReporte}.html"
    file_path = os.path.join(REPORTES_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    printlog(f"💾 Reporte guardado en: {file_path}")

    # Adjuntar partes
    msg.attach(MIMEText(texto_plano, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        # Conectar al servidor SMTP de Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Seguridad TLS
        server.login(Mail, password)
        server.sendmail(Mail, destinatario, msg.as_string())
        server.quit()
        printlog(f"✅ Correo enviado con éxito a {destinatario}.")
    except Exception as e:
        printlog(f"❌ Error al enviar correo: {e}", "ERROR")
