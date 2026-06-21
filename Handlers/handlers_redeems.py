import sqlite3
from datetime import datetime
import logging
import os

from Helpers.helpers import db_cursor
from Helpers.helpers_stats import update_global_stats

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función para manejar el canjeo de recompensas de canal 
async def handle_redeem(name, user, self):
    """Guardar en la base de datos la recompensa canjeada
        Para estadísticas
    """
    user_data = await self.fetch_users(names=[user.name])  # Obtiene información completa del usuario
    if not user_data:
        logging.warning(f"No se pudo resolver usuario para redeem de {user.name}")
        return

    user_info = user_data[0]  # La API devuelve una lista, tomamos el primer elemento
    user_id = user_info.id

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute(
                '''INSERT INTO redeems (redeem, user, date )VALUES (?, ?, ?)''',
                (name, user_id, timestamp)
            )

        logging.info(f"\033[1;34m{user.name} \033[38;5;255m ha canjeado \033[38;5;51m '{name}'")
    except sqlite3.Error as e:
        logging.error(f"Ocurrió un error al capturar la recompensa canjeada: {e}")
    finally:
        await update_global_stats("xp_Fuerza", user_id, 0.15)