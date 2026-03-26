import asyncio
from datetime import datetime
from Helpers.console_log import animated_message
from Helpers.colors import white, red

async def monitor_bot_health(bot):
    """
    Revisa el estado del bot cada 5 minutos.
    - Si el bot no responde, reinicia el proceso.
    - Si son las 5:00 AM exactas, también reinicia el proceso.
    """
    while True:
        await asyncio.sleep(300)  # Espera 5 minutos

        # Reinicio forzado a las 5:00 AM
        now = datetime.now()
        if now.hour == 5 and now.minute == 0:
            animated_message("Cerrando bot...",red)
            animated_message("Reiniciando bot...",white)
            await asyncio.sleep(1)
            await bot.restart_process("[Monitor] - Reinicio programado a las 5:00 AM")

        # Chequeo de salud del bot
        try:
            if not bot.connected:
                await bot.restart_process("[Monitor] - WebSocket desconectado. Reiniciando bot...")
            
        except Exception as e:
            await bot.restart_process(f"[Monitor] - Error en chequeo de salud: {e}. Reiniciando...")