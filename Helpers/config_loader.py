import json
import os
from Helpers.printlog import printlog

def load_config():
    """
    Carga el token desde el archivo config.json
    """
    # Generar la ruta absoluta al archivo token.json
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))
    # Verificar si el archivo existe
    if not os.path.exists(config_path):
        printlog(f"Error: No se encontró el archivo en la ruta especificada: {config_path}","ERROR")
        exit()
    try:
        # Abrir y cargar el archivo JSON
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
            return config_data
    except json.JSONDecodeError as e:
        printlog(f"Error al decodificar el archivo JSON: {e}","ERROR")
        exit()
    except Exception as e:
        printlog(f"Error cargando config.json: {e}","ERROR")
        exit()