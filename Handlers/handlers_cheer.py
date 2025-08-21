import sqlite3
from datetime import datetime
import os

from Helpers.helpers import  cerrar_conexion, clean_text, normalize_username, safe_int
from Helpers.helpers_stats import update_global_stats
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

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obtener fecha actual
        now = datetime.now()
        year = now.year
        month = now.month

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        
        # Insertar datos
        cursor.execute(f'''
            INSERT INTO donated_bits (amount, user, message, date)
            VALUES (?, ?, ?, ?);
        ''', (AMMOUNT,CHATTER_ID,MESSAGE,now.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        await update_stream_data("new_bits", AMMOUNT)
        printlog(f"{white}[{channelColor}{CHATTER_NAME}{white}]{dorado} Ha donado ({AMMOUNT}) bit{'s' if AMMOUNT > 1 else ''}")
        user = self.create_partialuser(BROACASTER_ID)
        await user.send_message(sender=self.user, message=f"¡Gracias por donar {AMMOUNT} bit{'s' if AMMOUNT > 1 else ''}, {payload.user.name}! 🎉")
        
        if conn:
            conn.close()


    except sqlite3.Error as e:
        printlog(f"Ha ocurrido un error al guardar el mensaje recibido {e}","ERROR")
    finally:
            if conn:
                conn.close()
                cerrar_conexion(conn, cursor)
            await update_global_stats("xp_Fuerza",CHATTER_ID,AMMOUNT)
            
