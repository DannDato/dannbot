import logging
import requests
import os
from datetime import datetime
import random

#Cargar el token para operaciones con las credenciales
from Helpers.token_loader import load_token
#asignacion de credenciales
token_data = load_token()
access_token = token_data.get("access_token")
client_id = token_data.get("client_id")
initial_channels = token_data.get("initial_channels", [])
broadcaster_id = token_data.get("broadcaster_id")
steam_api = token_data.get("steam_api")
steamid = token_data.get("steamID")



async def interactuar(ctx, message):
    mensaje = message.content.lower()
    if any(word in mensaje for word in ["hola", "holaaa", "wolas"]):
        await ctx.send(f'[BOT] - {gen_response("saludos.txt")} @{message.author.name}')

    if any(word in mensaje for word in ["adios", "bye"]):
        await ctx.send(f'[BOT] - {gen_response("despedidas.txt")} @{message.author.name}')

    if any(word in mensaje for word in ["oye"]):
        await ctx.send(f'[BOT] - Qué? @{message.author.name}')

    if any(word in mensaje for word in ["peruano"]):
        await ctx.send(f'[BOT] - déja en paz a los peruanos @{message.author.name}')

    if any(word in mensaje for word in ["pito", "pene", "verga"]):
        await ctx.send(f'[BOT] -  @{message.author.name} {gen_response("regaños.txt")}')


async def desafiar(ctx, message):
    lnReto = random.randint(0, 300)
    if lnReto == 49: await ctx.send(f'[BOT] - @{message.author.name} {gen_response("desafios.txt")}')

#___________________________________________________________________________________________
def gen_response(document):
    try:
        # Lee todas las líneas del archivo
        respuestas_folder = os.path.join(os.path.dirname(__file__),"textos")
        respuestas_file = os.path.join(respuestas_folder,document)  # Ruta del archivo basado en la fecha
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
    user_url = f'https://api.twitch.tv/helix/users?login={initial_channels}'
    headers = {
        'Client-Id': client_id,
        'Authorization': f'Bearer {access_token}',
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
            logging.info(f'No se encontraron VIPs en el canal {initial_channels}.')
    else:
        logging.warning(f'No se encontró el canal {initial_channels}.')

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
            logging.info("No se encontraron juegos en la biblioteca.")
            return []
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al obtener la biblioteca de Steam: {e}")
        return []


#___________________________________________________________________________________________

