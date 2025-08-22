# -*- coding: utf-8 -*-
"""
    DannBot - Bot de Twitch
"""
import os
import asyncio
import twitchio
import importlib
from twitchio import eventsub
from twitchio.ext import commands

                    # Importar configuraciones
from Helpers.token_loader import load_token
from Helpers.console_log import init_console, clear_console, animated_message
from Helpers.printlog import printlog
from Helpers.helpers_bot import user_joined, send_timed_messages, happy_birthday

            #Importar handlers/Manejadores de eventos
from Handlers.handlers_message import handle_message
from Handlers.handlers_follow import handle_follow
from Handlers.handlers_cheer import handle_cheer
from Handlers.handlers_subs import handle_sub, handle_sub_gift
from Handlers.console_handler import console_control
from Helpers.health_check import monitor_bot_health

from Helpers.colors import (
    azul, white, resetColor, 
    channelColor, colorConvert, 
    userColors, rosa, red, green
)
init_console()
animated_message(" Iniciando DannBot", resetColor)

token_data = load_token()
CLIENT_ID = token_data.get("client_id")
CLIENT_SECRET = token_data.get("client_secret")
BOT_ID = token_data.get("bot_id")
OWNER_ID = token_data.get("bot_id")  # canal objetivo del bot
ACCESS_TOKEN = token_data.get("access_token")
BOT_NAME = token_data.get("bot_name")
CHANNEL_NAME = token_data.get("channel_name")
INITIAL_CHANNELS = token_data.get("initial_channels", [])

animated_message("Token cargado correctamente...", azul)

async def main():
    subs = [
        eventsub.ChatMessageSubscription(broadcaster_user_id=OWNER_ID, user_id=BOT_ID),
        eventsub.ChannelCheerSubscription(broadcaster_user_id=OWNER_ID, user_id=BOT_ID),
        eventsub.ChannelSubscribeSubscription(broadcaster_user_id=OWNER_ID, user_id=BOT_ID),
        eventsub.ChannelFollowSubscription(broadcaster_user_id=OWNER_ID, moderator_user_id=OWNER_ID),
        eventsub.ChannelSubscriptionGiftSubscription(broadcaster_user_id=OWNER_ID),
        eventsub.ChannelBanSubscription(broadcaster_user_id=OWNER_ID),
        eventsub.ChannelUnbanSubscription(broadcaster_user_id=OWNER_ID),
        eventsub.ChannelUpdateSubscription(broadcaster_user_id=OWNER_ID),
        eventsub.StreamOnlineSubscription(broadcaster_user_id=OWNER_ID),
        eventsub.StreamOfflineSubscription(broadcaster_user_id=OWNER_ID),
    ]
    bot = Bot(subs=subs)
    bot_task = asyncio.create_task(bot.start())
    console_task = asyncio.create_task(console_control(bot))
    await asyncio.wait([bot_task, console_task], return_when=asyncio.FIRST_COMPLETED)


class Bot(commands.AutoBot):
    def __init__(self, *, subs: list[eventsub.SubscriptionPayload]) -> None:
        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="!",
            subscriptions=subs,
            ignore_self=False,   # <<-- Muy importante, procesa mensajes propios
            force_subscribe=True
        )
        self.connected = False  # Bandera de estado
        self.messages_processed = 0
        self.commands_executed = 0
        animated_message("Credenciales aplicadas", rosa)


    #Setup inicial del bot, carga dinámica de archivos py para modulos de comandos
    async def setup_hook(self) -> None:
        animated_message("Cargando comandos...", white)
        commands_dir = "Commands"
        for filename in os.listdir(commands_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"{commands_dir}.{filename[:-3]}"
                module = importlib.import_module(module_name)
                # Buscar clases que hereden de commands.Component
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, commands.Component) and attr is not commands.Component:
                        await self.add_component(attr(self))
                        printlog(f"Lista de comandos cargados: {attr_name}")
        await asyncio.sleep(1) 
    #______________________________________________________________________

    # Evento que se dispara cuando el bot está listo
    async def event_ready(self) -> None:
        printlog(f"Bot en linea...")
        self.connected = True  # Bandera de estado para analizis de status
        clear_console()
        user = self.create_partialuser(BOT_ID)
        self.happy_birthday_task = asyncio.create_task(happy_birthday(self, user))
        self.timed_messages_task = asyncio.create_task(send_timed_messages(self, user))
        self.monitor_task = asyncio.create_task(monitor_bot_health(self))
        await user.send_message(sender=self.user, message=f"[BOT] - DannBot en linea 😎")
        animated_message("DannBot en linea", green)

    # Listener para mensajes
    async def event_message(self, message: twitchio.ChatMessage) -> None:
        await handle_message(self, message)
        # Procesar los comandos recibidos dentro del mensaje despues del hanlder personalizado
        message.text=message.text.lower() #Bajamos a minusculas por si el comando está capitalizado
        await self.process_commands(message)

    # Listener para seguidores
    async def event_follow(self, payload: twitchio.ChannelFollow) -> None:
        await handle_follow(self, payload)
        
    #listener para donaciones de bits
    async def event_cheer(self, payload: twitchio.ChannelCheer) -> None:
        await handle_cheer(self, payload)

    # Listener para suscripciones
    async def event_subscription(self, payload: twitchio.ChannelSubscribe) -> None:
        await handle_sub(self, payload)

    #Listener para regalos de suscripciones
    async def event_subscription_gift(self, payload: twitchio.ChannelSubscribe) -> None:
        await handle_sub_gift(self, payload)

    #Listener para saber cuando se banea a alguien
    async def event_ban(self, payload: twitchio.ChannelBan) -> None:
        printlog(f"Se ha Baneado a {payload.user.name} del canal por {payload.reason}")
        #Aqui agregaremos un handler para llevar registro de los baneos
    
    #Listener para saber cuando se banea a alguien
    async def event_unban(self, payload: twitchio.ChannelUnban) -> None:
        printlog(f"Se quitado el baneo a {payload.user.name} del canal")
        #Aqui agregaremos un handler para llevar registro de los baneos

    #Listener de cambios en titulo, categoria, propiedades, etiquetas o cualquier info del stream
    async def event_channel_update(self, payload: twitchio.ChannelUpdate) -> None:
        printlog(f"Se ha actualizado la información del canal {payload.title} | {payload.category_name}")

    # async def event_stream_online(self, payload: twitchio.StreamOnline) -> None:
    #     printlog("Se ha inicializado un stream!")
    #     #Aqui agregaremos el handler para iniciar directo
    
    # async def event_stream_offline(self, payload: twitchio.StreamOffline) -> None:
    #     printlog("Se ha detenido el stream!")
    #     #Aqui agregaremos el handler para detener directo
        
    #______________________________________________________________________
    #Eventos de error
    async def event_command_error(self, payload: twitchio.ext.commands.CommandErrorPayload) -> None:
        printlog(f"Se ha presentado un error de comando o comando desconocido {payload}", "WARNING")
    
    async def event_error(self, payload: twitchio.EventErrorPayload) -> None:
        printlog(f"Se ha capturado un error de evento {payload}", "ERROR")


    # Evento de desconexión
    async def event_disconnect(self):
        self.connected = False  # Bandera de estado
        printlog(f"Desconectando bot...", "WARNING")
        animated_message("Bot desconectado", red)


#______________________________________________________________________

if __name__ == "__main__":
    asyncio.run(main())
