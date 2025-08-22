
import sqlite3
from datetime import datetime
import os

from Helpers.helpers import  cerrar_conexion, clean_text, normalize_username, safe_int
from Helpers.helpers_stats import update_global_stats
from Helpers.colors import colorConvert, white, resetColor, userColors, channelColor
from Helpers.helpers_bot import new_user, update_stream_data
from Helpers.printlog import printlog
from Helpers.helpers_dynamic import analisis, interactuar, desafiar

from types import SimpleNamespace

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función para manejar las donaciones de bits 
async def handle_message(self, payload):
    """
    Guardar en la base de datos lOS MENSAJES
    Para estadísticas
    """
    self.messages_processed += 1
    chatter = payload.chatter
    CHATTER_NAME = normalize_username(chatter.name)
    CHATTER_ID = safe_int(chatter.id)
    CHATTER_COLOR = colorConvert(chatter.color.hex_clean) if chatter.color else userColors.get("regularUserColor", white)
    BROADCASTER_NAME = clean_text(payload.broadcaster.name)
    BROADCASTER_ID = safe_int(payload.broadcaster.id)
    MESSAGE = clean_text(payload.text)
    if MESSAGE.startswith("!"):
        self.commands_executed += 1

    printlog(
        f"{CHATTER_ID} {resetColor}Chat:"
        f" {CHATTER_COLOR}{CHATTER_NAME}{resetColor} "
        f"- {white}{MESSAGE}"
    )
    #Dinamicas aplicadas a los mensajes
    await analisis(MESSAGE, CHATTER_ID)
    await interactuar(self, MESSAGE, CHATTER_NAME)
    await desafiar(self, CHATTER_NAME)
    #_________________________________________________


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
            WHERE type='table' AND name=?;
        ''', (table_name,))
        table_exists = cursor.fetchone() is not None
        if not table_exists:
            # Crear la tabla si no existe
            cursor.execute(f'''
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    username TEXT,
                    message TEXT,
                    date TEXT,
                    timestamp TEXT
                );
            ''')
            printlog(f"Tabla '{table_name}' creada correctamente.")

        # Insertar datos
        cursor.execute(f'''
            INSERT INTO {table_name} (user, username, message, date, timestamp)
            VALUES (?, ?, ?, ?, ?);
        ''', (CHATTER_ID,CHATTER_NAME,MESSAGE, now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

        if conn:
            conn.close()

        await update_stream_data("total_messages",1)
        await update_global_stats("messages",CHATTER_ID,1)


    except sqlite3.Error as e:
        printlog(f"Ha ocurrido un error al guardar el mensaje recibido {e}","ERROR")
    finally:
            if conn:
                conn.close()
                cerrar_conexion(conn, cursor)
            await update_global_stats("xp_Voluntad",CHATTER_ID,0.05)
