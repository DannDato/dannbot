
import os
import time
import re


def printlog(message, level="INFO"):
    """
    """
    levels = {
        "INFO": "\033[38;5;47m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "DEBUG": "\033[94m"   # Blue
    }
    
    gray = "\033[90m"
    reset = "\033[0m"
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    date=time.strftime("%Y-%m-%d", time.localtime())


    logs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Logs', f'{date}.log'))
    if not os.path.exists(os.path.dirname(logs_path)):
        os.makedirs(os.path.dirname(logs_path))
    
    if level in levels:
        print(f"{gray}{datetime} {levels[level]} [{level}] {reset}- {message}{reset}")
    else:
        print(f"[UNKNOWN] {message}")


    message = quitar_colores(clean_text(message))
    with open(logs_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"{datetime} - [{level}] - {message}\n")


def quitar_colores(texto_con_color: str) -> str:
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', texto_con_color)

import re
import unicodedata
def clean_text(text):
    if not isinstance(text, str):
        return str(text)
    # Normalizar texto para quitar acentos y caracteres raros
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    # Eliminar emojis y símbolos no alfabéticos
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # Emoticons
        u"\U0001F300-\U0001F5FF"  # Símbolos y pictogramas
        u"\U0001F680-\U0001F6FF"  # Transporte y mapas
        u"\U0001F700-\U0001F77F"  # Alquimia
        u"\U0001F780-\U0001F7FF"  # Geometría
        u"\U0001F800-\U0001F8FF"  # Flechas
        u"\U0001F900-\U0001F9FF"  # Caras y gestos
        u"\U0001FA00-\U0001FA6F"  # Objetos y animales
        u"\U0001FA70-\U0001FAFF"  # Símbolos adicionales
        u"\U00002702-\U000027B0"  # Varias cosas
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub("", text)

    # Reemplazar saltos de línea, tabulaciones y otras marcas invisibles por espacios
    text = re.sub(r"[\n\r\t\f\v]+", " ", text)
    
    # Colapsar múltiples espacios a uno solo
    text = re.sub(r"\s+", " ", text)

    # Eliminar espacios al inicio y al final
    return text.strip()