import sqlite3
from datetime import datetime
import logging
import os

from Helpers.helpers import  cerrar_conexion
from Helpers.helpers_stats import update_global_stats
from Helpers.token_loader import load_token

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función para manejar el canjeo de recompensas de canal 
async def handle_redeem(self, payload):
    """Guardar en la base de datos la recompensa canjeada
        Para estadísticas
    """
    