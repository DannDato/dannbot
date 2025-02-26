#Librerias de control de consola y conexión a twitch
from twitchio.ext import commands, pubsub
import logging

# Importar módulos (Comandos)
from Commands.admin import admin_commands
from Commands.stats import stats_commands
from Commands.general import general_commands
from Commands.dynamic import dynamic_commands
from Commands.xp import xp_commands

#Importar todos los listeners de eventos mediante pubsub y eventsub
from Extensions.listeners import listen_to_pubsub

# Importar Helpers basicos del bot
from Helpers.helpers import get_broadcaster_id
from Helpers.helpers_dynamic import interactuar, desafiar
from Helpers.helpers_bot import read_save_chat, user_joined, send_timed_messages

#Importar handlers de eventos
from Handlers.handlers_bits import handle_bits
from Handlers.handlers_redeems import handle_redeem
from Handlers.handlers_subs import handle_sub, handle_sub_gift

#Importar configuraciónes
from Helpers.token_loader import load_token
from Helpers.console_log import init_console, animated_message
from logging.handlers import TimedRotatingFileHandler


init_console() #Inicializar configuración de la consola (logging y colorlog)

# Cargar credenciales desde el archivo token.json
token_data = load_token()
access_token = token_data.get("access_token")
client_id = token_data.get("client_id")
initial_channels = token_data.get("initial_channels", [])
channel_name = token_data.get("channel_name")

broadcaster_id = get_broadcaster_id()

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

        #Inicializando pubSub_________________________________________________
        """Estas lineas inicializan la lectura de pubSub para el manejo de eventos
            captura eventos de:
            -Puntos de canal
            -Bits
            -Subscripciones
            -Subscripcones de regalo
        """
        animated_message("Cargando pubsub... ","\033[38;5;204m")
        self.pubsub = pubsub.PubSubPool(self)
        self.loop.create_task(listen_to_pubsub(self, access_token, broadcaster_id))
        #______________________________________________________________pubSub

    # Registra comandos desde módulos separados.
    def load_modules(self):
        #Pinta mensaje
        animated_message("Conectando modulos...","\033[38;5;207m")
        #______________________________
        admin_commands(self)
        general_commands(self)
        stats_commands(self)
        dynamic_commands(self)
        xp_commands(self)

    #___________________________________________________________________
    """
        Declarando los diferentes eventos de pubsub 
        para ejecutar diferentes handlers
    """
    animated_message("Preparando eventos... ","\033[38;5;152m")


    #evento para manejar el uso de recompensas de canal
    async def event_pubsub_channel_points(self, event):
        await handle_redeem(event.reward.title, event.user.name)

    # Evento para manejar el uso de Bits
    async def event_pubsub_bits(self, event):
        await handle_bits(event.bits_used, event.user.name, event.message.content)


    async def event_pubsub_channel_subscriptions(self, event):
        await handle_sub(event, self)

    async def event_pubsub_channel_subscription_gift(self, event):
        await handle_sub_gift(event, self)

    #Evento de unión de un usuario al canal
    async def event_join(self, channel, user):
        await user_joined(user.name)
    
    #Lectura del evento de nuevo mensaje en el chat del canal
    async def event_message(self, message): #Evento de nuevo mensaje en el chat
        channel = self.get_channel(self.nick) #Obtener el canal del bot para poder enviar mensajes, es como el ctx
        if message.author is None:
            return  # Ignorar mensajes sin autor
        await read_save_chat(message)
        await interactuar(channel,message)
        await desafiar(channel,message)
        message.content=message.content.lower()
        await self.handle_commands(message)

    async def event_command_error(self, ctx, error):
        """Maneja errores de comandos no encontrados"""
        if isinstance(error, commands.CommandNotFound):
            logging.warning(f'❌ Comando desconocido. ')

    # Validación de bot cargado
    async def event_ready(self):
        # Evento que se ejecuta cuando el bot se conecta correctamente.
        animated_message(f"{self.nick} en linea...","\033[38;5;154m")
        #await send_timed_messages(self)
        

# Iniciar el bot
if __name__ == "__main__":
    bot = TwitchBot()
    bot.run()
    
