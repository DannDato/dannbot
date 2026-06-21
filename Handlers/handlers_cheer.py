import sqlite3
from datetime import datetime
import os

from Helpers.helpers import db_cursor, clean_text, normalize_username, safe_int
from Helpers.helpers_stats import update_global_stats
from Helpers.discord_notifier import notify_bits
from Helpers.colors import colorConvert, white, resetColor, userColors, channelColor, dorado
from Helpers.helpers_bot import new_user, update_stream_data
from Helpers.printlog import printlog


DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función para manejar las donaciones de bits 
async def handle_cheer(self, payload):
    """Guardar en la base de datos las donaciones realizadas
        Para estadísticas
    """
    chatter = payload.user
    CHATTER_NAME = normalize_username(chatter.name)
    CHATTER_ID = safe_int(chatter.id)
    AMMOUNT = safe_int(payload.bits)
    MESSAGE = clean_text(payload.message) if payload.message else ""
    BROACASTER_ID = safe_int(payload.broadcaster.id)

    try:
        #Nuevo usuario del canal
        await new_user(CHATTER_ID,CHATTER_NAME)

        # Obtener fecha actual
        now = datetime.now()
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('''
                INSERT INTO donated_bits (amount, user, message, date)
                VALUES (?, ?, ?, ?);
            ''', (AMMOUNT, CHATTER_ID, MESSAGE, now.strftime('%Y-%m-%d %H:%M:%S')))

        await update_stream_data("new_bits", AMMOUNT)
        printlog(f"{white}[{channelColor}{CHATTER_NAME}{white}]{dorado} Ha donado ({AMMOUNT}) bit{'s' if AMMOUNT > 1 else ''}")
        await notify_bits(CHATTER_NAME, AMMOUNT, MESSAGE)
        user = self.create_partialuser(BROACASTER_ID)
        await user.send_message(sender=self.user, message=f"¡Gracias por donar {AMMOUNT} bit{'s' if AMMOUNT > 1 else ''}, {payload.user.name}! 🎉")


    except sqlite3.Error as e:
        printlog(f"Ha ocurrido un error al guardar el mensaje recibido {e}","ERROR")
    finally:
        await update_global_stats("xp_Fuerza",CHATTER_ID,AMMOUNT)
            
