import asyncio

from Helpers.helpers import is_channel_online
from Helpers.helpers_admin import start_stream, end_stream
from Helpers.printlog import printlog


STREAM_OFFLINE_GRACE_SECONDS = 3600


async def _finalize_stream_after_grace(bot, broadcaster_id: str) -> None:
    try:
        await asyncio.sleep(STREAM_OFFLINE_GRACE_SECONDS)

        channel_online = await is_channel_online()
        if channel_online:
            printlog(
                "Se omitio auto-cierre: el canal volvio a estar en vivo dentro de la validacion final.",
                "DEBUG",
            )
            return

        stream_ended = await end_stream()
        if stream_ended:
            printlog(
                f"Auto-cierre ejecutado tras 1h offline para broadcaster {broadcaster_id}.",
                "WARNING",
            )
        else:
            printlog("Auto-cierre omitido: no habia stream activo para finalizar.", "DEBUG")

    except asyncio.CancelledError:
        printlog("Auto-cierre cancelado por regreso del stream.", "DEBUG")
        raise
    except Exception as exc:
        printlog(f"Error en auto-cierre de stream offline: {exc}", "ERROR")
    finally:
        bot.stream_offline_finalize_task = None


async def handle_stream_online(bot, payload) -> None:
    printlog(f"Evento stream_online recibido para broadcaster {payload.broadcaster.id}")

    if bot.stream_offline_finalize_task and not bot.stream_offline_finalize_task.done():
        await bot._cancel_task(bot.stream_offline_finalize_task)
        bot.stream_offline_finalize_task = None
        printlog("Se cancela auto-cierre: el stream volvio antes del tiempo de gracia.", "DEBUG")

    stream_started = await start_stream()
    if stream_started:
        printlog("Stream iniciado automaticamente desde EventSub stream_online.")
    else:
        printlog("Ya existia un stream activo en BD. Se ignora stream_online para evitar duplicados.", "WARNING")


async def handle_stream_offline(bot, payload) -> None:
    printlog(f"Evento stream_offline recibido para broadcaster {payload.broadcaster.id}")

    if bot.stream_offline_finalize_task and not bot.stream_offline_finalize_task.done():
        await bot._cancel_task(bot.stream_offline_finalize_task)

    bot.stream_offline_finalize_task = asyncio.create_task(
        _finalize_stream_after_grace(bot, str(payload.broadcaster.id))
    )
    printlog(
        "Se programo auto-cierre de stream en 1 hora si no vuelve a entrar stream_online.",
        "DEBUG",
    )
