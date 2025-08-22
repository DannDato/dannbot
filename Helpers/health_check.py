import asyncio
import os
import sys
import time
from datetime import datetime
from Helpers.printlog import printlog
from Helpers.console_log import clear_console, animated_message
from Helpers.colors import resetColor, white, red, green, dorado

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
            animated_message("Cerrando bot...",red)
            await bot.close()
            animated_message("Bot cerrado...",red)
            time.sleep(1)
            animated_message("Reiniciando bot...",white)
            time.sleep(1)
            # Reemplaza el proceso actual con uno nuevo (reinicio real)
            script = os.path.abspath(sys.argv[0])
            os.execv(sys.executable, [sys.executable, script] + sys.argv[1:])

        # Chequeo de salud del bot
        try:
            if not bot.connected:
                printlog("[Monitor] - WebSocket desconectado. Reiniciando bot...")
                await bot.close()
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                printlog("Chequeo de salud correcto, sin acciones realizadas")

        except Exception as e:
            printlog(f"[Monitor] - Error en chequeo de salud: {e}. Reiniciando...")
            await bot.close()
            os.execv(sys.executable, [sys.executable] + sys.argv)