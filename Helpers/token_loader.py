import json
import os

from Helpers.printlog import printlog

def load_token():
    """
    Carga el token desde el archivo token.json ubicado en la carpeta Credentials.
    """
    # Generar la ruta absoluta al archivo token.json
    token_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Credentials', 'token.json'))
    # Verificar si el archivo existe
    if not os.path.exists(token_path):
        printlog(f"Error: No se encontró el archivo en la ruta especificada: {token_path}", "ERROR")
        exit()
    try:
        # Abrir y cargar el archivo JSON
        with open(token_path, 'r', encoding='utf-8') as file:
            token_data = json.load(file)
            return token_data
    except json.JSONDecodeError as e:
        printlog(f"Error al decodificar el archivo JSON: {e}", "ERROR")
        exit()
    except Exception as e:
        printlog(f"Error cargando token.json: {e}","ERROR")
        exit()


    