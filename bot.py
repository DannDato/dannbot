#Librerias de control de consola y conexión a twitch
import asyncio
import logging
import random
from logging.handlers import TimedRotatingFileHandler
from twitchio.ext import commands


# Importar módulos (Comandos)
from Commands.admin import admin_commands
from Commands.stats import stats_commands
from Commands.general import general_commands
from Commands.dynamic import dynamic_commands
from Commands.xp import xp_commands

# Importar Helpers basicos del bot
from Helpers.helpers_bot import read_save_chat, user_joined, save_current_data
from Helpers.helpers_dynamic import gen_response, interactuar, desafiar
from Helpers.helpers import is_channel_online, get_viewers_count

#Importar configuraciónes
from Helpers.token_loader import load_token
from Helpers.console_log import init_console, animated_message

init_console() #Inicializar configuración de la consola (logging y colorlog)

# Cargar credenciales desde el archivo token.json
token_data = load_token()
access_token = token_data.get("access_token")
client_id = token_data.get("client_id")
initial_channels = token_data.get("initial_channels", [])
broadcaster_id = token_data.get("broadcaster_id")

# Verificar credenciales esenciales
if not access_token or not client_id or not broadcaster_id:
    logging.error(" Error: Faltan credenciales esenciales en token.json.")
    exit()

# Clase principal del bot
class TwitchBot(commands.Bot):

    #inicialización del bot
    def __init__(self):
        super().__init__( #Aplicación de credenciales para la conexión con la API
            token=access_token,
            prefix="!",
            nick="diosito",  # Nombre de usuario del bot
            initial_channels=initial_channels if isinstance(initial_channels, list) else [initial_channels],
        )
        animated_message("Inicializando...","\033[38;5;221m")
        self.load_modules() #Cargar modulos en el objeto bot

    # Validación de bot cargado
    async def event_ready(self):
        # Evento que se ejecuta cuando el bot se conecta correctamente.
        animated_message(f"Bot en linea...","\033[38;5;154m")

    # Registra comandos desde módulos separados.
    def load_modules(self):
        animated_message("Cargando modulos...","\033[38;5;207m")
        admin_commands(self)
        general_commands(self)
        stats_commands(self)
        dynamic_commands(self)
        xp_commands(self)

    #Lectura del evento de nuevo mensaje en el chat del canal
    async def event_message(self, message): #Evento de nuevo mensaje en el chat
        channel = self.get_channel(self.nick) #Obtener el canal del bot para poder enviar mensajes, es como el ctx
        if message.author is None:
            return  # Ignorar mensajes sin autor
        await read_save_chat(message)
        await interactuar(channel,message)
        await desafiar(channel,message)
        await self.handle_commands(message)
    
    #Evento de unión de un usuario al canal
    async def event_join(self, channel, user):
        await user_joined(user.name)

    #Timers para mensajes aleatorios
    async def send_timed_messages(self):
        """Envía mensajes aleatorios desde un archivo de texto en intervalos de tiempo."""
        await self.wait_until_ready()  # Espera a que el bot esté listo
        channel = self.get_channel(self.nick)
        sleep_time = random.randint(1200, 1800)
        while True:
            if channel:
                if is_channel_online(): # Verificar si el canal está en vivo
                    await channel.send(f'[DESAFIO RANDOM] 🔮 {gen_response("mensajes_twitch.txt")}')  # Enviar mensaje al chat
                    sleep_time = random.randint(1200, 1800)
            await asyncio.sleep(1200)  # Esperar 20 minutos antes del siguiente mensaje
    
     #Timers para mensajes aleatorios
    # async def get_stream_data(self):
    #     """Consulta cada minuto el numero de viewers, followers y """
    #     await self.wait_until_ready()  # Espera a que el bot esté listo
    #     channel = self.get_channel(self.nick)
        
    #     while True:
    #         if channel:
    #             if is_channel_online(): # Verificar si el canal está en vivo
    #                 save_current_data()
    #         await asyncio.sleep(1)  # Esperar

    

# Iniciar el bot
if __name__ == "__main__":
    bot = TwitchBot()
    bot.run()
