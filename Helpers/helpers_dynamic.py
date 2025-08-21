
import requests
import aiohttp
import os
from datetime import datetime, timezone
import random

#Cargar el token para operaciones con las credenciales
from Helpers.token_loader import load_token
from Helpers.helpers import wordslist, is_channel_online, clean_text
from Helpers.helpers_stats import update_global_stats
from Helpers.printlog import printlog

#asignacion de credenciales
token_data = load_token()
CLIENT_ID = token_data.get("client_id")
CLIENT_SECRET = token_data.get("client_secret")
BOT_ID = token_data.get("bot_id")
OWNER_ID = token_data.get("bot_id")  # canal objetivo del bot
ACCESS_TOKEN = token_data.get("access_token")
BOT_NAME = token_data.get("bot_name")
CHANNEL_NAME = token_data.get("channel_name")
INITIAL_CHANNELS = token_data.get("initial_channels", [])
if CHANNEL_NAME not in INITIAL_CHANNELS:
    INITIAL_CHANNELS.append(CHANNEL_NAME)
steam_api = token_data.get("steam_api")
steamid = token_data.get("steamID")


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
    user = self.create_partialuser(BOT_ID)
    
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
            
        # if any(word in mensaje for word in ["pito", "pene", "verga"]):
        #     await ctx.send(f'[BOT] -  @{message.author.name} {gen_response("regaños.txt")}')

    
async def desafiar(self, username):
    user = self.create_partialuser(BOT_ID)
    lnReto = random.randint(0, 1000)
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
    # Obtener el ID de tu canal
    user_url = f'https://api.twitch.tv/helix/users?login={INITIAL_CHANNELS}'
    headers = {
        'Client-Id': CLIENT_ID,
        'Authorization': f'Bearer {ACCESS_TOKEN}',
    }

    user_response = requests.get(user_url, headers=headers)
    user_data = user_response.json()

    if user_data['data']:
        channel_id = user_data['data'][0]['id']
        # Obtener la lista de VIPs del canal
        vips_url = f'https://api.twitch.tv/helix/channels/vips?broadcaster_id={channel_id}'
        vips_response = requests.get(vips_url, headers=headers)
        vips_data = vips_response.json()
        
        # Imprimir los nombres de los VIPs
        if 'data' in vips_data:
            vips = [vip['user_name'] for vip in vips_data['data']]
            return vips
        else:
            printlog(f'No se encontraron VIPs en el canal {INITIAL_CHANNELS}.')
    else:
        printlog(f'No se encontró el canal {INITIAL_CHANNELS}.',"WARNING")

async def get_followers_count():
    url = f"https://api.twitch.tv/helix/channels/followers?broadcaster_id={BOT_ID}"
    headers = {
        "Client-Id": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            return data.get("total", 0)
        
def get_follow_age(user_id):
    """
    user_id: id del usuario que sigue
    """
    url = "https://api.twitch.tv/helix/channels/followers"
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    params = {
        "from_id": user_id,   # el seguidor
        "to_id": BOT_ID,   # el canal seguido (tú)
        "broadcaster_id":BOT_ID
    }


    res = requests.get(url, headers=headers, params=params)
    data = res.json()
    print(res)
    print(data)
    if res.status_code == 200 and data.get("data"):
        followed_at = data["data"][0]["followed_at"]
        dt = datetime.fromisoformat(followed_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return now - dt, dt
    else:
        return None, None
    
def get_viewers():
    url = "https://api.twitch.tv/helix/streams"
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    params = { "user_login": BOT_ID}
    response = requests.get(url, headers=headers, params=params).json()

    if response.get("data"):
        stream_info = response["data"][0]
        viewers = stream_info["viewer_count"]
        return viewers
    else:
        return 0  # si está offline


#___________________________________________________________________________________________
def get_steam_library():
    # Endpoint de la API de Steam
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"

    # Parámetros de la solicitud
    params = {
        "key": steam_api,  # Tu API Key de Steam
        "steamid": steamid,  # Tu Steam ID64
        "include_appinfo": True,  # Incluye información del juego (como el título)
        "include_played_free_games": True,  # Incluye juegos gratuitos
        "format": "json"  # Respuesta en formato JSON
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Verificar si hay juegos en la biblioteca
        if "response" in data and "games" in data["response"]:
            games = data["response"]["games"]
            return [game["name"] for game in games]  # Devuelve una lista de títulos
        else:
            printlog("No se encontraron juegos en la biblioteca.")
            return []
    except requests.exceptions.RequestException as e:
        printlog(f"Error al obtener la biblioteca de Steam:","ERROR")
        return []


#___________________________________________________________________________________________

