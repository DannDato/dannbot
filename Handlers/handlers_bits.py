import sqlite3
from datetime import datetime
import logging
import os

from Helpers.helpers import  cerrar_conexion
from Helpers.helpers_stats import update_global_stats

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función para manejar las donaciones de bits 
async def handle_bits(amount, user, message, self):
    """Guardar en la base de datos las donaciones realizadas
        Para estadísticas
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Insertar el nuevo registro en la tabla
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''INSERT INTO donated_bits (amount, username, message, date)VALUES (?, ?, ?, ?)''', ( amount, user, message, timestamp))
        # Confirmar los cambios y cerrar la conexión
        conn.commit()   
        conn.close()
        cerrar_conexion(conn, cursor)
        ctx = self.get_channel(self.nick)
        await ctx.send(f"Ehh! @{user} Gracias por {'ese' if amount == 1 else 'esos'} {amount} bit{'' if amount == 1 else 's'}!")
        logging.info(f" \033[38;5;11m{user} \033[38;5;255m ha donado \033[38;5;51m '{amount}' bit{'' if amount == 1 else 's'}!")

    except sqlite3.Error as e:
        logging.error("Ocurrió un error al capturar la donación de bits")
    finally:
            if conn:
                conn.close()
                cerrar_conexion(conn, cursor)
            await update_global_stats("xp_Fuerza",user,0.15)
