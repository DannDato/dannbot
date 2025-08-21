import sqlite3
from datetime import datetime
import logging
import os

from Helpers.helpers import  cerrar_conexion, clean_text, normalize_username, safe_int
from Helpers.helpers_stats import update_global_stats
from Helpers.colors import colorConvert, white, resetColor, userColors, channelColor, dorado
from Helpers.helpers_bot import new_user, update_stream_data
from Helpers.printlog import printlog


DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función para manejar las subs
async def handle_sub(self, payload):
    """
    ____________________sub_______________
    CHATER_NAME         CHATTER_ID  GIFT    TIER    BROACASTER_ID
    solo_sigo_gayss_    1317807643  True    1000    439400816
    <class 'str'> 
    <class 'int'> 
    <class 'bool'> 
    <class 'str'> 
    <class 'int'>
    ______________________________________

    """
    chatter = payload.user
    CHATTER_NAME = normalize_username(chatter.name)
    CHATTER_ID = safe_int(chatter.id)
    GIFT = payload.gift
    TIER = clean_text(payload.tier) if payload.tier else ""
    BROACASTER_ID = safe_int(payload.broadcaster.id)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obtener fecha actual
        now = datetime.now()
        year = now.year
        month = now.month

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Verificar si la tabla existe
        cursor.execute('''
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name='subscriptions';
        ''', ())
        table_exists = cursor.fetchone() is not None
        if not table_exists:
            # Crear la tabla si no existe
            cursor.execute(f'''
                CREATE TABLE subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    username TEXT,
                    gift BOOLEAN,
                    tier TEXT,
                    date TEXT,
                    timestamp TEXT
                );
            ''')
            printlog(f"Tabla 'subscriptions' creada correctamente.")
        # Insertar datos
        cursor.execute(f'''
            INSERT INTO subscriptions (user, username, gift, tier, date, timestamp)
            VALUES (?, ?, ?, ?, ?, ?);
        ''', (CHATTER_ID, CHATTER_NAME, GIFT, TIER, now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        await update_stream_data("new_subs", 1)

        printlog(f"{dorado}{"Le han regalado una suscripción a " if GIFT else "Se ha suscrito "}{white}[{channelColor}{CHATTER_NAME}{white}]{dorado} Tier {TIER} ")
        user = self.create_partialuser(BROACASTER_ID)
        await user.send_message(sender=self.user, message=f"[BOT] - ¡Gracias por suscribirte @{CHATTER_NAME}! 🎉" if not GIFT else f"[BOT] - ¡Agradece por esa suscripción  @{CHATTER_NAME}! 🎉")
        
        if conn:
            conn.close()


    except sqlite3.Error as e:
        printlog(f"Ha ocurrido un error al guardar al nuevo suscriptor {e}","ERROR")
    finally:
            if conn:
                conn.close()
                cerrar_conexion(conn, cursor)
            await update_global_stats("xp_Fuerza",CHATTER_ID,5)
            await update_global_stats("History_Subs",CHATTER_ID,1)
            await update_global_stats("Subscription",CHATTER_ID,1)

            
async def handle_sub_gift(self, payload):
    """
     _________________regalo_______________
    CHATER_NAME     CHATTER_ID  TIER    BROACASTER_ID   TOTAL
    dannievt        1003698641  1000    439400816       1
    <class 'str'> 
    <class 'int'> 
    <class 'str'> 
    <class 'int'> 
    <class 'int'>
    ______________________________________
    """
    chatter = payload.user
    CHATTER_NAME = normalize_username(chatter.name)
    CHATTER_ID = safe_int(chatter.id)
    TIER = payload.tier if payload.tier else ""
    BROACASTER_ID = safe_int(payload.broadcaster.id)
    BROACASTER_NAME = safe_int(payload.broadcaster.name)
    TOTAL = safe_int(payload.total)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obtener fecha actual
        now = datetime.now()
        year = now.year
        month = now.month

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Verificar si la tabla existe
        cursor.execute('''
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name='subscriptions_gift';
        ''', ())
        table_exists = cursor.fetchone() is not None
        if not table_exists:
            # Crear la tabla si no existe
            cursor.execute(f'''
                CREATE TABLE subscriptions_gift (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT,
                    username TEXT,
                    tier TEXT,
                    total INTEGER,
                    date TEXT,
                    timestamp TEXT
                );
            ''')
            printlog(f"Tabla 'subscriptions_gift' creada correctamente.")
        # Insertar datos
        cursor.execute(f'''
            INSERT INTO subscriptions_gift (user, username, tier, total, date, timestamp)
            VALUES (?, ?, ?, ?, ?, ?);
        ''', (CHATTER_ID, CHATTER_NAME, TIER, TOTAL, now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

        printlog(f"{dorado}{CHATTER_NAME}{white} ha regalado {white}{TOTAL}{dorado} suscripcion{'es' if TOTAL>1 else ''} de Tier {TIER} al canal {channelColor}{BROACASTER_NAME}{resetColor}.")
        user = self.create_partialuser(BROACASTER_ID)
        await user.send_message(sender=self.user, message=f"[BOT] - ¡Gracias por la{'s' if TOTAL>1 else ''} {TOTAL if TOTAL>1 else ''} sub{'s' if TOTAL>1 else ''} @{CHATTER_NAME}! 🎉")
        
        if conn:
            conn.close()


    except sqlite3.Error as e:
        printlog(f"Ha ocurrido un error al guardar al regalador de subs {e}","ERROR")
    finally:
            if conn:
                conn.close()
                cerrar_conexion(conn, cursor)
            await update_global_stats("xp_Fuerza",CHATTER_ID,5)
            await update_global_stats("xp_Carisma",CHATTER_ID,5)
            await update_global_stats("xp_Empatia",CHATTER_ID,5)
            await update_global_stats("Subs_Gifted",CHATTER_ID,TOTAL)