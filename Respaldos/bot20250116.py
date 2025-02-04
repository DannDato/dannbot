# bot.py
import logging
from logging.handlers import TimedRotatingFileHandler
from twitchio.ext import commands

# Importar módulos desde los archivos
from Commands.admin import admin_commands
from Commands.stats import stats_commands
from Commands.general import general_commands
from Commands.dynamic import dynamic_commands
from Commands.xp import xp_commands

# from events.chat_listener import chat_event
from Helpers.helpers_bot import read_save_chat, user_joined
from Helpers.token_loader import load_token

# Configuración de logging
log_filename = "twitch_bot.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s -  %(filename)s - %(message)s",
    handlers=[
        TimedRotatingFileHandler(log_filename, when="midnight", backupCount=7),  # Cambia diariamente y conserva 7 días de logs
        logging.StreamHandler()  # Opcional: Mantener mensajes en consola también
    ]
)

# Cargar credenciales desde el archivo token.json
logging.info("\n\nCargando token...\n")
token_data = load_token()
access_token = token_data.get("access_token")
client_id = token_data.get("client_id")
initial_channels = token_data.get("initial_channels", [])
broadcaster_id = token_data.get("broadcaster_id")

# Verificar credenciales esenciales
if not access_token or not client_id or not broadcaster_id:
    logging.error("Error: Faltan credenciales esenciales en token.json.")
    exit()

# Clase principal del bot
class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=access_token,
            prefix="!",
            nick="diosito",  # Nombre de usuario del bot
            initial_channels=initial_channels if isinstance(initial_channels, list) else [initial_channels],
        )
        logging.info("-> Iniciando módulos Twitch")
        self.load_modules()

    def load_modules(self):
        # Registra comandos desde módulos separados.
        admin_commands(self)
        general_commands(self)
        stats_commands(self)
        dynamic_commands(self)
        xp_commands(self)

    async def event_message(self, message):
        read_save_chat(message)
        if message.author is None:
            return  # Ignorar mensajes sin autor
        await self.handle_commands(message)

    async def event_join(self, channel, user):
        # Llamamos a la función user_joined para registrar al usuario
        await user_joined(user.name)

    # Validación de bot cargado
    async def event_ready(self):
        # Evento que se ejecuta cuando el bot se conecta correctamente.
        logging.info(f"Bot conectado como {self.nick}")
        logging.info(f"En el canal: {self.user_id}")


# Iniciar el bot
if __name__ == "__main__":
    bot = TwitchBot()
    bot.run()
