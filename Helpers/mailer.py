import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from premailer import transform
from datetime import datetime

from Helpers.printlog import printlog

# ruta de Reportes, fuera del folder actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # carpeta actual
REPORTES_DIR = os.path.join(os.path.dirname(BASE_DIR), "Reportes")
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
os.makedirs(REPORTES_DIR, exist_ok=True)


def _load_env_file(path=ENV_PATH):
    if not os.path.exists(path):
        return

    try:
        with open(path, "r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                if not key:
                    continue

                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                os.environ.setdefault(key, value)
    except Exception as exc:
        printlog(f"No se pudo cargar .env para mailer: {exc}", "WARNING")


def _resolve_mail_credentials():
    _load_env_file()

    mail_user = (
        os.environ.get("DANNBOT_MAIL_USER")
        or os.environ.get("SMTP_USER")
    )
    mail_password = (
        os.environ.get("DANNBOT_MAIL_PASS")
        or os.environ.get("SMTP_PASS")
    )
    return mail_user, mail_password

async def enviar_correo(destinatario, asunto, cuerpo_html):
    """
    Envía un correo electrónico utilizando SMTP de Gmail con multipart (texto + HTML).
    """
    printlog("Configurando envío de correo...")

    mail_user, mail_password = _resolve_mail_credentials()
    if not mail_user or not mail_password:
        printlog(
            "❌ Correo no enviado: faltan credenciales SMTP en .env (DANNBOT_MAIL_USER y DANNBOT_MAIL_PASS).",
            "ERROR",
        )
        return False

    if not destinatario:
        printlog("❌ Correo no enviado: destinatario vacío.", "ERROR")
        return False

    if not asunto:
        asunto = "Reporte de stream"

    # Crear mensaje en formato multipart/alternative
    msg = MIMEMultipart("alternative")
    msg["From"] = mail_user
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg["Reply-To"] = mail_user
    msg["MIME-Version"] = "1.0"
    msg["Content-Language"] = "es"

    # Versión texto plano (fallback para evitar spam)
    texto_plano = "Hola!\n\nEste es el contenido del correo en texto plano.\n\nSi no ves el formato, revisa en un navegador."

    # Optimizar el HTML con premailer (inlining de estilos)
    printlog("Generando cuerpo del correo...")
    html = transform(cuerpo_html or "")

     # Guardar copia del HTML en Reportes
    fechaReporte = datetime.now().strftime("%Y-%m-%d")
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
        server.login(mail_user, mail_password)
        server.sendmail(mail_user, destinatario, msg.as_string())
        server.quit()
        printlog(f"✅ Correo enviado con éxito a {destinatario}.")
        return True
    except Exception as e:
        printlog(f"❌ Error al enviar correo: {e}", "ERROR")
        return False
