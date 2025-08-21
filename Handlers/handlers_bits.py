import sqlite3
from datetime import datetime
import logging
import os

from Helpers.helpers import  cerrar_conexion, clean_text, normalize_username, safe_int
from Helpers.helpers_stats import update_global_stats
from Helpers.colors import colorConvert, white, resetColor, green
from Helpers.helpers_bot import new_user, update_stream_data

from types import SimpleNamespace

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función para manejar las donaciones de bits 
async def handle_bits(self, payload):
    """Guardar en la base de datos las donaciones realizadas
        Para estadísticas
    """
    event = payload["event"]
    if not event : return
    
    USERNAME = normalize_username(event["user_name"]).strip()
    USERID = safe_int(event["user_id"].strip())
    AMMOUNT = safe_int(event["bits"])
    MESSAGE = clean_text(event["message"]).strip().lower().replace("cheer"+str(AMMOUNT),'').strip()
    USER = SimpleNamespace(id=USERID, name=USERNAME)

    logging.info(f"[\033[38;5;221m D O N A C I O N {resetColor}] - {USERID} \033[38;5;221m[ {USERNAME} ]{resetColor} - {white}Ha donado {green}{AMMOUNT} Bitbit{'' if AMMOUNT == 1 else 's'}! Mensaje:{white}{MESSAGE} ")

    USER = SimpleNamespace(id=USERID, name=USERNAME)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Insertar el nuevo registro en la tabla
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''INSERT INTO donated_bits (amount, user, message, date)VALUES (?, ?, ?, ?)''', ( AMMOUNT, USERID, MESSAGE, timestamp))
        # Confirmar los cambios y cerrar la conexión
        conn.commit()   
        conn.close()
        cerrar_conexion(conn, cursor)
        ctx = "danndato"
        await ctx.send(f"Ehh! @{USER.name} Gracias por {'ese' if AMMOUNT == 1 else 'esos'} {AMMOUNT} bit{'' if AMMOUNT == 1 else 's'}!")


    except sqlite3.Error as e:
        logging.error("Ocurrió un error al capturar la donación de bits")
    finally:
            if conn:
                conn.close()
                cerrar_conexion(conn, cursor)
            await update_global_stats("xp_Fuerza",USERID,0.15)
