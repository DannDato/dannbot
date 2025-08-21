import sqlite3
from datetime import datetime
import logging
import os

from Helpers.helpers import  cerrar_conexion, clean_text, normalize_username, safe_int
from Helpers.helpers_stats import update_global_stats
from Helpers.colors import colorConvert, white, resetColor, userColors, channelColor, morado
from Helpers.helpers_bot import new_user, update_stream_data
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
    BROACASTER_ID = safe_int(payload.broadcaster.id)
    try:
        #Nuevo usuario del canal
        await new_user(CHATTER_ID,CHATTER_NAME)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obtener fecha actual
        now = datetime.now()
        year = now.year
        month = now.month
        table_name = f"chat_{year}{month:02}"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificar si la tabla existe
        cursor.execute('''
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name='followers';
        ''', ())
        table_exists = cursor.fetchone() is not None
        if not table_exists:
            # Crear la tabla si no existe
            cursor.execute(f'''
                CREATE TABLE followers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    username TEXT,
                    date TEXT,
                    timestamp TEXT
                );
            ''')
            printlog(f"Tabla 'followers' creada correctamente.")

        cursor.execute('''
            SELECT *
            FROM followers
            WHERE user = ?;
        ''', (CHATTER_ID,))
        user_exists = cursor.fetchone() is not None
        if user_exists:
            printlog(f"El usuario {CHATTER_NAME} ya estaba registrado como seguidor.")
            return
        # Insertar datos
        cursor.execute(f'''
            INSERT INTO followers (user, username, date, timestamp)
            VALUES (?, ?, ?, ?);
        ''', (CHATTER_ID,CHATTER_NAME, now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        await update_stream_data("new_followers", 1)
        printlog(f"{morado} N U E V O    S E G U I D O R {white}  [ {channelColor}{CHATTER_NAME}{white} ({CHATTER_ID}) ]")
        user = self.create_partialuser(BROACASTER_ID)
        await user.send_message(sender=self.user, message=f"¡Gracias por seguirme, {payload.user.name}! 🎉")
        if conn:
            conn.close()


    except sqlite3.Error as e:
        printlog(f"Ha ocurrido un error al guardar el mensaje recibido {e}","ERROR")
    finally:
            if conn:
                conn.close()
                cerrar_conexion(conn, cursor)
            await update_global_stats("xp_Carisma",CHATTER_ID,5)
            
