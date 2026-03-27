import logging
import asyncio
import datetime
import sys

from Helpers.console_log import clear_console, animated_message
from Helpers.colors import resetColor, white, red, green, dorado
from Helpers.printlog import printlog

# Variables globales para monitoreo
BOT_START_TIME = datetime.datetime.now()

async def console_control(bot):
    if not sys.stdin.isatty():
        return
    while True:
        list_commands =[
            "commands",
            "exit",
            "restart",
            "status",
            "clear",
            "stats",
            "uptime"
        ]
        
        command = await asyncio.to_thread(input, ">> ")
        command = command.strip()
        if command.lower() == "commands" or command.lower()=="comandos" :
            printlog(f" Comandos de consola:{white} {list_commands}")
            
        if command == "uptime":
            now = datetime.datetime.now()
            delta = now - BOT_START_TIME
            hours, remainder = divmod(delta.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            printlog(f"[Console] - Bot activo desde: {int(hours)}h {int(minutes)}m {int(seconds)}s", "INFO")
        
        elif command == "stats":
            printlog(f"[Console] - Mensajes procesados: {bot.messages_processed}", "INFO")
            printlog(f"[Console] - Comandos ejecutados: {bot.commands_executed}", "INFO")

        #_____________________________________________________________________________________
        elif command.lower() == "exit" or command.lower() == "stop" or command.lower() == "quit" or command.lower() == "close" :
            clear_console()
            animated_message("Cerrando bot",dorado)
            await bot.close()
            animated_message("Bot cerrado...",red)
            break

        #_______________________________________________________________________________________
        elif command.lower() == "restart" or command.lower()=="reiniciar":
            animated_message("Cerrando bot",red)
            animated_message("Reiniciando bot...",white)
            await asyncio.sleep(1)
            await bot.restart_process("[Console] - Reiniciando bot por comando de consola...")

        #______________________________________________________________________________________
        elif command.lower() == "status":
            animated_message("Chequeando estado del bot...",white)
            await asyncio.sleep(1)
            try:
                if not bot.connected:
                    animated_message("Reiniciando bot...",white)
                    await asyncio.sleep(1)
                    await bot.restart_process("[Console] - WebSocket desconectado. Reiniciando bot...")
                else:
                    animated_message("DannDato en linea","\033[38;5;51m")
                    await asyncio.sleep(3)
            except Exception as e:
                animated_message("Algo ha ocurrido, reiniciando bot...",green)
                printlog(f"[Monitor] - Error en chequeo de salud: {e}. Reiniciando...","ERROR")
                await asyncio.sleep(1)
                await bot.restart_process(f"[Console] - Error en chequeo de salud: {e}. Reiniciando...")

        #______________________________________________________________________________________
        elif command.lower() == "clear" or command.lower()=="cls" :
            clear_console()
            animated_message("DannDato en linea","\033[38;5;51m")
        

        #_______________________________________________________________________________________
        else:
            printlog("<<Console>> - Comando no reconocido.","WARNING")
        