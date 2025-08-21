import asyncio
import os
import sys
from datetime import datetime
from Helpers.printlog import printlog

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
            printlog("[Monitor] - Reinicio programado a las 5:00 AM")
            await bot.shutdown()
            os.execv(sys.executable, [sys.executable] + sys.argv)

        # Chequeo de salud del bot
        try:
            if bot._ws is None or not bot._ws._connection.open:
                printlog("[Monitor] - WebSocket desconectado. Reiniciando bot...")
                await bot.shutdown()
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            printlog(f"[Monitor] - Error en chequeo de salud: {e}. Reiniciando...")
            await bot.shutdown()
            os.execv(sys.executable, [sys.executable] + sys.argv)