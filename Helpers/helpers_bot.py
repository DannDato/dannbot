import sqlite3
import os
from datetime import datetime
import emoji
import asyncio
import random 
import json
import sys
import urllib.parse
import aiohttp
import requests
from urllib.parse import urlencode

from Helpers.printlog import printlog
from Helpers.helpers import normalize_username, clean_text, cerrar_conexion, is_channel_online, format_usernames, get_app_access_token, db_cursor
from Helpers.helpers_dynamic import gen_response, interactuar, desafiar, analisis
from Helpers.helpers_stats import update_global_stats, today_birthdays, week_birthdays

from Helpers.token_loader import load_token as load_token_file
from Helpers.required_scopes import required_scopes
from Helpers.colors import white, resetColor, colorConvert

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')
token_data = load_token_file()
OPENAI_API_KEY = token_data.get("openai_api_key")

# Scopes recomendados para maximo acceso
REQUIRED_SCOPES = [
    "chat:read",
    "chat:edit",
    "channel:read:redemptions",
    "channel:read:subscriptions",
    "channel:read:goals",
    "channel:read:polls",
    "channel:read:predictions",
    "channel:manage:redemptions",
    "channel:manage:polls",
    "channel:manage:predictions",
    "channel:read:hype_train",
    "channel:read:charity",
    "channel:read:vips",
    "channel:read:editors",
    "moderator:read:followers",
    "moderation:read",
    "bits:read",
    "whispers:read",
    "whispers:edit"
]

OAUTH_BASE_URL = "https://id.twitch.tv/oauth2/authorize"
REDIRECT_URI = "http://localhost:8080"

TOKEN_FIELDS = [
    "access_token",
    "client_id",
    "client_secret",
    "channel_name",
    "owner_id",
    "BOT_ID",
    "bot_name"
]

HEADERS_TEMPLATE = lambda token, client_id: {
    "Authorization": f"Bearer {token}",
    "Client-ID": client_id,
}

API_USERS_ENDPOINT = "https://api.twitch.tv/helix/users"
TOKEN_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\Credentials', 'token.json'))



def unload_bot_modules(prefixes):
    """
    Elimina módulos de sys.modules que coincidan con los prefijos especificados.

    :param prefixes: Lista de prefijos de módulos a eliminar (por ejemplo ['Commands.', 'Helpers.'])
    """
    modules_to_delete = [name for name in sys.modules if any(name.startswith(p) for p in prefixes)]
    printlog("Borrando modulos residuales...")
    for module_name in modules_to_delete:
        printlog(f"Eliminando caché del módulo: {module_name}", 'DEBUG')
        del sys.modules[module_name]

def load_token_data():
    with open(TOKEN_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_token_data(data):
    with open(TOKEN_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

async def fetch_user_info(session, headers, login=None):
    params = {"login": login} if login else {}
    async with session.get(API_USERS_ENDPOINT, headers=headers, params=params) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise Exception(f"Error {resp.status} al obtener datos del usuario: {text}")
        data = await resp.json()
        if not data['data']:
            raise Exception("Usuario no encontrado")
        return data['data'][0]  # Regresa el primer usuario

async def resolve_user_ids_and_update_token(token_path=TOKEN_PATH):
    if not os.path.exists(token_path):
        printlog("No se encontró el archivo token.json. Se solicitará información...","WARNING")
        token_data = {}
    else:
        with open(token_path, "r") as f:
            token_data = json.load(f)

    client_id = token_data.get("client_id")
    client_secret = token_data.get("client_secret")

    if not client_id or not client_secret:
        printlog("Faltan 'client_id' o 'client_secret' en token.json","ERROR")
        sys.exit("Debes volver a generar el token.json con client_id y client_secret")

    access_token = token_data.get("access_token")
    if not access_token:
        print("\nNo se encontró el token de acceso. Debes generarlo desde la cuenta del canal principal.\n")
        query = urlencode({
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "token",
            "scope": " ".join(REQUIRED_SCOPES),
            "force_verify": "true"
        })
        print(f"🔑 Abre esta URL en el navegador y copia el token:\n{OAUTH_BASE_URL}?{query}\n")
        access_token = input("Pega el token de acceso: ").strip()
        token_data["access_token"] = access_token

    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }

    if not token_data.get("channel_name"):
        token_data["channel_name"] = input("Nombre del canal (donde estará activo el bot): ").strip()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.twitch.tv/helix/users?login=" + token_data["channel_name"], headers=headers) as resp:
                data = await resp.json()
                if "data" in data and data["data"]:
                    user_data = data["data"][0]
                    token_data["bot_name"] = user_data["login"]
                    token_data["bot_id"] = user_data["id"]
                    token_data["channel_id"] = user_data["id"]
                    token_data["OWNER_ID"] = user_data["id"]
                    token_data["initial_channels"] = [user_data["login"]]
                else:
                    printlog(f"Error al obtener datos del canal: {data}","ERROR")
                    sys.exit(1)
    except Exception as e:
        printlog(f"Error al obtener datos del canal: {e}","ERROR")
        sys.exit(1)

    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=4)

    printlog("✔ token.json actualizado correctamente")


def get_app_access_token(client_id, scopes, redirect_uri="http://localhost:8080"):
    """
    Genera la URL de OAuth para obtener el token de acceso de Twitch.
    """
    base_url = "https://id.twitch.tv/oauth2/authorize"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "token",
        "scope": " ".join(scopes),
    }
    oauth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return oauth_url


def check_credentials_or_generate():
    """
    Verifica o genera el archivo token.json con client_id, client_secret y access_token válidos.
    Si no existen, solicita al usuario que los genere a través del flujo OAuth.
    Si el token es inválido, permite regenerarlo en consola.
    """
    token_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Credentials', 'token.json'))

    def ask_for_credentials_and_save():
        print("🔐 Necesitamos tus credenciales de desarrollador de Twitch.")
        client_id = input("CLIENT_ID: ").strip()
        client_secret = input("CLIENT_SECRET: ").strip()
        oauth_url = get_app_access_token(client_id, required_scopes)
        print(f"\n🌐 Abre esta URL para generar el access_token")
        print(oauth_url)
        access_token = input("\n🔑 Pega aquí el access_token: ").strip()
        channel_name = input("🎯 Nombre del canal donde estará activo el bot: ").strip()

        data = {
            "access_token": access_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "channel_name": channel_name,
            "initial_channels": [channel_name]
        }

        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        print("✅ Se ha creado el archivo token.json correctamente.\n")

    if not os.path.exists(token_path):
        printlog(f"{white}No se encontró el archivo token.json. Generando nuevo...",'WARNING')
        ask_for_credentials_and_save()
        return

    with open(token_path, 'r', encoding='utf-8') as f:
        token_data = json.load(f)

    # Verificar que existan los campos básicos
    if not all(k in token_data for k in ("access_token", "client_id", "client_secret")):
        printlog(f"{white}Faltan campos en el archivo token.json. Regenerando...","WARNING")
        ask_for_credentials_and_save()
        return

    # Verificar si el access_token coincide con el client_id
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}",
        "Client-Id": token_data['client_id']
    }

    response = requests.get("https://api.twitch.tv/helix/users", headers=headers)
    if response.status_code == 401:
        printlog(f"{white}❌ El token no es válido o no coincide con el client_id.","ERROR")
        print("⚠️  El token parece haber expirado o no coincide con tu app.")
        ask_for_credentials_and_save()
        return
    elif response.status_code != 200:
        printlog(f"{white}Error inesperado verificando token: {response.status_code} - {response.text}","ERROR")
        sys.exit(1)

    printlog(f"{white}✅ Token validado correctamente.")



def delete_token():
    # Ruta del archivo token.json
    token_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Credentials', 'token.json'))
    
    # Comprobar si el archivo existe
    if os.path.exists(token_path):
        # Abrir el archivo y cargar su contenido
        with open(token_path, 'r') as token_file:
            token_data = json.load(token_file)
        
        # Eliminar la clave del token
        if 'access_token' in token_data:
            del token_data['access_token']
            print("Token eliminado exitosamente.")
        
        # Guardar el archivo actualizado (vacío o sin el token)
        with open(token_path, 'w') as token_file:
            json.dump(token_data, token_file, indent=4)
    else:
        print(f"El archivo {token_path} no existe.")

#Función anidada en el event listener JOIN
async def user_joined(self, user):
    if user.name not in ('streamelements','nightbot','dannprod', 'dannievt'): #Exclusión de bots externos
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = normalize_username(user.name)

        user_data = await self.fetch_users(names=[user.name])  # Obtiene información completa del usuario
        if user_data:
            user_info = user_data[0]  # La API devuelve una lista, tomamos el primer elemento
            userid = user_info.id
            await new_user(user_info)
            # Conectar a la base de datos (si no existe, se creará automáticamente)
            try:
                await count_user_joined(username)
                with db_cursor(DB_PATH, commit=True) as (_, cursor):
                    cursor.execute('''INSERT INTO history_users (user, date)VALUES (?, ?)''', (userid, timestamp))
                printlog(f'\033[38;5;154m {username} se ha unido \033[0m')

            except sqlite3.Error as e:
                printlog(f'{username} se ha unido')
                printlog(f"Error al insertar el usuario en la base de datos: {e}","ERROR")
        

async def read_save_chat(self, message):
    if message.author:
        """
        Gestiona la tabla de chat del mes actual en la base de datos.
        Crea la tabla si no existe e inserta los datos proporcionados.

        :param db_path: Ruta a la base de datos SQLite.
        :param username: Nombre de usuario.
        :param userid: ID de usuario.
        :param message: Mensaje del usuario.
        """
        channel = self.get_channel(self.nick) #Obtener el canal del bot para poder enviar mensajes, es como el ctx
        message.text=message.text.lower().strip()
        await self.handle_commands(message)
        await interactuar(channel,message)
        await analisis(channel,message)
        await desafiar(channel,message)
        userid = None
        try:
            username = normalize_username(message.author.name)
            userid=message.author.id
            
            #Nuevo usuario del canal
            await new_user(message.author)

            message = clean_text(message.content)
            # Obtener fecha actual
            now = datetime.now()
            year = now.year
            month = now.month
            table_name = f"chat_{year}{month:02}"

            with db_cursor(DB_PATH, commit=True) as (_, cursor):
                cursor.execute('''
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table' AND name=?;
                ''', (table_name,))
                table_exists = cursor.fetchone() is not None
                if not table_exists:
                    cursor.execute(f'''
                        CREATE TABLE {table_name} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user TEXT,
                            message TEXT,
                            date TEXT,
                            timestamp TEXT
                        );
                    ''')
                    printlog(f"Tabla '{table_name}' creada correctamente.")

                cursor.execute(f'''
                    INSERT INTO {table_name} (user, message, date, timestamp)
                    VALUES (?, ?, ?, ?);
                ''', (userid, message, now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d %H:%M:%S')))

            await update_stream_data("total_messages",1)
            await update_global_stats("messages",userid,1)

            printlog(f'\033[38;5;141m{username}\033[38;5;255m {message} \033[0m')
            
        except sqlite3.Error as e:
            printlog(f"Error al gestionar la tabla de chat: {e}","ERROR")
        finally:
            if userid is not None:
                await update_global_stats("xp_Voluntad",userid,0.15)
  

async def update_stream_data(stat_category, value):

    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('''
                SELECT date 
                FROM stream_data
                WHERE accion = "start_stream"
                AND NOT EXISTS (
                    SELECT 1
                    FROM stream_data AS subquery
                    WHERE subquery.accion = "end_stream"
                    AND subquery.date >= stream_data.date
                )
                ORDER BY date ASC
                LIMIT 1;
            ''')
            result = cursor.fetchone()
            if not result:
                return None

            cursor.execute(f'''
                SELECT value FROM stream_data
                WHERE accion = "{stat_category}" AND DATETIME(date)>= DATETIME('{result[0]}')
            ''')
            result = cursor.fetchone()

            if result:
                hvalue = int(result[0]) + value
                cursor.execute(f'''
                    UPDATE stream_data
                    SET value = ?
                    WHERE accion = ? AND date like '%{current_date}%'
                ''', (hvalue, stat_category))
            else:
                current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO stream_data (accion, value, date)
                    VALUES (?, ?, ?)
                ''', (stat_category, value, current_date))

        return True

    except sqlite3.Error as e:
        printlog(f"Error al registrar conteo de mensajes del stream en la base de datos: {e}","ERROR")
        return None
    
async def count_user_joined(user):
    try:
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with db_cursor(DB_PATH) as (_, cursor):
            cursor.execute('''
                SELECT date 
                FROM stream_data    
                WHERE accion = "start_stream"
                AND NOT EXISTS (
                    SELECT 1
                    FROM stream_data AS subquery
                    WHERE subquery.accion = "end_stream"
                    AND subquery.date >= stream_data.date
                )
                ORDER BY date ASC
                LIMIT 1;
            ''')
            result = cursor.fetchone()
            if not result:
                return None

            cursor.execute(f'''
                SELECT user FROM history_users
                WHERE DATETIME(date)>= DATETIME('{result[0]}')
                AND user=?
            ''', (user,))
            result = cursor.fetchone()

        if result:
            return False

        await update_stream_data("total_users",1)
        return True

    except sqlite3.Error as e:
        printlog(f"Error al registrar conteo de Usuarios del stream en la base de datos: {e}","ERROR")
        return None
    
#Timers para mensajes aleatorios
async def send_timed_messages(self, user):
    """Envía mensajes aleatorios desde un archivo de texto en intervalos de tiempo."""
    while True:
        minT=1800
        maxT=2400
        sleep_time = random.randint(minT, maxT)
        await asyncio.sleep(sleep_time)  # Esperar antes del primer mensaje
        if await is_channel_online(): # Verificar si el canal está en vivo
            await user.send_message(sender=self.user, message=f'[BOT] {gen_response("mensajes_twitch.txt")}')
            sleep_time = random.randint(minT, maxT)
            
#Timers para mensajes aleatorios
async def happy_birthday(self, user):
    """Envía mensajes aleatorios desde un archivo de texto en intervalos de tiempo."""
    while True:
        minT=1800
        maxT=2400
        sleep_time = random.randint(minT, maxT)
        await asyncio.sleep(sleep_time)  # Esperar antes del mensaje
        birthdays = await today_birthdays()
        if await is_channel_online() and birthdays[0]==True:
            users = format_usernames(birthdays[1])
            await user.send_message(sender=self.user, message=f'[BOT] - 🥳 HOY ESTAMOS DE FIESTA, es el cumpleaños de {users} 🎉')

        nBirthdays = await week_birthdays()
        if await is_channel_online() and nBirthdays[0]==True:
            nusers = format_usernames(nBirthdays[1])
            await user.send_message(sender=self.user, message=f'[BOT] - Recuerden que esta semana tenemos el cumpleaños de {nusers} 🎉')
                


async def new_user(uid, uname):
    userid = uid  # Convertir a string por si la DB maneja `TEXT`
    username = uname
    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('SELECT username FROM users WHERE twitch_id = ?', (userid,))
            result = cursor.fetchone()
            update = False
            if result:
                if result[0] != username:
                    cursor.execute('UPDATE users SET username = ? WHERE twitch_id = ?', (username, userid))
                    update = True
            else:
                cursor.execute('INSERT INTO users (twitch_id, username) VALUES (?, ?)', (userid, username))
                update = True

            if update:
                tablas = ['stats_channel', 'clanes']
                for tabla in tablas:
                    cursor.execute(f'UPDATE {tabla} SET user = ? WHERE user = ?', (userid, username))
                printlog(f'\033[38;5;154m {username} (ID: {userid}) registrado/actualizado \033[0m')

    except sqlite3.Error as e:
        printlog(f"Error al registrar usuario {username} (ID: {userid}): {e}")


async def save_current_data():
    """
        Obtiene los numeros actuales del stream como:
        Viewers, Followers, subs 
        y los registra en las tablas para las estadísticas
    """
    # Datos de la API
    token_data = load_token_file()
    access_token = token_data.get("access_token")
    client_id = token_data.get("client_id")
    initial_channels = token_data.get("initial_channels", [])
    broadcaster_id = token_data.get("broadcaster_id")
    
    # while True: 
    #     # Aqui se pondria el codigo de la obtención de estadísticas...
    #           # SI TUVIERA UNO!!!!!

    #     await asyncio.sleep(2)

def deEmojify(text):
    return emoji.get_emoji_regexp().sub(r'', text.decode('utf8'))
    
