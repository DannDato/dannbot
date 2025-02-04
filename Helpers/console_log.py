import os
import logging
from logging.handlers import TimedRotatingFileHandler
import colorlog

def init_console():
    # Configuración de logging con colores en la consola
    log_filename = "Logs/twitch_bot.log"

    # Crear un formateador de colores para la consola
    console_formatter = colorlog.ColoredFormatter(
        "\033[90m %(asctime)s -\033[0m %(log_color)s%(levelname)s%(reset)s - %(filename)s - \033[90m%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }
    )

    # Configuración de logging sin duplicación en consola
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
        handlers=[
            TimedRotatingFileHandler(log_filename, when="midnight", backupCount=7),  # Cambia diariamente y conserva 7 días de logs
        ]
    )

    # Configurar el handler para consola con colores (lo añadimos explícitamente)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # Añadir el handler de consola a los handlers del logger
    logging.getLogger().addHandler(console_handler)

    if os.name == 'nt':  # Para Windows
        os.system('cls')
    else:  # Para Linux y MacOS
        os.system('clear')
    # Titulo con colores en consola
    title = """
    \033[1;36m _____                        _       _          ____   ____ _______ 
    |  __ \                      | |     | |        |  _ \ / __ \__   __|
    | |  | | __ _ _ __  _ __   __| | __ _| |_ ___   | |_) | |  | | | |   
    | |  | |/ _` | '_ \| '_ \ / _` |/ _` | __/ _ \  |  _ <| |  | | | |   
    | |__| | (_| | | | | | | | (_| | (_| | || (_) | | |_) | |__| | | |   
    |_____/ \__,_|_| |_|_| |_|\__,_|\__,_|\__\___/  |____/ \____/  |_|   
                                                                      
                                                                      
                                                                          
    \033[1;32m                          BOT
    \033[1;33m                    Inicializando...
    """
    # Imprimir el título
    print(title)
    print("\n")

