import sqlite3
from datetime import datetime
import logging
import os

from Helpers.helpers import  cerrar_conexion
from Helpers.helpers_stats import update_global_stats
from Helpers.token_loader import load_token

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función para manejar el canjeo de recompensas de canal 
async def handle_sub(event, self):
    """Guardar en la base de datos la recompensa canjeada
        Para estadísticas
    """
    logging.warning(f"Manejando sub")
    ctx = self.get_channel(self.nick)
    user=event.user.name
    await ctx.send(f"Ehh! @{user} Gracias por eso!")

    # try:
    #     conn = sqlite3.connect(DB_PATH)
    #     cursor = conn.cursor()
    #     # Insertar el nuevo registro en la tabla
    #     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #     cursor.execute('''INSERT INTO redeems (redeem, username, date )VALUES (?, ?, ?)''', ("SUB", user, timestamp))
    #     # Confirmar los cambios y cerrar la conexión
    #     conn.commit()
    #     conn.close()
    #     cerrar_conexion(conn, cursor)

    #     logging.info(f"\033[1;34m{user} \033[38;5;255m ha canjeado \033[38;5;51m '{name}'")

    # except sqlite3.Error as e:
    #     logging.error("Ocurrió un error al capturar la recompensa canjeada")
    # finally:
    #         if conn:
    #             conn.close()
    #             cerrar_conexion(conn, cursor)
    #         await update_global_stats("xp_Fuerza",user,0.15)

async def handle_sub_gift(event, self):
    """Guardar en la base de datos la recompensa canjeada
        Para estadísticas
    """
    logging.warning(f"Manejando sub regalada")
    ctx = self.get_channel(self.nick)
    user=event.user.name
    await ctx.send(f"Ehh! @{user} Gracias por ese regalo!")