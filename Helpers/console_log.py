import os
import shutil
import time

from Helpers.config_loader import load_config

config_data =load_config()
name=config_data.get("name")
version=config_data.get("version")
copyright=config_data.get("copyright")

title = f"""
    \033[38;5;255m       {copyright} \n
    \033[\033[38;5;255m         ██████╗  █████╗ ███╗   ██╗███╗   ██╗██████╗  ██████╗ ████████╗
██╔══██╗██╔══██╗████╗  ██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
██║  ██║███████║██╔██╗ ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
██║  ██║██╔══██║██║╚██╗██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
██████╔╝██║  ██║██║ ╚████║██║ ╚████║██████╔╝╚██████╔╝   ██║   
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
    \033[38;5;255m        ──────────────────────────────────────────────────────────────
                                                                
    """
# title=f"""\033[\033[38;5;63m
# ████████▄     ▄████████ ███▄▄▄▄   ███▄▄▄▄   ▀█████████▄   ▄██████▄      ███     
# ███   ▀███   ███    ███ ███▀▀▀██▄ ███▀▀▀██▄   ███    ███ ███    ███ ▀█████████▄ 
# ███    ███   ███    ███ ███   ███ ███   ███   ███    ███ ███    ███    ▀███▀▀██ 
# ███    ███   ███    ███ ███   ███ ███   ███  ▄███▄▄▄██▀  ███    ███     ███   ▀ 
# ███    ███ ▀███████████ ███   ███ ███   ███ ▀▀███▀▀▀██▄  ███    ███     ███     
# ███    ███   ███    ███ ███   ███ ███   ███   ███    ██▄ ███    ███     ███     
# ███   ▄███   ███    ███ ███   ███ ███   ███   ███    ███ ███    ███     ███     
# ████████▀    ███    █▀   ▀█   █▀   ▀█   █▀  ▄█████████▀   ▀██████▀     ▄████▀
# \033[38;5;255m         ──────────────────────────────────────────────────────────────────────────────
# \033[38;5;245m             {copyright}   
# \033[38;5;255m                                                                                
# """
def init_console():
    if os.name == 'nt':  # Para Windows
        os.system('cls')
    else:  # Para Linux y MacOS
        os.system('clear')
    # check_colors()
    print(centrar_texto(title))
    # Mostrar el título centrado

def clear_console():
    if os.name == 'nt':  # Para Windows
        os.system('cls')
    else:  # Para Linux y MacOS
        os.system('clear')
    print(centrar_texto(title))

def animated_message(text,color):
    total_length = 62
    text_length = len(text)
    version_length = len(f"Versión {version}")

    # Calcular el número de espacios entre el texto y la versión
    spaces_between = total_length - text_length - version_length

    # Crear el mensaje con los espacios calculados
    # mensaje_original = f"\033[38;5;154m{text}{' ' * spaces_between}\033[38;5;237mVersión {version}"
    mensaje_original = f"{color}{text}{' ' * spaces_between}\033[38;5;240mVersión {version}"

    # Eliminar tabuladores y espacios innecesarios
    mensaje_sin_espacios = mensaje_original.strip()

    # Calcular el centro
    ancho_terminal = shutil.get_terminal_size().columns
    mensaje_length = len(mensaje_sin_espacios)
    centro_x = ((ancho_terminal - mensaje_length) // 2)+12

    # Función para mover el cursor a la posición deseada
    def gotoxy(x, y):
        print(f"\033[{y};{x}H", end="")

    # Guardar la posición actual del cursor
    print("\033[s", end="")  # Guarda la posición actual del cursor

    # Calcular el espacio en el centro de la terminal
    # Mover al inicio de la línea y luego al centro
    gotoxy(centro_x, 11)

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

