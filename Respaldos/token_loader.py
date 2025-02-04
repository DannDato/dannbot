import json
import os

def load_token():
    #Carga el token desde el archivo token.json.
    token_path = os.path.join(os.path.dirname(__file__), '..', 'Credentials', 'token.json')
    print(f"Ruta generada: {token_path}")
    if os.path.exists(token_path):
        print(f"El archivo se encuentra en: {token_path}")
    else:
        print("No se encontró el archivo en la ruta especificada.")
    try:
        with open(token_path, 'r') as file: 
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error cargando token.json: {e}")
        exit()
