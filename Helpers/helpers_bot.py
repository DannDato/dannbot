import random
import sqlite3
import os
from datetime import datetime
import logging
import emoji


from Helpers.helpers import normalize_username, clean_text, cerrar_conexion
from Helpers.helpers_stats import update_global_stats
from Helpers.helpers_dynamic import gen_response

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

#Función anidada en el event listener JOIN
async def user_joined(username):
    if username not in ('streamelements','nightbot','danndato'): #Exclusión de bots externos
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Conectar a la base de datos (si no existe, se creará automáticamente)
        try:
            await count_user_joined(username)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Insertar el nuevo registro en la tabla
            cursor.execute('''INSERT INTO history_users (username, date)VALUES (?, ?)''', (username, timestamp))
            # Confirmar los cambios y cerrar la conexión
            conn.commit()
            conn.close()
            cerrar_conexion(conn, cursor)
            logging.info(f'\033[1;35m{username} se ha unido\033[0m')

        except sqlite3.Error as e:
            logging.info(f'{username} se ha unido')
            logging.error(f"Error al insertar el usuario en la base de datos: {e}")
            if conn:
                conn.rollback()
                conn.close()
                cerrar_conexion(conn, cursor)
        

async def read_save_chat(message):
    if message.author:
        """
        Gestiona la tabla de chat del mes actual en la base de datos.
        Crea la tabla si no existe e inserta los datos proporcionados.

        :param db_path: Ruta a la base de datos SQLite.
        :param username: Nombre de usuario.
        :param message: Mensaje del usuario.
        """
        try:
            username = normalize_username(message.author.name)
            message = clean_text(message.content)
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
                        username TEXT,
                        message TEXT,
                        date TEXT,
                        timestamp TEXT
                    );
                ''')
                logging.info(f"Tabla '{table_name}' creada correctamente.")

            # Insertar datos
            cursor.execute(f'''
                INSERT INTO {table_name} (username, message, date, timestamp)
                VALUES (?, ?, ?, ?);
            ''', (username, message, now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()

            if conn:
                conn.close()

            await update_stream_data("total_messages",1)

            logging.info(f'\033[1;33m{username}\033[0m:\033[94m {message} \033[0m')
            
        except sqlite3.Error as e:
            logging.error(f"Error al gestionar la tabla de chat: {e}")
        finally:
            if conn:
                conn.close()
            await update_global_stats("xp_Habilidad",username,0.15)
            await update_global_stats("xp_Carisma",username,0.15)
  

async def update_stream_data(stat_category, value):

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        current_date = datetime.now().strftime('%Y-%m-%d')
        # Verificar si hay un stream iniciado y no cerrado
        cursor.execute('''
            SELECT date 
            FROM stream_data
            WHERE accion = "start_stream"
            AND NOT EXISTS (
                SELECT 1
                FROM stream_data AS subquery
                WHERE subquery.accion = "end_stream"
                AND subquery.date >= stream_data.date
            )
            ORDER BY date ASC
            LIMIT 1;
        ''')
        result = cursor.fetchone()
        if result:
            # Verificar si el usuario ya tiene un valor para esta categoría
            cursor.execute(f'''
                SELECT value FROM stream_data
                WHERE accion = "{stat_category}" AND DATETIME(date)>= DATETIME('{result[0]}')
            ''',)

            result = cursor.fetchone()

            if result:
                # Si el usuario ya tiene una estadística, actualizar el valor
                hvalue = int(result[0]) + value
                cursor.execute(f'''
                    UPDATE stream_data
                    SET value = ?
                    WHERE accion = ? AND date like '%{current_date}%'
                ''', (hvalue, stat_category))
            else:
                # Si no existe, insertar un nuevo registro
                current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO stream_data (accion, value, date)
                    VALUES (?, ?, ?)
                ''', (stat_category, value, current_date))
                

            # Confirmar los cambios y cerrar la conexión
            conn.commit()
            conn.close()
            return True

    except sqlite3.Error as e:
        logging.error(f"Error al registrar conteo de mensajes del stream en la base de datos: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None
    
async def count_user_joined(user):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Verificar si hay un stream iniciado y no cerrado
        cursor.execute('''
            SELECT date 
            FROM stream_data    
            WHERE accion = "start_stream"
            AND NOT EXISTS (
                SELECT 1
                FROM stream_data AS subquery
                WHERE subquery.accion = "end_stream"
                AND subquery.date >= stream_data.date
            )
            ORDER BY date ASC
            LIMIT 1;
        ''')
        result = cursor.fetchone()
        # return
        if result:
            # Verificar si el usuario ya tiene un valor para esta categoría
            cursor.execute(f'''
                SELECT username FROM history_users
                WHERE DATETIME(date)>= DATETIME('{result[0]}')
                AND username=?
            ''',(user,))

            result = cursor.fetchone()
            if result:
                # Confirmar los cambios y cerrar la conexión
                conn.commit()
                conn.close()
                return False
                
            else:
                await update_stream_data("total_users",1)
                

            # Confirmar los cambios y cerrar la conexión
            conn.commit()
            conn.close()
            return True

    except sqlite3.Error as e:
        logging.error(f"Error al registrar conteo de Usuarios del stream en la base de datos: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None
    
def deEmojify(text):
    return emoji.get_emoji_regexp().sub(r'', text.decode('utf8'))
