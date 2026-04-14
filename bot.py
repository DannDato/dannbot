# -*- coding: utf-8 -*-
"""
    DannBot - Bot de Twitch
"""
import os
import sys
import asyncio
import contextlib
import socket

try:
    import certifi

    # Ensure Python, requests and aiohttp use a valid CA bundle for Twitch HTTPS.
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except Exception:
    pass

import twitchio
import importlib
from twitchio import eventsub
from twitchio.ext import commands
from twitchio.ext.commands import CommandNotFound

                    # Importar configuraciones
from Helpers.token_loader import load_token, refresh_token_silent
from Helpers.console_log import init_console, clear_console, animated_message
from Helpers.printlog import printlog
from Helpers.helpers import safe_int
from Helpers.helpers_bot import user_joined, send_timed_messages, happy_birthday, poll_chatters

            #Importar handlers/Manejadores de eventos
from Handlers.handlers_message import handle_message
from Handlers.handlers_follow import handle_follow
from Handlers.handlers_cheer import handle_cheer
from Handlers.handlers_subs import handle_sub, handle_sub_gift
from Handlers.handlers_youtube import poll_youtube_uploads
from Handlers.console_handler import console_control
from Helpers.health_check import monitor_bot_health
from Helpers.helpers_admin import start_stream
from Helpers.discord_notifier import notify_critical_error
from Helpers.feature_flags import is_feature_enabled
from Seed.basic_commands import ensure_seed_basic_commands

from Helpers.colors import (
    azul, white, resetColor,
    channelColor, colorConvert,
    userColors, rosa, red, green
)

IS_TTY = sys.stdin.isatty() and sys.stdout.isatty()


def _systemd_notify(payload: str) -> bool:
    """Envía notificaciones al socket de systemd si está disponible."""
    notify_socket = os.getenv("NOTIFY_SOCKET")
    if not notify_socket:
        return False

    # Socket abstracto en Linux: systemd usa prefijo '@'
    if notify_socket.startswith("@"):
        notify_socket = "\0" + notify_socket[1:]

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(notify_socket)
            sock.sendall(payload.encode("utf-8"))
        return True
    except OSError as exc:
        printlog(f"[Systemd] No se pudo notificar a systemd: {exc}", "WARNING")
        return False


def _systemd_watchdog_interval_seconds(default_seconds: int = 30) -> int:
    """Calcula intervalo de ping basado en WATCHDOG_USEC (mitad del valor)."""
    watchdog_usec = os.getenv("WATCHDOG_USEC")
    if not watchdog_usec:
        return default_seconds

    try:
        usec = int(watchdog_usec)
        if usec <= 0:
            return default_seconds
        return max(1, usec // 2_000_000)
    except ValueError:
        return default_seconds


async def keep_systemd_watchdog(stop_check, interval_seconds=30):
    """Envía pulsos WATCHDOG=1 para que systemd supervise salud del proceso."""
    while not stop_check():
        _systemd_notify("WATCHDOG=1\nSTATUS=DannBot running")
        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break


async def keep_token_fresh(bot, channel_user, stop_check, interval_seconds=900):
    """
    Refresca token periodicamente de forma SILENCIOSA (sin OAuth interactivo).

    Se ejecuta cada `interval_seconds` segundos (default 15min).
    Intenta refresco silencioso; si falla, solo loguea advertencia.
    NO dispara OAuth interactivo en background.
    """
    attention_alert_sent = False

    while not stop_check():
        try:
            # Refresco silencioso: solo intenta renovar via Twitch, sin flujo interactivo
            status = await asyncio.to_thread(refresh_token_silent)
            if status.get("ok"):
                if attention_alert_sent:
                    printlog("[Auth] Token recuperado nuevamente tras fallo previo.", "INFO")
                attention_alert_sent = False
            else:
                code = status.get("code", "unknown")
                detail = status.get("detail", "Fallo desconocido durante refresco silencioso")
                printlog(f"[Auth] Refresco silencioso falló ({code}): {detail}", "WARNING")

                # Aviso visible para intervención manual cuando el token deja de ser usable.
                if not attention_alert_sent:
                    await channel_user.send_message(
                        sender=bot.user,
                        message=(
                            "[BOT] - ALERTA: el token OAuth expiró o quedó inválido y requiere atención manual. "
                            "Reautoriza/reinicia el bot para recuperar conexión estable."
                        )
                    )
                    attention_alert_sent = True
        except Exception as exc:
            printlog(f"[Auth] Error inesperado en refresco de token: {exc}", "ERROR")

        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break


if IS_TTY:
    init_console()
    animated_message(" Iniciando DannBot", resetColor)
else:
    printlog("Iniciando DannBot en modo servicio (sin TTY)", "INFO")

token_data = load_token(ensure_valid=True, allow_interactive=IS_TTY)
CLIENT_ID = token_data.get("client_id")
CLIENT_SECRET = token_data.get("client_secret")
BOT_ID = token_data.get("bot_id")
OWNER_ID = token_data.get("owner_id") or BOT_ID  # canal objetivo del bot
ACCESS_TOKEN = token_data.get("access_token")
CHANNEL_NAME = token_data.get("channel_name")

if IS_TTY:
    animated_message("Token cargado correctamente...", azul)
else:
    printlog("Token cargado correctamente", "INFO")

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

    # lanzar consola solo si existe terminal
    if sys.stdin.isatty():
        bot.console_task = asyncio.create_task(console_control(bot))

    # El adapter web local no es necesario para este flujo y puede chocar con puertos ya ocupados (ej. 4343).
    await bot.start(with_adapter=False)


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
        self.console_task = None
        self.happy_birthday_task = None
        self.timed_messages_task = None
        self.monitor_task = None
        self.chatters_poll_task = None
        self.token_refresh_task = None
        self.systemd_watchdog_task = None
        self.youtube_poll_task = None
        self._bot_closing = False
        self.command_modules_loaded = True
        self.command_module_issues = []
        self._systemd_notify_enabled = bool(os.getenv("NOTIFY_SOCKET"))
        if IS_TTY:
            animated_message("Credenciales aplicadas", rosa)

    async def _cancel_task(self, task: asyncio.Task | None) -> None:
        if not task or task.done() or task is asyncio.current_task():
            return

        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    async def close(self, **options) -> None:
        if self._bot_closing:
            return

        self._bot_closing = True
        self.connected = False

        if self._systemd_notify_enabled:
            _systemd_notify("STOPPING=1\nSTATUS=DannBot stopping")

        for task in (
            self.happy_birthday_task,
            self.timed_messages_task,
            self.monitor_task,
            self.console_task,
            self.chatters_poll_task,
            self.token_refresh_task,
            self.systemd_watchdog_task,
            self.youtube_poll_task,
        ):
            await self._cancel_task(task)

        await super().close(**options)

    async def restart_process(self, reason: str) -> None:
        printlog(reason, "WARNING")
        script = os.path.abspath(sys.argv[0])
        await self.close()
        os.execv(sys.executable, [sys.executable, script] + sys.argv[1:])


    #Setup inicial del bot, carga dinámica de archivos py para modulos de comandos
    async def setup_hook(self) -> None:
        if IS_TTY:
            animated_message("Cargando comandos...", white)
        inserted, total = ensure_seed_basic_commands()
        printlog(f"Comandos base en BD: {total} (nuevos insertados: {inserted})", "DEBUG")
        self.command_modules_loaded = True
        self.command_module_issues = []
        commands_dir = os.path.join(os.path.dirname(__file__), "Commands")
        command_files = [
            filename for filename in os.listdir(commands_dir)
            if filename.endswith(".py") and not filename.startswith("__")
        ]
        command_files.sort()

        for filename in command_files:
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"Commands.{filename[:-3]}"
                printlog(f"Cargando modulo: {module_name}", "DEBUG")
                try:
                    module = importlib.import_module(module_name)
                    loaded_component = False
                    # Buscar clases que hereden de commands.Component
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, commands.Component) and attr is not commands.Component:
                            await self.add_component(attr(self))
                            loaded_component = True
                            printlog(f"Lista de comandos cargados: {attr_name}")
                    if not loaded_component:
                        self.command_modules_loaded = False
                        self.command_module_issues.append(module_name)
                        printlog(f"No se encontro ningun commands.Component en {module_name}", "WARNING")
                except Exception as e:
                    self.command_modules_loaded = False
                    self.command_module_issues.append(module_name)
                    printlog(f"Error cargando {module_name}: {e}", "ERROR")

        if not self.command_modules_loaded:
            printlog("No se pudieron cargar todos los modulos, se necesita atencion", "ERROR")
            printlog(f"Modulos con problemas: {', '.join(self.command_module_issues)}", "WARNING")
            if IS_TTY:
                animated_message("Carga incompleta de modulos", red)
        await asyncio.sleep(1)
    #______________________________________________________________________

    # Evento que se dispara cuando el bot está listo
    async def event_ready(self) -> None:
        printlog(f"Bot en linea...")
        self.connected = True  # Bandera de estado para analizis de status
        if IS_TTY:
            clear_console()
        user = self.create_partialuser(BOT_ID)
        if is_feature_enabled("FEATURE_BIRTHDAYS", True) and (self.happy_birthday_task is None or self.happy_birthday_task.done()):
            self.happy_birthday_task = asyncio.create_task(happy_birthday(self, user))
        elif not is_feature_enabled("FEATURE_BIRTHDAYS", True):
            printlog("[Features] FEATURE_BIRTHDAYS deshabilitado: se omite tarea de cumpleaños.", "INFO")
        if self.timed_messages_task is None or self.timed_messages_task.done():
            self.timed_messages_task = asyncio.create_task(send_timed_messages(self, user))
        if self.monitor_task is None or self.monitor_task.done():
            self.monitor_task = asyncio.create_task(monitor_bot_health(self))
        if self.chatters_poll_task is None or self.chatters_poll_task.done():
            self.chatters_poll_task = asyncio.create_task(poll_chatters(self))
        if self.token_refresh_task is None or self.token_refresh_task.done():
            self.token_refresh_task = asyncio.create_task(keep_token_fresh(self, user, lambda: self._bot_closing))
        if is_feature_enabled("FEATURE_YOUTUBE", True) and (self.youtube_poll_task is None or self.youtube_poll_task.done()):
            self.youtube_poll_task = asyncio.create_task(poll_youtube_uploads(lambda: self._bot_closing))
        elif not is_feature_enabled("FEATURE_YOUTUBE", True):
            printlog("[Features] FEATURE_YOUTUBE deshabilitado: se omite monitor de YouTube.", "INFO")
        if self._systemd_notify_enabled and (self.systemd_watchdog_task is None or self.systemd_watchdog_task.done()):
            watchdog_interval = _systemd_watchdog_interval_seconds(default_seconds=30)
            self.systemd_watchdog_task = asyncio.create_task(
                keep_systemd_watchdog(lambda: self._bot_closing, interval_seconds=watchdog_interval)
            )

        if self._systemd_notify_enabled:
            _systemd_notify("READY=1\nSTATUS=DannBot conectado a Twitch")

        await user.send_message(sender=self.user, message=f"[BOT] - DannBot en linea 😎")
        if not self.command_modules_loaded:
            await user.send_message(sender=self.user, message="[BOT] - Se me olvidaron los comandooos! ayudame datooo")
        if IS_TTY:
            animated_message("DannBot en linea", green)

    # Listener para mensajes
    async def event_message(self, message: twitchio.ChatMessage) -> None:
        custom_command_handled = await handle_message(self, message)
        if custom_command_handled:
            return
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

    async def event_stream_online(self, payload: twitchio.StreamOnline) -> None:
        printlog(f"Evento stream_online recibido para broadcaster {payload.broadcaster.id}")

        stream_started = await start_stream()
        if stream_started:
            printlog("Stream iniciado automaticamente desde EventSub stream_online.")
        else:
            printlog("Ya existia un stream activo en BD. Se ignora stream_online para evitar duplicados.", "WARNING")


    #______________________________________________________________________
    #Eventos de error
    async def event_command_error(self, payload: twitchio.ext.commands.CommandErrorPayload) -> None:
        error = getattr(payload, "error", None)
        exception = getattr(payload, "exception", None)
        detail = error or exception

        # Evita ruido por comandos desconocidos escritos en chat.
        if isinstance(detail, CommandNotFound):
            return

        context = getattr(payload, "context", None)
        command_name = "unknown"
        chatter_name = "unknown"
        message_text = ""

        if context is not None:
            command_obj = getattr(context, "command", None)
            command_name = getattr(command_obj, "name", "unknown") if command_obj else "unknown"
            chatter = getattr(context, "chatter", None)
            chatter_name = getattr(chatter, "name", "unknown") if chatter else "unknown"
            message = getattr(context, "message", None)
            message_text = getattr(message, "text", "") if message else ""

        detail_text = str(detail) if detail else "Error de comando sin detalle"
        printlog(
            f"Error en comando '{command_name}' de @{chatter_name}: {detail_text} | mensaje: {message_text}",
            "ERROR",
        )
        await notify_critical_error(
            "event_command_error",
            f"command={command_name} user={chatter_name} detail={detail_text} msg={message_text}",
        )

    async def event_error(self, payload: twitchio.EventErrorPayload) -> None:
        printlog(f"Se ha capturado un error de evento {safe_int(payload.error)}", "ERROR")
        await notify_critical_error("event_error", str(payload.error))


    # Evento de desconexión
    async def event_disconnect(self):
        self.connected = False  # Bandera de estado
        printlog(f"Desconectando bot...", "WARNING")
        if IS_TTY:
            animated_message("Bot desconectado", red)


#______________________________________________________________________

if __name__ == "__main__":
    asyncio.run(main())
