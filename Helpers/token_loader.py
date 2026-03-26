import json
import os

from Helpers.printlog import printlog
from Helpers.oauth_flow import ensure_token_data, get_token_path

def load_token():
    """
    Carga el token desde el archivo token.json ubicado en la carpeta Credentials.
    """
    token_path = get_token_path()
    try:
        if os.path.exists(token_path):
            with open(token_path, 'r', encoding='utf-8') as file:
                token_data = json.load(file)
            if token_data.get('access_token') and token_data.get('client_id') and token_data.get('client_secret'):
                return ensure_token_data()

        return ensure_token_data()
    except json.JSONDecodeError as e:
        printlog(f"Error al decodificar el archivo JSON: {e}", "ERROR")
        exit()
    except Exception as e:
        printlog(f"Error cargando token.json: {e}","ERROR")
        exit()


    