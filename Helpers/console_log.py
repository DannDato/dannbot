import os
import logging
from logging.handlers import TimedRotatingFileHandler
import colorlog
import shutil
import time
import sys

from Helpers.config_loader import load_config

config_data =load_config()
name=config_data.get("name")
version=config_data.get("version")
copyright=config_data.get("copyright")

init_message = 0

def init_console():
    # Configuración de logging con colores en la consola
    log_filename = "Logs/bot_log.log"  # Se agrega .log manualmente

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

    # Configuración del archivo de log con rotación diaria
    log_handler = TimedRotatingFileHandler(
        log_filename, when="midnight", encoding="utf-8", utc=True, backupCount=7
    )

    # Ajustar manualmente el formato de los archivos rotados
    log_handler.suffix = "%Y-%m-%d"
    log_handler.extMatch = r"^\d{4}-\d{2}-\d{2}$"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
        handlers=[log_handler]
    )

    # Configurar el handler para consola con colores
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # Añadir el handler de consola a los handlers del logger
    logging.getLogger().addHandler(console_handler)

    if os.name == 'nt':  # Para Windows
        os.system('cls')
    else:  # Para Linux y MacOS
        os.system('clear')

    # check_colors()
    title = f"""
    \033[1;34m           ____                    ____        __ 
       / __ \____ _____  ____  / __ )____  / /_
      / / / / __ `/ __ \/ __ \/ /_/ / __ \/ __/
     / /_/ / /_/ / / / / / / / /_/ / /_/ / /_  
    /_____/\__,_/_/ /_/_/ /_/_____/\____/\__/  
    \033[38;5;255m         {copyright}
    \033[38;5;255m          ──────────────────────────────────────────
"""
    print(centrar_texto(title))
    # Mostrar el título centrado

def animated_message(text,color):
    total_length = 43
    text_length = len(text)
    version_length = len(f"Versión {version}")

    # Calcular el número de espacios entre el texto y la versión
    spaces_between = total_length - text_length - version_length

    # Crear el mensaje con los espacios calculados
    # mensaje_original = f"\033[38;5;154m{text}{' ' * spaces_between}\033[38;5;237mVersión {version}"
    mensaje_original = f"{color}{text}{' ' * spaces_between}\033[38;5;237mVersión {version}"

    # Eliminar tabuladores y espacios innecesarios
    mensaje_sin_espacios = mensaje_original.strip()

    # Calcular el centro
    ancho_terminal = shutil.get_terminal_size().columns
    mensaje_length = len(mensaje_sin_espacios)
    centro_x = ((ancho_terminal - mensaje_length) // 2)+14

    # Función para mover el cursor a la posición deseada
    def gotoxy(x, y):
        print(f"\033[{y};{x}H", end="")

    # Guardar la posición actual del cursor
    print("\033[s", end="")  # Guarda la posición actual del cursor

    # Calcular el espacio en el centro de la terminal
    # Mover al inicio de la línea y luego al centro
    gotoxy(centro_x, 9)

    # Imprimir letra por letra con 20ms de espera
    for letra in mensaje_sin_espacios:
        print(letra, end="", flush=True)  # No salto de línea y limpia el buffer
        time.sleep(0.005)  # Espera 20 ms entre cada letra

    # Restaurar la posición original del cursor
    print("\033[u", end="")  # Restaura la posición del cursor

    print()  # Salto de línea al final para evitar desorden en la terminal

def centrar_texto(texto):
    # Obtener el ancho de la terminal
    ancho_terminal = shutil.get_terminal_size().columns
    
    # Dividir el texto en líneas individuales
    lineas = texto.split("\n")
    
    # Calcular el espacio necesario para centrar cada línea
    texto_centrado = "\n".join(linea.center(ancho_terminal) for linea in lineas)
    
    return texto_centrado
    

def check_colors():
    for i in range(256):
        print(f"\033[38;5;{i}mColor {i}")
    return

