import sys

from Helpers.oauth_flow import get_token_path, run_oauth_server_from_env, OAuthFlowCancelled
from Helpers.printlog import printlog


def main():
    auto_open_browser = '--no-auto-open' not in sys.argv
    try:
        token_data = run_oauth_server_from_env(auto_open_browser=auto_open_browser)
        print('OAuth completado correctamente.')
        print(f"Canal autorizado: {token_data.get('channel_name')}")
        print(f"Archivo generado: {get_token_path()}")
        return 0
    except OAuthFlowCancelled as exc:
        printlog(f'OAuth cancelado por el usuario: {exc}', 'WARNING')
        return 130
    except Exception as exc:
        printlog(f'Error en servidor OAuth: {exc}', 'ERROR')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())