import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from premailer import transform

from Helpers.token_loader import load_token

print("Cargando mail...\n")

token_data = load_token()
Mail = token_data.get("mail_og")
password = token_data.get("password_mail_og")

async def enviar_correo(destinatario, asunto, cuerpo_html):
    """
    Envía un correo electrónico utilizando SMTP de Gmail.
    """
    # Configuración del remitente
    # Mail = "dannprod.dato@gmail.com"  # Reemplaza con tu correo
    # password = "twqn usud lsui wnbv"  # Usa una contraseña de aplicación

    # Configurar el mensaje
    msg = MIMEMultipart()
    msg["From"] = Mail
    msg["To"] = destinatario
    msg["Subject"] = asunto
    
    html = transform(cuerpo_html)
    print("Generando cuerpo del correo...\n")
    # Adjuntar el contenido HTML al correo
    msg.attach(MIMEText(html, "html"))

    try:
        # Conectar al servidor SMTP de Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Seguridad TLS
        server.login(Mail, password)
        server.sendmail(Mail, destinatario, msg.as_string())
        server.quit()
        print("✅ Correo enviado con éxito.")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

    print(f"Correo enviado a {destinatario}")

