import sys

from Helpers.oauth_flow import get_token_path, run_oauth_server_from_env


def main():
    auto_open_browser = '--no-auto-open' not in sys.argv
    token_data = run_oauth_server_from_env(auto_open_browser=auto_open_browser)
    print('OAuth completado correctamente.')
    print(f"Canal autorizado: {token_data.get('channel_name')}")
    print(f"Archivo generado: {get_token_path()}")


if __name__ == '__main__':
    main()