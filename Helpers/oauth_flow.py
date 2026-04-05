import json
import os
import secrets
import subprocess
import sys
import threading
import asyncio
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

try:
    import certifi

    # Ensure HTTPS calls to Twitch validate against a known CA bundle.
    os.environ.setdefault('SSL_CERT_FILE', certifi.where())
    os.environ.setdefault('REQUESTS_CA_BUNDLE', certifi.where())
except Exception:
    pass

import aiohttp

from Helpers.printlog import printlog
from Helpers.required_scopes import required_scopes


TOKEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Credentials'))
TOKEN_PATH = os.path.join(TOKEN_DIR, 'token.json')
REDIRECT_HOST = 'localhost'
REDIRECT_PORT = 8080
HEALTH_PATH = '/health'
START_PATH = '/start'
REDIRECT_PATH = '/'
REDIRECT_URI = f'http://{REDIRECT_HOST}:{REDIRECT_PORT}'
AUTHORIZE_URL = 'https://id.twitch.tv/oauth2/authorize'
TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
VALIDATE_URL = 'https://id.twitch.tv/oauth2/validate'
USERS_URL = 'https://api.twitch.tv/helix/users'
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SERVER_SCRIPT = os.path.join(REPO_ROOT, 'server.py')
ENV_PATH = os.path.join(REPO_ROOT, '.env')
TOKEN_FIELDS = (
    'access_token',
    'refresh_token',
    'client_id',
    'client_secret',
    'bot_id',
    'channel_name',
    'owner_id',
)

_TOKEN_CACHE = None


class OAuthFlowCancelled(Exception):
    """Se lanza cuando el usuario cancela/deniega la autorización OAuth."""


def get_token_path():
    return TOKEN_PATH


def get_server_base_url():
    return f'http://{REDIRECT_HOST}:{REDIRECT_PORT}'


def get_healthcheck_url():
    return f'{get_server_base_url()}{HEALTH_PATH}'


def get_authorize_entrypoint_url():
    return f'{get_server_base_url()}{START_PATH}'


def _ensure_token_dir():
    os.makedirs(TOKEN_DIR, exist_ok=True)


def _load_env_file(path=ENV_PATH):
    """Carga variables desde .env sin sobrescribir variables ya presentes."""
    if not os.path.exists(path):
        return

    try:
        with open(path, 'r', encoding='utf-8') as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                if not key:
                    continue

                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                os.environ.setdefault(key, value)
    except Exception as exc:
        printlog(f'No se pudo cargar .env ({path}): {exc}', 'WARNING')


def _load_token_file():
    if not os.path.exists(TOKEN_PATH):
        return {}

    with open(TOKEN_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)


def _save_token_file(data):
    _ensure_token_dir()
    with open(TOKEN_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def _is_interactive():
    return sys.stdin.isatty()


def _prompt_value(label, current_value=None, allow_empty=False):
    suffix = f' [{current_value}]' if current_value else ''
    value = input(f'{label}{suffix}: ').strip()
    if value:
        return value
    if current_value:
        return current_value
    if allow_empty:
        return ''
    raise RuntimeError(f'Se requiere el valor {label}.')


def _prompt_for_client_credentials(existing_data):
    data = dict(existing_data)

    if data.get('client_id') and data.get('client_secret'):
        return data

    if not _is_interactive():
        raise RuntimeError('No hay credenciales de Twitch y el entorno no es interactivo para solicitarlas.')

    printlog('No se encontraron credenciales completas de Twitch. Se solicitarán para iniciar el OAuth.', 'WARNING')
    data['client_id'] = _prompt_value('Twitch CLIENT_ID', data.get('client_id'))
    data['client_secret'] = _prompt_value('Twitch CLIENT_SECRET', data.get('client_secret'))
    return data


def _validate_token(access_token, expected_client_id=None):
    if not access_token:
        return None

    async def _request():
        headers = {'Authorization': f'OAuth {access_token}'}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(VALIDATE_URL, headers=headers, timeout=15) as response:
                    if response.status != 200:
                        return None
                    return await response.json(content_type=None)
        except aiohttp.ClientError:
            return None

    payload = asyncio.run(_request())
    if not payload:
        return None
    if expected_client_id and payload.get('client_id') != expected_client_id:
        return None
    return payload


def _refresh_access_token(token_data):
    refresh_token = token_data.get('refresh_token')
    if not refresh_token:
        return None

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': token_data['client_id'],
        'client_secret': token_data['client_secret'],
    }

    async def _request():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(TOKEN_URL, data=payload, timeout=20) as response:
                    body = await response.text()
                    if response.status != 200:
                        printlog(f'No se pudo refrescar el access token: {body}', 'WARNING')
                        return None
                    return json.loads(body)
        except aiohttp.ClientError as exc:
            printlog(f'No se pudo refrescar el access token: {exc}', 'WARNING')
            return None

    return asyncio.run(_request())


def _fetch_authenticated_user(access_token, client_id):
    async def _request():
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Client-ID': client_id,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(USERS_URL, headers=headers, timeout=20) as response:
                response.raise_for_status()
                return await response.json(content_type=None)

    payload = asyncio.run(_request())

    if not payload.get('data'):
        raise RuntimeError('Twitch no devolvió datos del usuario autenticado.')

    return payload['data'][0]


def _has_required_scopes(scopes):
    current = set(scopes or [])
    expected = set(required_scopes)
    return expected.issubset(current)


def _build_token_data(existing_data, token_payload, user_payload, validated_payload=None):
    merged = dict(existing_data)
    merged.update(
        {
            'access_token': token_payload['access_token'],
            'refresh_token': token_payload.get('refresh_token', merged.get('refresh_token')),
            'client_id': merged['client_id'],
            'client_secret': merged['client_secret'],
            'bot_id': user_payload['id'],
            'owner_id': user_payload['id'],
            'channel_name': user_payload['login'],
            'scopes': token_payload.get('scope') or (validated_payload or {}).get('scopes') or merged.get('scopes', []),
            'token_type': token_payload.get('token_type', merged.get('token_type', 'bearer')),
            'expires_in': token_payload.get('expires_in', (validated_payload or {}).get('expires_in')),
            'token_obtained_at': int(time.time()),
        }
    )
    return merged


def _token_is_usable(token_data):
    return all(token_data.get(field) for field in TOKEN_FIELDS)


def _authorization_url(client_id, state):
    query = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(required_scopes),
        'force_verify': 'true',
        'state': state,
    }
    return f'{AUTHORIZE_URL}?{urlencode(query)}'


def _exchange_code_for_token(client_id, client_secret, code):
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    }
    async def _request():
        async with aiohttp.ClientSession() as session:
            async with session.post(TOKEN_URL, data=payload, timeout=20) as response:
                response.raise_for_status()
                return await response.json(content_type=None)

    return asyncio.run(_request())


def _wait_for_server_ready(timeout=30):
    deadline = time.time() + timeout
    last_error = None

    async def _ping_healthcheck():
        async with aiohttp.ClientSession() as session:
            async with session.get(get_healthcheck_url(), timeout=2) as response:
                return response.status

    while time.time() < deadline:
        try:
            response_status = asyncio.run(_ping_healthcheck())
            if response_status == 200:
                return
        except Exception as exc:
            last_error = exc
        threading.Event().wait(0.25)

    raise TimeoutError(f'El servidor OAuth no respondió a tiempo. Último error: {last_error}')


def _run_oauth_server(existing_data, auto_open_browser=False, timeout=300):
    state = secrets.token_urlsafe(24)
    result = {'token_data': None, 'error': None}
    auth_url = _authorization_url(existing_data['client_id'], state)
    server = None
    server_finished = threading.Event()

    class OAuthHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def _write_response(self, status_code, body, content_type='text/html; charset=utf-8', extra_headers=None):
            self.send_response(status_code)
            self.send_header('Content-Type', content_type)
            if extra_headers:
                for key, value in extra_headers.items():
                    self.send_header(key, value)
            self.end_headers()
            if isinstance(body, str):
                body = body.encode('utf-8')
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == HEALTH_PATH:
                self._write_response(200, '{"status":"ready"}', 'application/json; charset=utf-8')
                return

            if parsed.path == START_PATH:
                self.send_response(302)
                self.send_header('Location', auth_url)
                self.end_headers()
                return

            if parsed.path != REDIRECT_PATH:
                self._write_response(404, '<h1>Ruta no encontrada</h1>')
                return

            params = parse_qs(parsed.query)
            returned_state = params.get('state', [''])[0]
            code = params.get('code', [''])[0]
            error = params.get('error', [''])[0]
            error_description = params.get('error_description', [''])[0]

            try:
                if returned_state != state:
                    raise RuntimeError('Estado OAuth invalido.')
                if error:
                    if error == 'access_denied':
                        raise OAuthFlowCancelled(
                            error_description or 'El usuario canceló/denegó la autorización de Twitch.'
                        )
                    raise RuntimeError(error_description or error)
                if not code:
                    raise RuntimeError('Twitch no devolvió un código de autorización.')

                token_payload = _exchange_code_for_token(existing_data['client_id'], existing_data['client_secret'], code)
                user_payload = _fetch_authenticated_user(token_payload['access_token'], existing_data['client_id'])
                token_data = _build_token_data(existing_data, token_payload, user_payload)
                _save_token_file(token_data)
                result['token_data'] = token_data
                html = f"""
                    <!DOCTYPE html>
                    <html lang="es">
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            body {{
                                background-color: #0e0e10;
                                color: #efeff1;
                                font-family: 'Inter', 'Roobert', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                height: 100vh;
                                margin: 0;
                                padding: 2rem;
                            }}
                            .card {{
                                background-color: #18181b;
                                padding: 3rem;
                                border-radius: 12px;
                                text-align: center;
                                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                                border-top: 4px solid #9147ff;
                                max-width: 400px;
                                animation: fadeIn 0.5s ease-out;
                            }}
                            h1 {{
                                color: #9147ff;
                                margin-top: 0;
                                font-size: 2.5rem;
                                letter-spacing: -1px;
                            }}
                            p {{
                                font-size: 1.1rem;
                                line-height: 1.6;
                                color: #adadb8;
                            }}
                            .status-icon {{
                                background: #9147ff;
                                width: 60px;
                                height: 60px;
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                margin: 0 auto 1.5rem;
                                font-size: 1.5rem;
                                color: white;
                            }}
                            @keyframes fadeIn {{
                                from {{ opacity: 0; transform: translateY(20px); }}
                                to {{ opacity: 1; transform: translateY(0); }}
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="card">
                            <div class="status-icon">✓</div>
                            <h1>DannBot</h1>
                            <p>Autorización recibida.<br><strong>Ya puedes cerrar esta ventana y volver a la consola.</strong></p>
                        </div>
                    </body>
                    </html>
                """
                self._write_response(200, html)
            except OAuthFlowCancelled as exc:
                result['error'] = f'OAUTH_CANCELLED:{exc}'
                html = f"""
                    <!DOCTYPE html>
                    <html lang="es">
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            body {{
                                background-color: #0e0e10;
                                color: #efeff1;
                                font-family: 'Inter', 'Roobert', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                height: 100vh;
                                margin: 0;
                                padding: 2rem;
                            }}
                            .card {{
                                background-color: #18181b;
                                padding: 3rem;
                                border-radius: 12px;
                                text-align: center;
                                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                                border-top: 4px solid #f0ad4e;
                                max-width: 450px;
                            }}
                            h1 {{
                                color: #f0ad4e;
                                margin-top: 0;
                                font-size: 2.2rem;
                            }}
                            p {{
                                font-size: 1.05rem;
                                line-height: 1.5;
                                color: #adadb8;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="card">
                            <h1>DannBot</h1>
                            <p>Autorización cancelada.<br><strong>Puedes cerrar esta ventana y volver a intentarlo cuando quieras.</strong></p>
                        </div>
                    </body>
                    </html>
                """
                self._write_response(200, html)
            except Exception as exc:
                result['error'] = str(exc)
                html = f"""
                    <!DOCTYPE html>
                    <html lang="es">
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            body {{
                                background-color: #0e0e10;
                                color: #efeff1;
                                font-family: 'Inter', 'Roobert', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                height: 100vh;
                                margin: 0;
                                padding: 2rem;
                            }}
                            .card {{
                                background-color: #18181b;
                                padding: 3rem;
                                border-radius: 12px;
                                text-align: center;
                                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                                border-top: 4px solid #eb0400; /* Rojo de error estilo Twitch */
                                max-width: 400px;
                                animation: shake 0.4s ease-in-out; /* Animación de sacudida para el error */
                            }}
                            h1 {{
                                color: #eb0400;
                                margin-top: 0;
                                font-size: 2.5rem;
                                letter-spacing: -1px;
                            }}
                            p {{
                                font-size: 1.1rem;
                                line-height: 1.6;
                                color: #adadb8;
                            }}
                            .status-icon {{
                                background: #eb0400;
                                width: 60px;
                                height: 60px;
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                margin: 0 auto 1.5rem;
                                font-size: 1.8rem;
                                color: white;
                                font-weight: bold;
                            }}
                            @keyframes shake {{
                                0%, 100% {{ transform: translateX(0); }}
                                25% {{ transform: translateX(-10px); }}
                                75% {{ transform: translateX(10px); }}
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="card">
                            <div class="status-icon">✕</div>
                            <h1>DannBot</h1>
                            <p>Hubo un problema con la autorización.<br><strong>Por favor, intenta el proceso de nuevo en la consola.</strong></p>
                        </div>
                    </body>
                    </html>
                    """
                self._write_response(500, html)
            finally:
                threading.Thread(target=server.shutdown, daemon=True).start()

    try:
        server = HTTPServer((REDIRECT_HOST, REDIRECT_PORT), OAuthHandler)
    except OSError as exc:
        raise RuntimeError(
            f'No se pudo iniciar el servidor OAuth local en {REDIRECT_HOST}:{REDIRECT_PORT}. {exc}'
        ) from exc

    if auto_open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(get_authorize_entrypoint_url(), new=1, autoraise=True)).start()

    def shutdown_on_timeout():
        if server_finished.wait(timeout):
            return
        if result['error'] is None and result['token_data'] is None:
            result['error'] = 'Se agotó el tiempo de espera del callback OAuth de Twitch.'
        try:
            server.shutdown()
        except Exception:
            pass

    timeout_thread = threading.Thread(target=shutdown_on_timeout, daemon=True)
    timeout_thread.start()

    printlog(f'Servidor OAuth escuchando en {get_server_base_url()}', 'INFO')
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        server_finished.set()
        server.server_close()

    if result['error']:
        if result['error'].startswith('OAUTH_CANCELLED:'):
            raise OAuthFlowCancelled(result['error'].split(':', 1)[1].strip())
        raise RuntimeError(result['error'])
    if not result['token_data']:
        raise RuntimeError('El servidor OAuth terminó sin generar credenciales.')

    return dict(result['token_data'])


def _run_oauth_via_server_process(existing_data, timeout=300):
    env = os.environ.copy()
    env['DANNBOT_CLIENT_ID'] = existing_data['client_id']
    env['DANNBOT_CLIENT_SECRET'] = existing_data['client_secret']

    process = subprocess.Popen([sys.executable, SERVER_SCRIPT, '--no-auto-open'], cwd=REPO_ROOT, env=env)
    try:
        _wait_for_server_ready()
        printlog('Servidor OAuth listo. Abriendo navegador para autorizar scopes de Twitch...', 'INFO')
        if not webbrowser.open(get_authorize_entrypoint_url(), new=1, autoraise=True):
            printlog('No se pudo abrir el navegador automáticamente. Abre esta URL manualmente:', 'WARNING')
            print(get_authorize_entrypoint_url())

        process.wait(timeout=timeout)
    except Exception:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        raise

    if process.returncode == 130:
        raise OAuthFlowCancelled('El usuario canceló la autorización OAuth.')

    if process.returncode != 0:
        raise RuntimeError(f'El servidor OAuth terminó con código {process.returncode}.')

    token_data = _load_token_file()
    reusable = _reuse_existing_token(token_data)
    if reusable is None:
        raise RuntimeError('El servidor OAuth terminó, pero las credenciales guardadas no son válidas.')

    return reusable


def _run_browser_oauth(existing_data):
    return _run_oauth_via_server_process(existing_data)


def _reuse_existing_token(existing_data):
    validated = _validate_token(existing_data.get('access_token'), existing_data.get('client_id'))
    if validated and _has_required_scopes(validated.get('scopes')):
        user_payload = _fetch_authenticated_user(existing_data['access_token'], existing_data['client_id'])
        token_payload = {
            'access_token': existing_data['access_token'],
            'refresh_token': existing_data.get('refresh_token'),
            'scope': validated.get('scopes', []),
            'token_type': 'bearer',
            'expires_in': validated.get('expires_in'),
        }
        return _build_token_data(existing_data, token_payload, user_payload, validated)

    refreshed = _refresh_access_token(existing_data)
    if not refreshed:
        return None

    validated = _validate_token(refreshed['access_token'], existing_data.get('client_id'))
    if not validated or not _has_required_scopes(validated.get('scopes')):
        return None

    user_payload = _fetch_authenticated_user(refreshed['access_token'], existing_data['client_id'])
    return _build_token_data(existing_data, refreshed, user_payload, validated)


def ensure_token_data(force_reauth=False):
    global _TOKEN_CACHE

    _load_env_file()

    if _TOKEN_CACHE and not force_reauth:
        return dict(_TOKEN_CACHE)

    existing_data = _load_token_file()
    env_client_id = os.environ.get('DANNBOT_CLIENT_ID') or os.environ.get('TWITCH_CLIENT_ID')
    env_client_secret = os.environ.get('DANNBOT_CLIENT_SECRET') or os.environ.get('TWITCH_CLIENT_SECRET')

    if env_client_id:
        existing_data['client_id'] = env_client_id
    if env_client_secret:
        existing_data['client_secret'] = env_client_secret

    existing_data = _prompt_for_client_credentials(existing_data)

    token_data = None
    if not force_reauth and existing_data.get('access_token'):
        token_data = _reuse_existing_token(existing_data)

    if token_data is None:
        token_data = _run_browser_oauth(existing_data)

    if not _token_is_usable(token_data):
        raise RuntimeError('El flujo OAuth terminó sin producir un token utilizable para el bot.')

    _save_token_file(token_data)
    _TOKEN_CACHE = dict(token_data)
    return dict(token_data)


def run_oauth_server_from_env(auto_open_browser=True):
    _load_env_file()

    existing_data = _load_token_file()
    client_id = (
        os.environ.get('DANNBOT_CLIENT_ID')
        or os.environ.get('TWITCH_CLIENT_ID')
        or existing_data.get('client_id')
    )
    client_secret = (
        os.environ.get('DANNBOT_CLIENT_SECRET')
        or os.environ.get('TWITCH_CLIENT_SECRET')
        or existing_data.get('client_secret')
    )

    if not client_id or not client_secret:
        existing_data = _prompt_for_client_credentials(existing_data)
        client_id = existing_data['client_id']
        client_secret = existing_data['client_secret']

    existing_data['client_id'] = client_id
    existing_data['client_secret'] = client_secret
    return _run_oauth_server(existing_data, auto_open_browser=auto_open_browser)
