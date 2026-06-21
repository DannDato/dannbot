import sqlite3
import os
from datetime import datetime, timedelta

from Helpers.helpers import normalize_username, db_cursor
from Helpers.printlog import printlog

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')


# ACTUALIZAR ESTADISTICAS DE LA CATEGORIA PARAMETRIZADA
async def update_global_stats(stat_category, user, value):
    """
    Actualiza las estadísticas globales.
    :param stat_category: Categoría de la estadística (ej. 'wordle_wins', 'top_chatter')
    :param user: Nombre del usuario
    :param value: Cantidad a incrementar
    """
    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('''
                SELECT value, hvalue FROM stats_channel
                WHERE category = ? AND user = ?
            ''', (stat_category, user))

            result = cursor.fetchone()

            if result:
                new_value = 0 if result[0] + value < 0 else result[0] + value
                hvalue = result[1] + value
                if stat_category == 'wordle_wins' and new_value >= 5:
                    new_value = 0
                cursor.execute('''
                    UPDATE stats_channel
                    SET value = ?, hvalue = ?
                    WHERE category = ? AND user = ?
                ''', (new_value, hvalue, stat_category, user))
            else:
                new_value = value
                cursor.execute('''
                    INSERT INTO stats_channel (category, user, value, hvalue)
                    VALUES (?, ?, ?, ?)
                ''', (stat_category, user, value, value))

        return new_value

    except sqlite3.Error as e:
        printlog(f"Error al actualizar las estadísticas en la base de datos stats: {e}","ERROR")
        return None
    
#OBTENER ESTADISTICAS DE LA CATEGORIA PARAMETRIZADA
async def get_stats(stat_category,user):
    """
    Obtener las estadísticas de la categoria.
    :param stat_category: Categoría de la estadística (ej. 'wordle_wins', 'top_chatter')
    :param user: id del usuario
    """

    try:
        with db_cursor(DB_PATH) as (_, cursor):
            if user is not None:
                cursor.execute('''
                    SELECT (SELECT username FROM users WHERE twitch_id=user) as username, value, hvalue FROM stats_channel
                    WHERE category = ? AND user = ?
                    GROUP BY username
                ''', (stat_category, user))
                result = cursor.fetchone()
                retorno = result if result else None
            else:
                cursor.execute('''
                    SELECT (SELECT username FROM users WHERE twitch_id=user) as username, value
                    FROM stats_channel
                    WHERE category = ?
                    GROUP BY user
                    ORDER BY value DESC
                    LIMIT 5
                ''', (stat_category,))
                result = cursor.fetchall()
                retorno = ", ".join([f"@{username} ({value})" for username, value in result]) if result else None

        return retorno

    except sqlite3.Error as e:
        printlog(f"Error al obtener las estadísticas de la base de datos: {e}","ERROR")
        return None

async def check_primero(user):
    """
        Verifica y registra de forma atómica el comando !primero para el stream activo.

        Retorna una tupla (status, username):
        - ("won", username): el usuario ganó el primero en este stream
        - ("already_you", username): ese mismo usuario ya era primero
        - ("already_ranked", level): el usuario ya ganó otro nivel (first_user/second_user/third_user)
        - ("already_other", username): otro usuario ya fue primero
        - ("offline", None): no hay stream activo en curso
        - ("error", None): error al consultar/guardar en base de datos
    """
    userid = str(user.id)
    username = normalize_username(getattr(user, "name", "")) or str(user.id)

    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            # Bloqueo de escritura para evitar doble ganador por concurrencia.
            cursor.execute("BEGIN IMMEDIATE")

            # Buscar stream activo (start_stream sin end_stream posterior).
            cursor.execute('''
                SELECT date
                FROM stream_data
                WHERE accion = "start_stream"
                AND NOT EXISTS (
                    SELECT 1
                    FROM stream_data AS subquery
                    WHERE subquery.accion = "end_stream"
                    AND datetime(subquery.date) >= datetime(stream_data.date)
                )
                ORDER BY datetime(date) DESC
                LIMIT 1;
            ''')
            active_stream = cursor.fetchone()
            if not active_stream:
                return "offline", None

            stream_start_date = active_stream[0]

            # Un usuario solo puede ganar un nivel por stream.
            cursor.execute('''
                SELECT accion
                FROM stream_data
                WHERE accion IN ('first_user', 'second_user', 'third_user')
                AND value = ?
                AND datetime(date) >= datetime(?)
                ORDER BY datetime(date) ASC
                LIMIT 1;
            ''', (userid, stream_start_date))
            user_claim = cursor.fetchone()
            if user_claim:
                action = user_claim[0]
                if action == 'first_user':
                    return "already_you", username
                return "already_ranked", action

            # Verificar si ya existe first_user para este stream activo.
            cursor.execute('''
                SELECT
                    value,
                    (SELECT u.username FROM users u WHERE u.twitch_id = stream_data.value) as username
                FROM stream_data
                WHERE accion = 'first_user'
                AND datetime(date) >= datetime(?)
                ORDER BY datetime(date) ASC
                LIMIT 1;
            ''', (stream_start_date,))
            result = cursor.fetchone()

            if result:
                winner_id, winner_username = result
                winner_username = winner_username or str(winner_id)
                if str(winner_id) == userid:
                    return "already_you", winner_username
                return "already_other", winner_username

            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO stream_data (accion, value, date)
                VALUES ('first_user', ?, ?)
            ''', (userid, current_date))
            return "won", username

    except sqlite3.Error as e:
        printlog(f"Error al obtener las estadísticas de la base de datos: {e}","ERROR")
        return "error", None


async def check_segundo(user):
    """
        Verifica y registra de forma atómica el comando !segundo para el stream activo.

        Retorna una tupla (status, username):
        - ("won", username): el usuario ganó el segundo en este stream
        - ("needs_first", first_username): no existe primer lugar aún
        - ("already_you", username): ese mismo usuario ya era segundo
        - ("already_ranked", level): el usuario ya ganó otro nivel (first_user/second_user/third_user)
        - ("already_other", username): otro usuario ya fue segundo
        - ("offline", None): no hay stream activo en curso
        - ("error", None): error al consultar/guardar en base de datos
    """
    userid = str(user.id)
    username = normalize_username(getattr(user, "name", "")) or str(user.id)

    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            # Bloqueo de escritura para evitar doble ganador por concurrencia.
            cursor.execute("BEGIN IMMEDIATE")

            # Buscar stream activo (start_stream sin end_stream posterior).
            cursor.execute('''
                SELECT date
                FROM stream_data
                WHERE accion = "start_stream"
                AND NOT EXISTS (
                    SELECT 1
                    FROM stream_data AS subquery
                    WHERE subquery.accion = "end_stream"
                    AND datetime(subquery.date) >= datetime(stream_data.date)
                )
                ORDER BY datetime(date) DESC
                LIMIT 1;
            ''')
            active_stream = cursor.fetchone()
            if not active_stream:
                return "offline", None

            stream_start_date = active_stream[0]

            # Un usuario solo puede ganar un nivel por stream.
            cursor.execute('''
                SELECT accion
                FROM stream_data
                WHERE accion IN ('first_user', 'second_user', 'third_user')
                AND value = ?
                AND datetime(date) >= datetime(?)
                ORDER BY datetime(date) ASC
                LIMIT 1;
            ''', (userid, stream_start_date))
            user_claim = cursor.fetchone()
            if user_claim:
                action = user_claim[0]
                if action == 'second_user':
                    return "already_you", username
                return "already_ranked", action

            # Regla principal: debe existir first_user en este stream antes de reclamar segundo.
            cursor.execute('''
                SELECT
                    value,
                    (SELECT u.username FROM users u WHERE u.twitch_id = stream_data.value) as username
                FROM stream_data
                WHERE accion = 'first_user'
                AND datetime(date) >= datetime(?)
                ORDER BY datetime(date) ASC
                LIMIT 1;
            ''', (stream_start_date,))
            first_result = cursor.fetchone()
            if not first_result:
                return "needs_first", None

            first_id, first_username = first_result
            first_username = first_username or str(first_id)

            # Verificar si ya existe second_user para este stream activo.
            cursor.execute('''
                SELECT
                    value,
                    (SELECT u.username FROM users u WHERE u.twitch_id = stream_data.value) as username
                FROM stream_data
                WHERE accion = 'second_user'
                AND datetime(date) >= datetime(?)
                ORDER BY datetime(date) ASC
                LIMIT 1;
            ''', (stream_start_date,))
            second_result = cursor.fetchone()

            if second_result:
                winner_id, winner_username = second_result
                winner_username = winner_username or str(winner_id)
                if str(winner_id) == userid:
                    return "already_you", winner_username
                return "already_other", winner_username

            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO stream_data (accion, value, date)
                VALUES ('second_user', ?, ?)
            ''', (userid, current_date))
            return "won", username

    except sqlite3.Error as e:
        printlog(f"Error al obtener las estadísticas de la base de datos: {e}","ERROR")
        return "error", None


async def check_tercero(user):
    """
        Verifica y registra de forma atómica el comando !tercero para el stream activo.

        Retorna una tupla (status, username):
        - ("won", username): el usuario ganó el tercero en este stream
        - ("needs_first", None): no existe primer lugar aún
        - ("needs_second", None): no existe segundo lugar aún
        - ("already_you", username): ese mismo usuario ya era tercero
        - ("already_ranked", level): el usuario ya ganó otro nivel (first_user/second_user/third_user)
        - ("already_other", username): otro usuario ya fue tercero
        - ("offline", None): no hay stream activo en curso
        - ("error", None): error al consultar/guardar en base de datos
    """
    userid = str(user.id)
    username = normalize_username(getattr(user, "name", "")) or str(user.id)

    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute("BEGIN IMMEDIATE")

            cursor.execute('''
                SELECT date
                FROM stream_data
                WHERE accion = "start_stream"
                AND NOT EXISTS (
                    SELECT 1
                    FROM stream_data AS subquery
                    WHERE subquery.accion = "end_stream"
                    AND datetime(subquery.date) >= datetime(stream_data.date)
                )
                ORDER BY datetime(date) DESC
                LIMIT 1;
            ''')
            active_stream = cursor.fetchone()
            if not active_stream:
                return "offline", None

            stream_start_date = active_stream[0]

            # Un usuario solo puede ganar un nivel por stream.
            cursor.execute('''
                SELECT accion
                FROM stream_data
                WHERE accion IN ('first_user', 'second_user', 'third_user')
                AND value = ?
                AND datetime(date) >= datetime(?)
                ORDER BY datetime(date) ASC
                LIMIT 1;
            ''', (userid, stream_start_date))
            user_claim = cursor.fetchone()
            if user_claim:
                action = user_claim[0]
                if action == 'third_user':
                    return "already_you", username
                return "already_ranked", action

            # Debe existir first_user en este stream.
            cursor.execute('''
                SELECT 1
                FROM stream_data
                WHERE accion = 'first_user'
                AND datetime(date) >= datetime(?)
                ORDER BY datetime(date) ASC
                LIMIT 1;
            ''', (stream_start_date,))
            if not cursor.fetchone():
                return "needs_first", None

            # Debe existir second_user en este stream.
            cursor.execute('''
                SELECT 1
                FROM stream_data
                WHERE accion = 'second_user'
                AND datetime(date) >= datetime(?)
                ORDER BY datetime(date) ASC
                LIMIT 1;
            ''', (stream_start_date,))
            if not cursor.fetchone():
                return "needs_second", None

            # Verificar si ya existe third_user para este stream activo.
            cursor.execute('''
                SELECT
                    value,
                    (SELECT u.username FROM users u WHERE u.twitch_id = stream_data.value) as username
                FROM stream_data
                WHERE accion = 'third_user'
                AND datetime(date) >= datetime(?)
                ORDER BY datetime(date) ASC
                LIMIT 1;
            ''', (stream_start_date,))
            third_result = cursor.fetchone()

            if third_result:
                winner_id, winner_username = third_result
                winner_username = winner_username or str(winner_id)
                if str(winner_id) == userid:
                    return "already_you", winner_username
                return "already_other", winner_username

            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO stream_data (accion, value, date)
                VALUES ('third_user', ?, ?)
            ''', (userid, current_date))
            return "won", username

    except sqlite3.Error as e:
        printlog(f"Error al obtener las estadísticas de la base de datos: {e}","ERROR")
        return "error", None
        
async def get_top_chatter_day():
    """
    Estadistica de top chatter del día
        -Asignar punto de top_chatter_dia
        ...
    """
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now()
        year = now.year
        month = now.month
        table_name = f"chat_{year}{month:02}"

        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute(f'''
                SELECT user, count(user) AS nMsg from {table_name} 
                WHERE date like ?
                GROUP BY user
                order by 2 DESC
                LIMIT 1
            ''', (f"%{current_date}%",))

            result = cursor.fetchone()
            if not result:
                printlog("Ha ocurrido un error al obtener al top_chatter_day","ERROR")
                return None

            usuario = result[0]
            cursor.execute('''
                INSERT INTO stream_data (accion,value,date)
                VALUES("top_chatter",?,?)
            ''', (usuario, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            return usuario

    except sqlite3.Error as e:
        printlog(f"Error al obtener top_chatter: {e}","ERROR")
        return None
    
async def count_user_messages(username, start_date=0, end_date=0):
    """
    Cuenta todos los mensajes enviados por un usuario en todas las tablas de chat.
    Si no se proporcionan fechas, cuenta el total histórico.

    :param username: Nombre del usuario.
    :param start_date: Fecha de inicio (formato 'YYYY-MM-DD HH:MM:SS'). Usa 0 para no filtrar por fecha.
    :param end_date: Fecha de fin (formato 'YYYY-MM-DD HH:MM:SS'). Usa 0 para no filtrar por fecha.
    :return: Número total de mensajes enviados por el usuario en el rango de fechas o en total.
    """
    total_messages = 0

    try:
        with db_cursor(DB_PATH) as (_, cursor):
            cursor.execute('''
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name LIKE 'chat_%';
            ''')
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                if start_date == 0 and end_date == 0:
                    cursor.execute(f'''
                        SELECT COUNT(*) 
                        FROM {table_name} 
                        WHERE user = ?;
                    ''', (username,))
                else:
                    cursor.execute(f'''
                        SELECT COUNT(*) 
                        FROM {table_name} 
                        WHERE user = ? 
                        AND datetime(timestamp) BETWEEN datetime(?) AND datetime(?);
                    ''', (username, start_date, end_date))

                total_messages += cursor.fetchone()[0]

        return total_messages

    except sqlite3.Error as e:
        printlog(f"Error al contar mensajes: {e}","ERROR")
        return -1  # Indica un error

async def save_user_bd(bd, user):
    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('''
                SELECT birthday FROM users WHERE twitch_id=?
            ''', (user,))
            result = cursor.fetchone()
            if not result:
                printlog("No se ha encontrado el usuario","ERROR")
                return False

            cursor.execute('''
                UPDATE users SET birthday=? WHERE twitch_id=?
            ''', (bd, user))
            return True
        
    except sqlite3.Error as e:
        printlog(f"Error al acceder a guardar cumpleaños: {e}","ERROR")
        return False

async def get_user_bd(user):
    try:
        current_date = datetime.now()
        current_year = current_date.year
        with db_cursor(DB_PATH) as (_, cursor):
            cursor.execute('''
                SELECT birthday FROM users WHERE twitch_id=?
            ''', (user,))
            result = cursor.fetchone()

        if result is not None:
            bd = result[0]
            if bd is None:
                return False, '0', '0', '0', '0'
            bd_date = datetime.strptime(bd, "%Y-%m-%d")  # Convertir a objeto datetime
            lcMes = bd_date.strftime("%B").capitalize()
            bd_month, bd_day = bd_date.month, bd_date.day  # Extraer mes y día
            # Crear la fecha del cumpleaños en el año actual
            next_birthday = datetime(current_year, bd_month, bd_day)
            # Si el cumpleaños ya pasó este año, calcular para el siguiente
            if next_birthday < current_date:
                next_birthday = datetime(current_year + 1, bd_month, bd_day)
            # Calcular cuántos días faltan
            lDays = (next_birthday - current_date).days +1
            return True, bd, lDays, lcMes, bd_day
        else:
            return False, '0', '0', '0', '0'
        
    except sqlite3.Error as e:
        printlog(f"Error al consultar cumpleaños: {e}","ERROR")
        return False, '0', '0', '0', '0'


async def today_birthdays():
    try:
        current_date = datetime.now()
        current_month_day = current_date.strftime('%m-%d')  # Formato MM-DD para la comparación

        with db_cursor(DB_PATH) as (_, cursor):
            cursor.execute('''
                SELECT username, birthday FROM users
                WHERE strftime('%m-%d', birthday) = ?
            ''', (current_month_day,))
            result = cursor.fetchall()

        if result:  # Si hay resultados
            users_with_birthday = [user for user, _ in result]
            return True, users_with_birthday
        else:
            return False, []
        
    except sqlite3.Error as e:
        printlog(f"Error al consultar cumpleaños de hoy: {e}","ERROR")
        return False


async def week_birthdays():
    try:
        today = datetime.now().date()
        week_days = [today + timedelta(days=offset) for offset in range(1, 8)]
        week_days_mmdd = {d.strftime('%m-%d') for d in week_days}

        with db_cursor(DB_PATH) as (_, cursor):
            placeholders = ','.join('?' for _ in week_days_mmdd)
            cursor.execute(f'''
                SELECT username, birthday 
                FROM users
                WHERE strftime('%m-%d', birthday) IN ({placeholders});
            ''', tuple(week_days_mmdd))
            result = cursor.fetchall()

        if result:  # Si hay resultados
            weekday_names = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
            users_with_birthday = []

            for username, birthday in result:
                if not birthday:
                    continue

                bd_date = datetime.strptime(birthday, '%Y-%m-%d').date()
                birthday_this_year = bd_date.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                delta_days = (birthday_this_year - today).days
                if delta_days < 1 or delta_days > 7:
                    continue

                if delta_days == 1:
                    day_label = 'Mañana'
                elif delta_days == 2:
                    day_label = 'Pasado mañana'
                else:
                    day_label = f"el {weekday_names[birthday_this_year.weekday()]}"
                users_with_birthday.append((delta_days, username, day_label))

            if users_with_birthday:
                users_with_birthday.sort(key=lambda item: (item[0], item[1].lower()))
                formatted_birthdays = [(username, day_label) for _, username, day_label in users_with_birthday]
                return True, formatted_birthdays
            return False, []
        else:
            return False, []
        
    except sqlite3.Error as e:
        printlog(f"Error al consultar cumpleaños de la semana: {e}","ERROR")
        return False
    except ValueError as e:
        printlog(f"Error al procesar fecha de cumpleaños semanal: {e}","ERROR")
        return False, []

async def get_twitch_id(username):
    try:
        username = normalize_username(username)
        with db_cursor(DB_PATH) as (_, cursor):
            cursor.execute('''
                SELECT twitch_id FROM users WHERE username=?
            ''',(username,))
            result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except sqlite3.Error as e:
        printlog(f"Error al obtener el id del usuario: {e}","ERROR")
        return None
