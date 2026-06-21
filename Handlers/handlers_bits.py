import sqlite3
from datetime import datetime
import logging
import os

from Helpers.helpers import clean_text, db_cursor, normalize_username, safe_int
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
    logging.info(f"[\033[38;5;221m D O N A C I O N {resetColor}] - {USERID} \033[38;5;221m[ {USERNAME} ]{resetColor} - {white}Ha donado {green}{AMMOUNT} Bitbit{'' if AMMOUNT == 1 else 's'}! Mensaje:{white}{MESSAGE} ")

    USER = SimpleNamespace(id=USERID, name=USERNAME)
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('''INSERT INTO donated_bits (amount, user, message, date)VALUES (?, ?, ?, ?)''', (AMMOUNT, USERID, MESSAGE, timestamp))

        broadcaster_id = safe_int(
            event.get("broadcaster_user_id")
            or event.get("channel_id")
            or getattr(self, "owner_id", 0)
        )
        if broadcaster_id > 0:
            channel_user = self.create_partialuser(broadcaster_id)
            await channel_user.send_message(
                sender=self.user,
                message=f"Ehh! @{USER.name} Gracias por {'ese' if AMMOUNT == 1 else 'esos'} {AMMOUNT} bit{'' if AMMOUNT == 1 else 's'}!"
            )
        else:
            logging.warning("No se pudo determinar broadcaster_id para anunciar bits en chat")


    except sqlite3.Error as e:
        logging.error(f"Ocurrió un error al capturar la donación de bits: {e}")
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado en handle_bits: {e}")
    finally:
        await update_global_stats("xp_Fuerza",USERID,0.15)
