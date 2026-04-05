import requests
import unicodedata
import os
import sqlite3
import re
import aiohttp
import time
from contextlib import contextmanager
from datetime import datetime
from openai import OpenAI, OpenAIError


#Cargar el token para operaciones con las credenciales
from Helpers.token_loader import load_token
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

_broadcaster_id_cache = None
_broadcaster_cache_key = None

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

def get_broadcaster_id(force_refresh=False):
    global _broadcaster_id_cache, _broadcaster_cache_key

    token_data = load_token()
    access_token = token_data.get("access_token")
    client_id = token_data.get("client_id")
    channel_name = token_data.get("channel_name")
    cache_key = (channel_name, client_id, access_token)

    if _broadcaster_id_cache and not force_refresh and _broadcaster_cache_key == cache_key:
        return _broadcaster_id_cache

    if not channel_name or not client_id or not access_token:
        return 0

    # Hacer la solicitud a la API de Twitch
    url = f"https://api.twitch.tv/helix/users?login={channel_name}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return 0

    # Extraer y mostrar el ID del usuario
    if "data" in data and len(data["data"]) > 0:
        _broadcaster_id_cache = data["data"][0]["id"]
        _broadcaster_cache_key = cache_key
        return _broadcaster_id_cache

    return 0
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


def is_mod(ctx):
    return bool(getattr(ctx.chatter, "moderator", False))

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
        with db_cursor(DB_PATH) as (_, cursor):
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
        if result and result[0] > 0:
            # printlog("Un stream está activo según la base de datos.","WARNING")
            return True
        # printlog("No hay stream activo en la base de datos, verificando en Twitch...","ERROR")
        # Si no hay registro en la base de datos, realizar solicitud a Twitch
        broadcaster_id = get_broadcaster_id()
        if not broadcaster_id:
            return False

        async with aiohttp.ClientSession() as session:
            for attempt in range(max_attempts):
                try:
                    async with session.get(f'https://www.twitch.tv/{broadcaster_id}', timeout=10) as resp:
                        contents = await resp.text()
                        if 'isLiveBroadcast' in contents:
                            printlog(f"{broadcaster_id} está en línea según Twitch.","INFO")
                            return True
                        # if attempt == max_attempts: printlog(f"{broadcaster_id} está offline según Twitch.")
                except Exception as e:
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


def create_db_connection(db_path=DB_PATH):
    return sqlite3.connect(db_path, timeout=30)


@contextmanager
def db_cursor(db_path=DB_PATH, *, commit=False):
    conn = None
    cursor = None
    try:
        conn = create_db_connection(db_path)
        cursor = conn.cursor()
        yield conn, cursor
        if commit:
            conn.commit()
    except sqlite3.Error:
        if conn:
            conn.rollback()
        raise
    finally:
        cerrar_conexion(conn, cursor)

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

async def parse_flexible_date(date_str: str) -> tuple[bool, str]:
    """
    Intenta parsear una fecha en múltiples formatos (local parsing).
    Si falla, utiliza OpenAI para interpretar la entrada y convertirla a YYYY-MM-DD.

    Args:
        date_str: Cadena de fecha en cualquier formato (ej: "25-12-1999", "25/12/99", "15 de octubre del 1997")

    Returns:
        (True, "YYYY-MM-DD") si es válida, (False, None) si falla
    """

    # Diccionarios para nombres de meses en español e inglés
    months_es = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
        'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
    }

    months_en = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7,
        'aug': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }

    all_months = {**months_es, **months_en}

    # Formatos locales a intentar
    local_formats = [
        "%Y-%m-%d",      # 1999-12-25
        "%d-%m-%Y",      # 25-12-1999
        "%d/%m/%Y",      # 25/12/1999
        "%d/%m/%y",      # 25/12/99
        "%d-%m-%y",      # 25-12-99
        "%Y/%m/%d",      # 1999/12/25
        "%m/%d/%Y",      # 12/25/1999
        "%m-%d-%Y",      # 12-25-1999
        "%d.%m.%Y",      # 25.12.1999
        "%Y.%m.%d",      # 1999.12.25
        "%d%m%Y",        # 25121999
        "%Y%m%d",        # 19991225
    ]

    # Intentar parsear con formatos locales simples
    for fmt in local_formats:
        try:
            fecha = datetime.strptime(date_str.strip(), fmt)
            # Validar rango razonable de año
            if 1900 <= fecha.year <= 2100:
                return True, fecha.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Intentar parsear patrones con nombres de meses (ej: "15 de octubre del 1997")
    date_lower = date_str.lower().strip()

    # Buscar patrón: número + opcional(de) + nombre_mes + opcional(del/de) + número
    for month_name, month_num in all_months.items():
        # Patrones: "15 de octubre del 1997", "15 octubre 1997", "15 de octubre 97", etc.
        patterns = [
            rf"(\d{{1,2}})\s+de\s+{month_name}\s+del\s+(\d{{2,4}})",      # 15 de octubre del 1997
            rf"(\d{{1,2}})\s+de\s+{month_name}\s+de\s+(\d{{2,4}})",       # 15 de octubre de 1997
            rf"(\d{{1,2}})\s+{month_name}\s+(\d{{2,4}})",                 # 15 octubre 1997
            rf"(\d{{1,2}})\s+de\s+{month_name}\s+(\d{{2,4}})",            # 15 de octubre 1997
        ]

        for pattern in patterns:
            match = re.search(pattern, date_lower)
            if match:
                day = match.group(1)
                year = match.group(2)

                # Convertir año de 2 dígitos a 4 si es necesario
                if len(year) == 2:
                    year = int(year)
                    # Si es 00-50, asumir 2000-2050; si es 51-99, asumir 1951-1999
                    if year <= 50:
                        year = 2000 + year
                    else:
                        year = 1900 + year
                    year = str(year)

                try:
                    fecha = datetime(int(year), month_num, int(day))
                    if 1900 <= fecha.year <= 2100:
                        return True, fecha.strftime("%Y-%m-%d")
                except ValueError:
                    continue

    # Si local parsing falla, intentar con OpenAI
    try:
        client = OpenAI()

        prompt = (
            f"Parse this date string into YYYY-MM-DD format only. "
            f"If it's ambiguous, assume DD/MM/YYYY format (European/Latin standard). "
            f"Return ONLY the date in YYYY-MM-DD format. "
            f"If you cannot parse it, return: INVALID\n\n"
            f"Input: {date_str}"
        )

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a date parser. Respond with only the date in YYYY-MM-DD format or INVALID."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20,
            temperature=0
        )


        if not completion.choices:
            printlog("No se recibió respuesta de OpenAI para el parsing de fecha.", level="WARNING")
            return False, None

        response = completion.choices[0].message.content.strip()

        # Verificar que la respuesta sea un formato válido YYYY-MM-DD
        if response == "INVALID" or not re.match(r"^\d{4}-\d{2}-\d{2}$", response):
            printlog(f"OpenAI no pudo parsear la fecha correctamente. Respuesta: {response}", level="WARNING")
            return False, None

        # Validar que sea una fecha real
        try:
            fecha = datetime.strptime(response, "%Y-%m-%d")
            if 1900 <= fecha.year <= 2100:
                printlog(f"Fecha parseada exitosamente por OpenAI: {response}", level="INFO")
                return True, response
        except ValueError:
            printlog(f"OpenAI devolvió un formato correcto pero fecha inválida: {response}", level="WARNING")
            return False, None

    except OpenAIError:
        printlog("Error al comunicarse con OpenAI para el parsing de fecha.", level="ERROR")
        return False, None
    except Exception:
        printlog("Error inesperado durante el parsing de fecha con OpenAI.", level="ERROR")
        return False, None
    printlog("No se pudo parsear la fecha con métodos locales ni con OpenAI.", level="WARNING")
    return False, None



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