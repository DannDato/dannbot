import aiohttp
import requests
import unicodedata
import time 
import os
import sqlite3
import logging
import re

#Cargar el token para operaciones con las credenciales
from Helpers.token_loader import load_token
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#asignacion de credenciales
token_data = load_token()
access_token = token_data.get("access_token")
client_id = token_data.get("client_id")
initial_channels = token_data.get("initial_channels", [])
broadcaster_id = token_data.get("broadcaster_id")
steam_api = token_data.get("steam_api")
steamid = token_data.get("steamID")
#______________________________________________________________

# Convierte los valores en enteros, asegurando que None, '' o valores inválidos sean 0
def safe_int(value):
    try:
        return int(value) if value not in [None, ""] else 0
    except ValueError:
        return 0
    
# Función para verificar si el autor del mensaje está en la lista de usuarios permitidos
def is_authorized(ctx):
    # Lista de usuarios autorizados
    AUTHORIZED_USERS = ['danndato', 'lauunieves']
    return ctx.author.name.lower() in AUTHORIZED_USERS

#Función que divide una cadena de texto grande en diferentes mensajes en base al límite definid
async def send_large_message(ctx, message):
    max = 450
    start = 0
    while start < len(message):
        # Buscar el límite donde se cortará el mensaje
        end = start + max
        if end < len(message):  # Si no estamos al final de la cadena
            # Buscar el último espacio antes del límite
            end = message.rfind(" ", start, end)
            if end == -1:  # Si no hay espacio en el rango, corta directamente en el límite
                end = start + max
        # Enviar el segmento del mensaje
        await ctx.send(message[start:end].strip())
        start = end + 1  # Continuar desde el carácter siguiente


#Funcion que valida la lectura de nombres de usuario
def normalize_username(username):
    username = unicodedata.normalize('NFKC', username) # Eliminar caracteres de control y normalizar el texto
    username = username.split(' ')[0] # Eliminar todo después de un espacio (si lo hay)
    return username.strip().lower()

#Revisión de si el canal se encuentra en vivo
async def is_channel_online():
    """
    Verifica si un canal de Twitch está transmitiendo en vivo.
    Primero verifica en la base de datos si hay un stream activo,
    si no encuentra, realiza la solicitud al servidor de Twitch.
    """
    max_attempts = 5
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificar en la base de datos si hay un stream activo
        cursor.execute('''
            SELECT COUNT(*)
            FROM stream_data
            WHERE accion = "start_stream" AND NOT EXISTS (
                SELECT 1
                FROM stream_data
                WHERE accion = "end_stream"
                AND datetime(date) > (
                    SELECT MAX(date)
                    FROM stream_data
                    WHERE accion = "start_stream"
                )
            );
        ''')
        result = cursor.fetchone()
        conn.close()

        if result and result[0] > 0:
            logging.warning("Un stream está activo según la base de datos.")
            return True

        logging.info("No hay stream activo en la base de datos, verificando en Twitch...")

        # Si no hay registro en la base de datos, realizar solicitud a Twitch
        for attempt in range(max_attempts):
            logging.info(f"Intento {attempt + 1} de {max_attempts}...")
            try:
                contents = requests.get('https://www.twitch.tv/' + broadcaster_id).content.decode('utf-8')
                if 'isLiveBroadcast' in contents:
                    logging.info(f"{broadcaster_id} está en línea según Twitch.")
                    return True
                else:
                    logging.info(f"{broadcaster_id} está offline según Twitch.")
            except requests.RequestException as e:
                logging.error(f"Error en la solicitud a Twitch: {e}")

        # Si después de todos los intentos no se obtiene confirmación, retornar False
        logging.info(f"{broadcaster_id} sigue offline después de {max_attempts} intentos.")
        return False

    except sqlite3.Error as e:
        logging.error(f"Error al acceder a la base de datos: {e}")
        return False


def clean_text(text):
    # Eliminar emojis (usando una expresión regular para rangos Unicode)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # Emoticons
        u"\U0001F300-\U0001F5FF"  # Símbolos y pictogramas
        u"\U0001F680-\U0001F6FF"  # Transporte y mapas
        u"\U0001F700-\U0001F77F"  # Alquimia
        u"\U0001F780-\U0001F7FF"  # Geometría
        u"\U0001F800-\U0001F8FF"  # Flechas
        u"\U0001F900-\U0001F9FF"  # Caras y gestos
        u"\U0001FA00-\U0001FA6F"  # Objetos y animales
        u"\U0001FA70-\U0001FAFF"  # Símbolos adicionales
        u"\U00002702-\U000027B0"  # Varias cosas
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)

    # Reemplazar saltos de línea y tabuladores con espacios
    text = text.replace("\n", " ").replace("\t", " ")

    # Eliminar emojis de la cadena
    text = emoji_pattern.sub("", text)

    # Eliminar espacios extra generados por los reemplazos
    text = re.sub(r"\s+", " ", text).strip()

    return text

async def get_viewers_count(self, channel_name):
        # Obtener el stream del canal usando el client
        streams = await self.client.get_streams(user_logins=[channel_name])
        if streams:
            # La cantidad de viewers estará en streams[0].viewer_count
            return streams[0].viewer_count
        else:
            return 0  # Si el canal no está transmitiendo