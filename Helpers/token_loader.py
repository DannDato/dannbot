import json
import os
import sys

from Helpers.printlog import printlog
from Helpers.oauth_flow import ensure_token_data, get_token_path, OAuthFlowCancelled, clear_token_cache, silent_refresh_token


_TOKEN_CACHE = None
_TOKEN_CACHE_MTIME = None


def _get_token_mtime(token_path):
    try:
        return os.path.getmtime(token_path)
    except OSError:
        return None


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


def load_token(*, ensure_valid=False, force_refresh=False, allow_interactive=True):
    """
    Carga token.json.

    - ensure_valid=True: valida/refresca token via OAuth flow (llamada de red).
    - ensure_valid=False: lectura local para evitar bloqueos durante imports.
    """
    global _TOKEN_CACHE, _TOKEN_CACHE_MTIME

    token_path = get_token_path()
    current_mtime = _get_token_mtime(token_path)

    if _TOKEN_CACHE is not None and not force_refresh and _TOKEN_CACHE_MTIME == current_mtime:
        return dict(_TOKEN_CACHE)

    try:
        token_data = {}
        if os.path.exists(token_path):
            with open(token_path, 'r', encoding='utf-8') as file:
                token_data = json.load(file)

        needs_oauth = ensure_valid or not _has_required_token_fields(token_data)
        if needs_oauth:
            token_data = ensure_token_data(allow_interactive=allow_interactive)
            current_mtime = _get_token_mtime(token_path)

        _TOKEN_CACHE = dict(token_data)
        _TOKEN_CACHE_MTIME = current_mtime
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

def refresh_token_silent():
    """
        Refresca el token de forma silenciosa (sin OAuth interactivo).

        Retorna un dict con estado:
            {"ok": bool, "code": str, "detail": str}
        Pensado para background refresh tasks en producción.

        Si falla, solo loguea y retorna estado no-ok; no dispara excepciones.
    """
    global _TOKEN_CACHE, _TOKEN_CACHE_MTIME

    status = silent_refresh_token()

    if status.get("ok"):
        # Limpiar cache para forzar recarga del token actualizado
        _TOKEN_CACHE = None
        _TOKEN_CACHE_MTIME = None

    return status

def delete_token_file():
    """Elimina token.json y limpia caches en memoria."""
    global _TOKEN_CACHE, _TOKEN_CACHE_MTIME

    token_path = get_token_path()
    deleted = False

    try:
        if os.path.exists(token_path):
            os.remove(token_path)
            deleted = True
    finally:
        _TOKEN_CACHE = None
        _TOKEN_CACHE_MTIME = None
        clear_token_cache()

    return deleted, token_path


    