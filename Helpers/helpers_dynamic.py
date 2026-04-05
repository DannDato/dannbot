
import aiohttp
import os
from datetime import datetime, timezone
import random
import sqlite3

#Cargar el token para operaciones con las credenciales
from Helpers.token_loader import load_token
from Helpers.helpers import wordslist, is_channel_online, clean_text, db_cursor
from Helpers.helpers_stats import update_global_stats
from Helpers.printlog import printlog

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

def _get_runtime_token_data():
    return load_token()


def _get_runtime_credentials():
    token_data = _get_runtime_token_data()
    bot_id = token_data.get("bot_id")
    return {
        "client_id": token_data.get("client_id"),
        "bot_id": bot_id,
        "owner_id": token_data.get("owner_id") or bot_id,
        "access_token": token_data.get("access_token"),
        "channel_name": token_data.get("channel_name"),
    }


def _get_steam_credentials():
    token_data = _get_runtime_token_data()
    return {
        "steam_api": os.environ.get("DANNBOT_STEAM_API") or token_data.get("steam_api"),
        "steamid": os.environ.get("DANNBOT_STEAM_ID") or token_data.get("steamID"),
    }


async def analisis(message, userid):
    mensaje=clean_text(message).lower()
    #evaluar si el mensaje contiene palabras malas o buenas
    if any(word in mensaje for word in wordslist("zPalabras_malas.txt")):
        await update_global_stats("xp_Oscuridad",userid,1.25)
    if any(word in mensaje for word in wordslist("zPalabras_buenas.txt")):
        await update_global_stats("xp_Carisma",userid,1.25)
    if any(word in mensaje for word in wordslist("zPalabras_broma.txt")):
        await update_global_stats("xp_Bromista",userid,1.25)
    if any(word in mensaje for word in wordslist("zPalabras_empatia.txt")):
        await update_global_stats("xp_Empatia",userid,1.25)
    if any(word in mensaje for word in wordslist("zPalabras_astuto.txt")):
        await update_global_stats("xp_Astucia",userid,1.25)

async def interactuar(self, message, username):
    credentials = _get_runtime_credentials()
    user = self.create_partialuser(credentials["bot_id"])
    mensaje=clean_text(message).lower()
    #validar que el mensaje no sea dirigido a otra persona para generar respuestas
    if any(word in mensaje for word in ["@"]):
        return
    else:
        if any(word in mensaje for word in ["hola", "holaaa", "wolas"]):
            await user.send_message(sender=self.user, message=f'[BOT] - {gen_response("saludos.txt")} @{username}')

        if any(word in mensaje for word in ["adios", "bye"]):
            await user.send_message(sender=self.user, message=f'[BOT] - {gen_response("despedidas.txt")} @{username}')

        if any(word in mensaje for word in ["oye"]):
            await user.send_message(sender=self.user, message=f'[BOT] - Qué? @{username}')

        if any(word in mensaje for word in ["peruano"]):
            await user.send_message(sender=self.user, message=f'[BOT] - déja en paz a los peruanos @{username}')



async def desafiar(self, username):
    credentials = _get_runtime_credentials()
    user = self.create_partialuser(credentials["bot_id"])
    lnReto = random.randint(0, 2500)
    if await is_channel_online():
        if lnReto == 500: await user.send_message(sender=self.user, message=f'[RETO RANDOM] 🔮 @{username} {gen_response("desafios.txt")}')

#___________________________________________________________________________________________
def gen_response(document):
    try:
        # Lee todas las líneas del archivo
        respuestas_folder = os.path.join(os.path.dirname(__file__),"textos")
        respuestas_file = os.path.join(respuestas_folder,document)  # Ruta del archivo de respuestas
        with open(respuestas_file, "r", encoding="utf-8") as file:
            respuestas = file.readlines()
        # Remueve saltos de línea al final de cada respuesta
        respuestas = [respuesta.strip() for respuesta in respuestas]
        # Genera un número aleatorio dentro del rango de respuestas
        lnResp = random.randint(0, len(respuestas) - 1)
        # Devuelve la respuesta correspondiente
        return respuestas[lnResp]
    except FileNotFoundError:
        return "No encontré el archivo de respuestas 😞 No se como responder."
    except Exception as e:
        return f"Error: {str(e)}"

#___________________________________________________________________________________________
async def get_vips():
    credentials = _get_runtime_credentials()
    headers = {
        'Client-Id': credentials["client_id"],
        'Authorization': f'Bearer {credentials["access_token"]}',
    }

    channel_login = credentials["channel_name"]
    if not channel_login:
        printlog('No hay channel_name configurado para consultar VIPs.', "WARNING")
        return []

    try:
        async with aiohttp.ClientSession() as session:
            user_url = 'https://api.twitch.tv/helix/users'
            async with session.get(user_url, headers=headers, params={'login': channel_login}) as user_resp:
                user_data = await user_resp.json(content_type=None)
                if user_resp.status != 200:
                    printlog(f'Error consultando canal para VIPs ({user_resp.status}): {user_data}', "WARNING")
                    return []

            if not user_data.get('data'):
                printlog(f'No se encontró el canal {channel_login}.', "WARNING")
                return []

            channel_id = user_data['data'][0]['id']
            vips_url = 'https://api.twitch.tv/helix/channels/vips'
            async with session.get(vips_url, headers=headers, params={'broadcaster_id': channel_id}) as vips_resp:
                vips_data = await vips_resp.json(content_type=None)
                if vips_resp.status != 200:
                    printlog(f'Error consultando VIPs ({vips_resp.status}): {vips_data}', "WARNING")
                    return []

            return [vip.get('user_name') for vip in vips_data.get('data', []) if vip.get('user_name')]
    except Exception as e:
        printlog(f'Error obteniendo VIPs: {e}', "WARNING")
        return []

async def get_followers_count():
    credentials = _get_runtime_credentials()
    url = f"https://api.twitch.tv/helix/channels/followers?broadcaster_id={credentials['owner_id']}"
    headers = {
        "Client-Id": credentials["client_id"],
        "Authorization": f"Bearer {credentials['access_token']}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            return data.get("total", 0)

def _ensure_follow_cache_table() -> None:
    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS followage_cache (
                    user_id TEXT NOT NULL,
                    broadcaster_id TEXT NOT NULL,
                    followed_at TEXT,
                    fetched_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, broadcaster_id)
                )
            ''')
    except sqlite3.Error as e:
        printlog(f"Error creando tabla followage_cache: {e}", "ERROR")


def cache_follow_from_event(user_id, broadcaster_id, followed_at=None) -> None:
    """Guarda followage desde EventSub follow sin sobrescribir datos existentes.

    - Inserta solo si no existe (user_id, broadcaster_id).
    - Si ya existe, no actualiza la fecha original.
    """
    if not user_id or not broadcaster_id:
        return

    _ensure_follow_cache_table()

    if isinstance(followed_at, datetime):
        followed_at_value = followed_at.astimezone(timezone.utc).isoformat()
    elif isinstance(followed_at, str):
        followed_at_value = followed_at
    else:
        followed_at_value = datetime.now(timezone.utc).isoformat()

    fetched_at_value = datetime.now(timezone.utc).isoformat()

    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute(
                '''
                INSERT INTO followage_cache (user_id, broadcaster_id, followed_at, fetched_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, broadcaster_id) DO NOTHING
                ''',
                (str(user_id), str(broadcaster_id), followed_at_value, fetched_at_value)
            )
    except sqlite3.Error as e:
        printlog(f"Error guardando followage desde evento: {e}", "WARNING")


async def get_follow_age(user_id, force_refresh: bool = False, cache_hours: int = 12):
    """Obtiene la antiguedad de follow usando Helix con cache local.

    Retorna (delta, followed_at_datetime) o (None, None) si no sigue el canal.
    """
    if not user_id:
        return None, None

    credentials = _get_runtime_credentials()
    owner_id = credentials["owner_id"]

    _ensure_follow_cache_table()
    now = datetime.now(timezone.utc)

    if not force_refresh:
        try:
            with db_cursor(DB_PATH) as (_, cursor):
                cursor.execute(
                    '''
                    SELECT followed_at, fetched_at
                    FROM followage_cache
                    WHERE user_id = ? AND broadcaster_id = ?
                    ''',
                    (str(user_id), str(owner_id))
                )
                row = cursor.fetchone()

            if row:
                followed_at_cached, fetched_at_cached = row
                fetched_dt = datetime.fromisoformat(fetched_at_cached.replace("Z", "+00:00"))
                age_seconds = (now - fetched_dt).total_seconds()
                if age_seconds <= cache_hours * 3600:
                    if followed_at_cached:
                        followed_dt = datetime.fromisoformat(followed_at_cached.replace("Z", "+00:00"))
                        return now - followed_dt, followed_dt
                    # Cache negativo corto para evitar "pegarse" ante errores transitorios.
                    if age_seconds <= 300:
                        return None, None
        except (sqlite3.Error, ValueError) as e:
            printlog(f"Error leyendo cache followage: {e}", "WARNING")

    url = "https://api.twitch.tv/helix/channels/followers"
    headers = {
        "Client-ID": credentials["client_id"],
        "Authorization": f"Bearer {credentials['access_token']}"
    }
    params = {
        "broadcaster_id": owner_id,
        "user_id": str(user_id),
        "first": 1
    }

    followed_at = None
    api_ok = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                data = await resp.json()
                if resp.status == 200:
                    api_ok = True
                    if data.get("data"):
                        followed_at = data["data"][0].get("followed_at")
                elif resp.status != 200:
                    printlog(f"Error Helix followage ({resp.status}): {data}", "WARNING")
    except Exception as e:
        printlog(f"Error consultando Helix followage: {e}", "WARNING")

    if api_ok:
        try:
            with db_cursor(DB_PATH, commit=True) as (_, cursor):
                cursor.execute(
                    '''
                    INSERT INTO followage_cache (user_id, broadcaster_id, followed_at, fetched_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, broadcaster_id)
                    DO UPDATE SET
                        followed_at=COALESCE(followage_cache.followed_at, excluded.followed_at),
                        fetched_at=excluded.fetched_at
                    ''',
                    (str(user_id), str(owner_id), followed_at, now.isoformat())
                )
        except sqlite3.Error as e:
            printlog(f"Error guardando cache followage: {e}", "WARNING")

    if followed_at:
        try:
            followed_dt = datetime.fromisoformat(followed_at.replace("Z", "+00:00"))
            return now - followed_dt, followed_dt
        except ValueError:
            return None, None

    return None, None

async def get_viewers():
    credentials = _get_runtime_credentials()
    url = "https://api.twitch.tv/helix/streams"
    headers = {
        "Client-ID": credentials["client_id"],
        "Authorization": f"Bearer {credentials['access_token']}"
    }
    params = {"user_id": str(credentials["owner_id"])}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200:
                    printlog(f"Error consultando viewers ({resp.status}): {data}", "WARNING")
                    return 0
                if data.get("data"):
                    return int(data["data"][0].get("viewer_count", 0))
    except Exception as e:
        printlog(f"Error al consultar viewers: {e}", "WARNING")

    return 0  # si está offline o hubo error


#___________________________________________________________________________________________
async def get_steam_library():
    steam_credentials = _get_steam_credentials()
    # Endpoint de la API de Steam
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"

    # Parámetros de la solicitud
    params = {
        "key": steam_credentials["steam_api"],  # Tu API Key de Steam
        "steamid": steam_credentials["steamid"],  # Tu Steam ID64
        "include_appinfo": True,  # Incluye información del juego (como el título)
        "include_played_free_games": True,  # Incluye juegos gratuitos
        "format": "json"  # Respuesta en formato JSON
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    printlog("Error al obtener la biblioteca de Steam:","ERROR")
                    return []
                data = await response.json(content_type=None)

        # Verificar si hay juegos en la biblioteca
        if "response" in data and "games" in data["response"]:
            games = data["response"]["games"]
            return [game["name"] for game in games]  # Devuelve una lista de títulos
        else:
            printlog("No se encontraron juegos en la biblioteca.")
            return []
    except aiohttp.ClientError:
        printlog(f"Error al obtener la biblioteca de Steam:","ERROR")
        return []


#___________________________________________________________________________________________

