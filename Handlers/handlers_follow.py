import sqlite3
from datetime import datetime
import logging
import os

from Helpers.helpers import db_cursor, clean_text, normalize_username, safe_int
from Helpers.helpers_stats import update_global_stats
from Helpers.colors import colorConvert, white, resetColor, userColors, channelColor, morado
from Helpers.helpers_bot import new_user, update_stream_data
from Helpers.helpers_dynamic import cache_follow_from_event
from Helpers.discord_notifier import notify_new_follow
from Helpers.printlog import printlog


DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función para manejar las donaciones de bits
async def handle_follow(self, payload):
    """Guardar en la base de datos las donaciones realizadas
        Para estadísticas
    """
    chatter = payload.user
    CHATTER_NAME = normalize_username(chatter.name)
    CHATTER_ID = safe_int(chatter.id)
    BROADCASTER_ID = safe_int(payload.broadcaster.id)
    try:
        #Nuevo usuario del canal
        await new_user(CHATTER_ID,CHATTER_NAME)

        # Obtener fecha actual
        now = datetime.now()
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('''
                SELECT name
                FROM sqlite_master
                WHERE type='table' AND name='followers';
            ''')
            table_exists = cursor.fetchone() is not None
            if not table_exists:
                cursor.execute('''
                    CREATE TABLE followers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user TEXT,
                        username TEXT,
                        date TEXT,
                        timestamp TEXT
                    );
                ''')
                printlog("Tabla 'followers' creada correctamente.")

            cursor.execute('''
                SELECT 1
                FROM followers
                WHERE user = ?;
            ''', (CHATTER_ID,))
            user_exists = cursor.fetchone() is not None
            if user_exists:
                printlog(f"El usuario {CHATTER_NAME} ya estaba registrado como seguidor.")
                return

            cursor.execute('''
                INSERT INTO followers (user, username, date, timestamp)
                VALUES (?, ?, ?, ?);
            ''', (CHATTER_ID, CHATTER_NAME, now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d %H:%M:%S')))

        # Cache followage solo una vez para preservar la fecha original.
        cache_follow_from_event(
            CHATTER_ID,
            BROADCASTER_ID,
            getattr(payload, "followed_at", None)
        )

        await update_stream_data("new_followers", 1)
        printlog(f"{morado} N U E V O    S E G U I D O R {white}  [ {channelColor}{CHATTER_NAME}{white} ({CHATTER_ID}) ]")
        await notify_new_follow(CHATTER_NAME)
        user = self.create_partialuser(BROADCASTER_ID)
        await user.send_message(sender=self.user, message=f"¡Gracias por seguirme, {payload.user.name}! 🎉")


    except sqlite3.Error as e:
        printlog(f"Ha ocurrido un error al guardar el mensaje recibido {e}","ERROR")
    finally:
        await update_global_stats("xp_Carisma",CHATTER_ID,5)

