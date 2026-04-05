import json
import os
import sys

from Helpers.printlog import printlog
from Helpers.oauth_flow import ensure_token_data, get_token_path, OAuthFlowCancelled


_TOKEN_CACHE = None


def _has_required_token_fields(token_data):
    return bool(
        token_data.get('access_token')
        and token_data.get('refresh_token')
        and token_data.get('client_id')
        and token_data.get('client_secret')
        and token_data.get('bot_id')
        and token_data.get('owner_id')
        and token_data.get('channel_name')
    )


def load_token(*, ensure_valid=False, force_refresh=False):
    """
    Carga token.json.

    - ensure_valid=True: valida/refresca token via OAuth flow (llamada de red).
    - ensure_valid=False: lectura local para evitar bloqueos durante imports.
    """
    global _TOKEN_CACHE

    if _TOKEN_CACHE is not None and not force_refresh:
        return dict(_TOKEN_CACHE)

    token_path = get_token_path()
    try:
        token_data = {}
        if os.path.exists(token_path):
            with open(token_path, 'r', encoding='utf-8') as file:
                token_data = json.load(file)

        needs_oauth = ensure_valid or not _has_required_token_fields(token_data)
        if needs_oauth:
            token_data = ensure_token_data()

        _TOKEN_CACHE = dict(token_data)
        return dict(token_data)
    except json.JSONDecodeError as e:
        printlog(f"Error al decodificar el archivo JSON: {e}", "ERROR")
        exit()
    except OAuthFlowCancelled as e:
        printlog(f"Autorización cancelada. Cerrando bot de forma segura: {e}", "WARNING")
        raise SystemExit(0)
    except Exception as e:
        printlog(f"Error cargando token.json: {e}", "ERROR")
        raise SystemExit(1)


    