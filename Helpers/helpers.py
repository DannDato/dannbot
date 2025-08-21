import requests
import unicodedata
import os
import sqlite3
import re
import aiohttp
import time
from datetime import datetime


#Cargar el token para operaciones con las credenciales
from Helpers.token_loader import load_token
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#asignacion de credenciales
token_data = load_token()
access_token = token_data.get("access_token")
client_id = token_data.get("client_id")
initial_channels = token_data.get("initial_channels", [])
channel_name = token_data.get("channel_name")
steam_api = token_data.get("steam_api")
steamid = token_data.get("steamID")

"""
        I N D E X
    get_broadcaster_id      :
    get_app_access_token    :
    safe_int                :
    is_authorized           :
    send_large_message      :
    normalize_username      :
    is_channel_online       :
    clean_text              :
    get_viewers_count       :
    cerrar_conexion         :   
    wordslist               :
    validar_fecha           :
    format_username         :
"""

def get_broadcaster_id():    
    # Hacer la solicitud a la API de Twitch
    url = f"https://api.twitch.tv/helix/users?login={channel_name}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    # Extraer y mostrar el ID del usuario
    if "data" in data and len(data["data"]) > 0:
        broadcaster_id = data["data"][0]["id"]
        return broadcaster_id
    else:
        return 0
broadcaster_id = get_broadcaster_id()
#______________________________________________________________

# Obtener access_token con client_credentials (ya lo tienes)
async def get_app_access_token(client_id: str, client_secret: str) -> str:
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "chat:read chat:edit channel:read:redemptions channel:read:subscriptions channel:read:hype_train channel:read:cheers"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as resp:
            data = await resp.json()
            if resp.status != 200:
                printlog(f"Error al obtener token de acceso: {data}")
                raise Exception("No se pudo obtener token de acceso")
            return data["access_token"]

# Convierte los valores en enteros, asegurando que None, '' o valores inválidos sean 0
def safe_int(value):
    try:
        return int(value) if value not in [None, ""] else 0
    except ValueError:
        return 0
    
# Función para verificar si el autor del mensaje está en la lista de usuarios permitidos
def is_authorized(ctx):
    # Lista de usuarios autorizados
    AUTHORIZED_USERS = ['danndato', 'lauunieves',]
    if ctx.chatter.name.lower() in AUTHORIZED_USERS:
        return True
    else: return False 

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
        await ctx.send(f'{message[start:end].strip()}')
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
        cerrar_conexion(conn, cursor)
        if result and result[0] > 0:
            # printlog("Un stream está activo según la base de datos.","WARNING")
            return True
        # printlog("No hay stream activo en la base de datos, verificando en Twitch...","ERROR")
        # Si no hay registro en la base de datos, realizar solicitud a Twitch
        for attempt in range(max_attempts):
            try:
                contents = requests.get('https://www.twitch.tv/' + broadcaster_id).content.decode('utf-8')
                if 'isLiveBroadcast' in contents:
                    printlog(f"{broadcaster_id} está en línea según Twitch.","INFO")
                    return True
                    # if attempt == max_attempts: printlog(f"{broadcaster_id} está offline según Twitch.")
            except requests.RequestException as e:
                printlog(f"Error en la solicitud a Twitch: {e}","ERROR")
        # Si después de todos los intentos no se obtiene confirmación, retornar False
        # printlog(f"{broadcaster_id} sigue offline después de {max_attempts} intentos.")
        return False
    except sqlite3.Error as e:
        # printlog(f"Error al acceder a la base de datos: {e}","ERROR")
        return False

import re
import unicodedata
def clean_text(text):
    # Normalizar texto para quitar acentos y caracteres raros
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    # Eliminar emojis y símbolos no alfabéticos
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
    text = emoji_pattern.sub("", text)

    # Reemplazar saltos de línea, tabulaciones y otras marcas invisibles por espacios
    text = re.sub(r"[\n\r\t\f\v]+", " ", text)
    
    # Colapsar múltiples espacios a uno solo
    text = re.sub(r"\s+", " ", text)

    # Eliminar espacios al inicio y al final
    return text.strip()


async def get_viewers_count(self, channel_name):
        # Obtener el stream del canal usando el client
        streams = await self.client.get_streams(user_logins=[channel_name])
        if streams:
            # La cantidad de viewers estará en streams[0].viewer_count
            return streams[0].viewer_count
        else:
            return 0  # Si el canal no está transmitiendo

def cerrar_conexion(conn, cursor):
    """Cierra una conexión y/o un cursor de base de datos si aún están abiertos."""
    if cursor: # Si hay un cursor, cerrarlo
        try:
            if not cursor.connection:  # Verifica si el cursor ya no tiene conexión
                return
            cursor.close()
        except sqlite3.ProgrammingError:  # Si ya estaba cerrado, no hacer nada
            pass
        except Exception as e:
            printlog(f"Error al cerrar el cursor: {e}","ERROR")
    if conn: # Si hay una conexión, cerrarla
        try:
            conn.close()
        except sqlite3.ProgrammingError:  # Si ya estaba cerrada, no hacer nada
            pass
        except Exception as e:
            printlog(f"Error al cerrar la conexión: {e}","ERROR")

def wordslist(filename):
    try:
        file_folder = os.path.join(os.path.dirname(__file__),"textos")
        file_file = os.path.join(file_folder,filename)  # Ruta del archivo de respuestas
        with open(file_file, "r", encoding="utf-8") as file:
            return set(line.strip().lower() for line in file if line.strip())  # Usamos set para mayor eficiencia
    except FileNotFoundError:
        printlog(f"El archivo {filename} no se encontró en la carpeta textos.","ERROR")
        return set()  # Si el archivo no existe, devolvemos un set vacío

def validar_fecha(bd):
    # Expresión regular para formato YYYY-MM-DD
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    # Verificar formato con regex
    if not re.match(pattern, bd):
        return False, "Formato incorrecto. Usa YYYY-MM-DD."
    # Intentar convertir la cadena en fecha
    try:
        fecha = datetime.strptime(bd, "%Y-%m-%d")
        # Año razonable (ajusta el rango si lo necesitas)
        if fecha.year < 1900 or fecha.year > 2100:
            return False, "El año debe estar entre 1900 y 2100."    
        return True, "Fecha válida."
    
    except ValueError:
        return False, "Fecha inválida. Revisa el día y el mes."

def format_usernames(usernames):
    if len(usernames) > 1:
        # Si hay más de un nombre, lo unimos con " y "
        return " y ".join([f"@{user}" for user in usernames])
    elif len(usernames) == 1:
        # Si solo hay un nombre, lo devolvemos directamente
        return f"@{usernames[0]}"
    else:
        return ""
    
def printlog(message, level="INFO"):
    """
    """
    levels = {
        "INFO": "\033[38;5;49m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "DEBUG": "\033[94m"   # Blue
    }
    
    gray = "\033[90m"
    reset = "\033[0m"
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    date=time.strftime("%Y-%m-%d", time.localtime())


    logs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Logs', f'{date}.log'))
    if not os.path.exists(os.path.dirname(logs_path)):
        os.makedirs(os.path.dirname(logs_path))
    
    if level in levels:
        print(f"{gray}{datetime} {levels[level]} [{level}] - {reset}{message}{reset}")
    else:
        print(f"[UNKNOWN] {message}")


    message = quitar_colores(clean_text(message))
    with open(logs_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"{datetime} - [{level}] - {message}\n")


def quitar_colores(texto_con_color: str) -> str:
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', texto_con_color)