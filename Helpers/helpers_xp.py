import sqlite3
import os
import math
from math import log, sqrt
from datetime import datetime

from Helpers.helpers import normalize_username, cerrar_conexion, safe_int
from Helpers.helpers_stats import update_global_stats, count_user_messages, get_stats
from Helpers.roles import role_rules, complemento_roles, role_emojis
from Helpers.printlog import printlog

#Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

# Regresa las estadisticas RPG del usuario
async def get_player(user):
    """
    Obtiene las estadísticas completas RPG del usuario.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Consulta para obtener las categorías relacionadas con XP ordenadas por valor
        cursor.execute('''
            SELECT REPLACE(category,'xp_','') as category, value
            FROM stats_channel
            WHERE user=? AND category LIKE '%xp_%'
            ORDER BY value DESC
        ''', (user,))
        result = cursor.fetchall()
        if result:
            limiteC = 6
            xp_total = 0
            Player = []
            # Procesar cada categoría para calcular XP y formar el arreglo Player
            for category, value in result:
                lcEmoji = role_emojis.get(category, '🔥')
                Player.append([category, f"{value:.2f}"])
                xp_total += float(value)

            # XP final multiplicado por 100
            xp_total *= 100
            # Calcular nivel usando una función externa
            nivel = await calculate_level(user)
            # Ordenar Player por las mejores categorías (ya ordenado por la consulta SQL)
            Player.sort(key=lambda x: float(x[1]), reverse=True)
            # Determinar el rol (pendiente de ajustar en get_rol)
            if len(Player) >= 3 and Player[0][1] == Player[1][1] == Player[2][1]:
                lcRol = "Comandante supremo"
            else:
                lcRol = await get_rol(Player[0][0], Player[1][0], Player[2][0])

            Player[0][0]=f"{Player[0][0]}{role_emojis.get(Player[0][0], '🔥')}"
            Player[1][0]=f"{Player[1][0]}{role_emojis.get(Player[1][0], '🔥')}"
            Player[2][0]=f"{Player[2][0]}{role_emojis.get(Player[2][0], '🔥')}"

            # Insertar XP, Nivel y Rol al inicio de Player
            Player.insert(0, ["Rol", lcRol])
            Player.insert(0, ["Nivel", str(nivel)[:limiteC]])
            Player.insert(0, ["XP", f"{xp_total:.2f}"])

            """
                Muestra el nivel de los jugadores segun sus estadísticas rpg
                oPlayer[0][1] = XP
                oPlayer[1][1] = Nivel
                oPlayer[2][1] = Rol
                oPlayer[3][1] = xp_categoria
                oPlayer[4][1] = xp_categoria
                ...
                oPlayer[X][1] = xp_categoria
            """
            conn.rollback()
            conn.close()
            return Player
        else:
            return False

    except sqlite3.Error as e:
        print(f"Error en la base de datos: {e}")
        return False
    finally:
        if conn:
            conn.close()
            cerrar_conexion(conn, cursor)
    
async def update_xp():
    """
    Calcula las estadísticas de los usuarios basadas en los datos del último stream.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obtener las fechas de inicio y fin del último stream
        cursor.execute('''
            SELECT date
            FROM stream_data
            WHERE accion = "start_stream"
            ORDER BY date DESC
            LIMIT 1;
        ''')
        start_stream = cursor.fetchone()

        cursor.execute('''
            SELECT date
            FROM stream_data
            WHERE accion = "end_stream"
            ORDER BY date DESC
            LIMIT 1;
        ''')
        end_stream = cursor.fetchone()

        if not start_stream or not end_stream:
            printlog("No hay un stream iniciado o finalizado para calcular las estadísticas.","WARNING")
            return False

        start_date = datetime.strptime(start_stream[0], '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(end_stream[0], '%Y-%m-%d %H:%M:%S')

        printlog(f"Procesando datos entre {start_date} y {end_date}...")

        # Obtener los usuarios únicos en ese rango
        cursor.execute('''
            SELECT DISTINCT (SELECT username FROM users WHERE twitch_id=history_users.user) AS username,
            user
            FROM history_users
            WHERE datetime(date) BETWEEN ? AND ?;
        ''', (start_date, end_date))
        users = cursor.fetchall()

        for row in users:
            username = row[0]
            user = row[1]
            printlog(f'\033[1;33m  Actualizando a: \033[0m: {username}')
            # Obtener hora de entrada del usuario
            cursor.execute('''
                SELECT MIN(date)
                FROM history_users
                WHERE user = ? AND datetime(date) BETWEEN ? AND ?;
            ''', (user, start_date, end_date))
            result = cursor.fetchone()
            hEntrada = result[0] if result and result[0] else None

            # Obtener hora del último mensaje del usuario
            now = datetime.now()
            year, month = now.year, now.month
            table_name = f"chat_{year}{month:02}"

            cursor.execute(f'''
                SELECT MAX(timestamp)
                FROM {table_name}
                WHERE user = ? AND datetime(timestamp) BETWEEN ? AND ?;
            ''', (user, start_date, end_date))
            result = cursor.fetchone()
            LastMsg = result[0] if result and result[0] else None

            # Obtener número de ingresos del usuario
            cursor.execute('''
                SELECT COUNT(date)
                FROM history_users
                WHERE user = ? AND datetime(date) BETWEEN ? AND ?;
            ''', (user, start_date, end_date))
            result = cursor.fetchone()
            nEntradas = result[0] if result and result[0] else 0

            # Obtener número de mensajes del usuario
            nMensajes = await count_user_messages(user, start_date, end_date)

            # Obtener número de caracteres enviados
            cursor.execute(f'''
                SELECT SUM(LENGTH(message))
                FROM {table_name}
                WHERE user = ? AND datetime(timestamp) BETWEEN ? AND ?;
            ''', (user, start_date, end_date))
            result = cursor.fetchone()
            nCaracteres = result[0] if result and result[0] else 0

            # Calcular estadísticas si hay datos de entrada y mensajes
            if hEntrada and LastMsg:
                try:
                    hEntrada = datetime.strptime(hEntrada, '%Y-%m-%d %H:%M:%S')
                    LastMsg = datetime.strptime(LastMsg, '%Y-%m-%d %H:%M:%S')

                    if LastMsg<hEntrada:
                        hEntrada=LastMsg
                    time_difference = (LastMsg - hEntrada).total_seconds() / 60

                    if nMensajes > 0:
                        Resistencia = (time_difference / 1000) * log(nMensajes + 1, 10)
                        Habilidad = sqrt((nCaracteres / 10) / nMensajes)
                        Fuerza = log((nEntradas + 1) * ((nMensajes / 20) + 1), 10)

                        await update_global_stats("xp_Resistencia", user, Resistencia)
                        await update_global_stats("xp_Habilidad", user, Habilidad)
                        await update_global_stats("xp_Fuerza", user, Fuerza)

                except ValueError as e:
                    printlog(f"Error al procesar las fechas: {e}","ERROR")

        conn.commit()
        conn.close()
        printlog("Actualización de estadísticas endstream completada.")
        return True

    except sqlite3.Error as e:
        printlog(f"Error en la base de datos: {e}","ERROR")
        if conn:
            conn.rollback()
            conn.close()
        return False


async def calculate_xp(user):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Consulta para obtener las categorías relacionadas con XP ordenadas por valor
        cursor.execute('''
            SELECT REPLACE(category,'xp_','') AS category, value
            FROM stats_channel
            WHERE user=? AND category LIKE '%xp_%'
            ORDER BY value DESC
        ''', (user,))
        result = cursor.fetchall()

        if result:
            xp_total = 0
            # Procesar cada categoría para calcular XP y formar el arreglo Player
            for category, value in result:
                xp_total += float(value)
            # XP final multiplicado por 10
            xp_total *= 10
            xp_total = float(f"{xp_total:.2f}")
            return xp_total
        else:
            xp_total=0
            return xp_total

            # XP final multiplicado por 100
    except sqlite3.Error as e:
        print(f"Error en la base de datos: {e}")
        return False

    finally:
        if conn:
            conn.close()


#Calcular nivel en base al XP
async def calculate_level(user):
    """
    Calcula el nivel del jugador basado en el XP, con una progresión lineal ajustada 
    :param xp: XP total del jugador.
    :return: Nivel calculado.
    """
    xp = await calculate_xp(user)
    xp=int(xp)
    level = 1
    xp_required = 5000  # XP necesario para el primer nivel
    increment = 1000   # Incremento para el siguiente nivel
    # Itera hasta que el XP sea suficiente para el nivel actual
    while xp >= xp_required:
        level += 1
        xp_required += (level*increment)  # Aumentamos el XP necesario para el siguiente nivel
    return level


    
async def get_top_players():
    """
    OBTENER EL TOP 5 JUGADORES CON MEJOR XP
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            SELECT IFNULL((SELECT username FROM users WHERE twitch_id=user),'None') as username, SUM(value) AS total_xp
            FROM stats_channel
            WHERE (user!='channel' AND user!='439400816') AND category LIKE '%xp_%'
            GROUP BY user
            ORDER BY total_xp DESC
            LIMIT 3
        ''',)
        result = cursor.fetchall()
        top=""
        lntop=1
        if result and result[0][0] is not None:
            for row in result:
                user = row[0]
                nXp = await calculate_xp(user)

                lcEmoji = "🥇" if lntop == 1 else "🥈" if lntop == 2 else "🥉"
                top += f" {lcEmoji}-@{row[0]} XP({nXp})\n "
                lntop += 1

            conn.rollback()
            conn.close()
            cerrar_conexion(conn, cursor)
            return top
        else:
            cerrar_conexion(conn, cursor)
            return False
        
    except sqlite3.Error as e:
        printlog(f"Error al finalizar directo: {e}","ERROR")
        if conn:
            conn.rollback()
            conn.close()
            cerrar_conexion(conn, cursor)
        return False
    
async def get_rol(h1, h2, h3):
    """
    Determina el rol principal y el complemento basado en las tres habilidades más destacadas.
    """
    
    # Ordenar las habilidades en pares (sin importar el orden)
    skills = (h1, h2)

    # Buscar el rol principal en las reglas
    lcRol = role_rules.get(skills, "Aventurero")
    # Obtener el rol complementario según la tercera habilidad
    lcRolComplemento = complemento_roles.get(h3, "Inicial")

    # Resultado final
    lcTitulo = f"{lcRol.lower()} {lcRolComplemento} "
    return lcTitulo

async def set_stats(stat_category, user, value):
    """
    Actualiza las estadísticas globales.
    :param stat_category: Categoría de la estadística (ej. 'wordle_wins', 'top_chatter')
    :param user: Nombre del usuario
    :param value: Cantidad a incrementar
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Normalizar el nombre de usuario
        user = normalize_username(user)

        # Verificar si el usuario ya tiene un valor para esta categoría
        cursor.execute('''
            SELECT value, hvalue FROM stats_channel
            WHERE category = ? AND user = ?
        ''', (stat_category, user))

        result = cursor.fetchone()

        if result:
            # Si el usuario ya tiene una estadística, actualizar el valor
            new_value = value
            hvalue = value

            cursor.execute('''
                UPDATE stats_channel
                SET value = ?, hvalue = ?
                WHERE category = ? AND user = ?
            ''', (new_value, hvalue, stat_category, user))
        else:
            # Si no existe, insertar un nuevo registro
            new_value=value
            cursor.execute('''
                INSERT INTO stats_channel (category, user, value, hvalue)
                VALUES (?, ?, ?, ?)
            ''', (stat_category, user, value, value))
            

        # Confirmar los cambios y cerrar la conexión
        conn.commit()
        conn.close()
        cerrar_conexion(conn, cursor)
        # printlog(f"Estadísticas actualizadas: {stat_category} | {user}: {value}")
        return new_value

    except sqlite3.Error as e:
        printlog(f"Error al actualizar las estadísticas en la base de datos stats: {e}","ERROR")
        if conn:
            conn.rollback()
            conn.close()
            cerrar_conexion(conn, cursor)  
        return None
    
async def get_clan_user(user):
    """
    Obtiene el clan actual del usuario.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        user = normalize_username(user)

        # Consulta para obtener el clan del usuario
        cursor.execute('''
            SELECT clan,lider
            FROM clanes
            WHERE user = ?
        ''', (user,))
        result = cursor.fetchone()
        cerrar_conexion(conn, cursor)
        if result:
            if result[1]=='1':
                return f"es lider del clan '{result[0]}'"
            else:
                return f"pertenece al clan '{result[0]}'"
        else:
            return "No pertenece a ningún clan."

    except sqlite3.Error as e:
        printlog(f"Error al obtener el clan del usuario: {e}","ERROR")
        return None

    finally:
        if conn:
            conn.close()
            cerrar_conexion(conn, cursor)

async def admin_clan(user,clan,accion):
    """
    Crea o elimina un clan.
    :param user: Nombre del usuario.
    :param clan: Nombre del clan.
    :param accion: Acción a realizar.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        user = normalize_username(user)

        # Consulta para verificar si el usuario ya es líder de un clan
        cursor.execute('''
            SELECT clan
            FROM clanes
            WHERE user = ? AND lider = 1
        ''', (user,))
        result = cursor.fetchone()

        if accion == 1:
            if result:
                # Si el usuario ya es líder de un clan, no puede crear otro
                return False
            # Crear un nuevo clan
            cursor.execute('''
                INSERT INTO clanes (clan, user, lider)
                VALUES (?, ?, 1)
            ''', (clan, user))
            conn.commit()
            cerrar_conexion(conn, cursor)
            return True

        elif accion == 2:
            # Eliminar un clan
            if result: #verifica si es lider
                cursor.execute('''
                DELETE FROM clanes
                WHERE clan = ? AND user = ? AND lider = 1
                ''', (clan, user))
                conn.commit()
                cerrar_conexion(conn, cursor)
                return True

    except sqlite3.Error as e:
        printlog(f"Error al administrar el clan: {e}","ERROR")
        if conn:
            conn.rollback()
            conn.close()
            cerrar_conexion(conn, cursor)
        return None
    
async def join_to_clan(admin,user):
    """
    Añade un usuario a un clan.
    :param admin: Nombre del usuario administrador.
    :param user: Nombre del usuario a añadir.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        admin = normalize_username(admin)
        user = normalize_username(user)

        # Consulta para verificar si el usuario es líder de un clan
        cursor.execute('''
            SELECT clan
            FROM clanes
            WHERE user = ? AND lider = 1
        ''', (admin,))
        result = cursor.fetchone()

        if result:
            # Añadir al usuario al clan
            cursor.execute('''
                INSERT INTO clanes (clan, user, lider)
                VALUES (?, ?, 0)
            ''', (result[0], user))
            conn.commit()
            cerrar_conexion(conn, cursor)
            return True
        else:
            cerrar_conexion(conn, cursor)
            return False

    except sqlite3.Error as e:
        printlog(f"Error al añadir al usuario al clan: {e}","ERROR")
        if conn:
            conn.rollback()
            conn.close()
            cerrar_conexion(conn, cursor)
        return None
    
async def left_clan(user):
    """
    Abandona un clan.
    :param user: Nombre del usuario.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        user = normalize_username(user)
        # Consulta para verificar si el usuario es líder de un clan
        cursor.execute('''
            SELECT clan
            FROM clanes
            WHERE user = ? AND lider = 1
        ''', (user,))
        result = cursor.fetchone()

        if result:
            # Abandonar el clan
            cursor.execute('''
                DELETE FROM clanes
                WHERE clan = ?
            ''', (result[0],))
            
        # Abandonar el clan
        cursor.execute('''
            DELETE FROM clanes
            WHERE user = ?
        ''', (user,))
        conn.commit()
        cerrar_conexion(conn, cursor)
        return True

    except sqlite3.Error as e:
        printlog(f"Error al abandonar el clan: {e}","ERROR")
        if conn:
            conn.rollback()
            conn.close()
            cerrar_conexion(conn, cursor)
        return None
    
async def get_clanes():
    """
    Obtiene la lista de clanes.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT clan, COUNT(user) AS miembros
            FROM clanes
            GROUP BY clan
            ORDER BY miembros DESC
        ''')
        result = cursor.fetchall()
        clanes = [row[0] for row in result]
        cerrar_conexion(conn, cursor)
        return clanes

    except sqlite3.Error as e:
        printlog(f"Error al obtener la lista de clanes: {e}","ERROR")
        return None

    finally:
        if conn:
            conn.close()
            cerrar_conexion(conn, cursor)

async def get_clan_members(clan):
    """
    Obtiene la lista de miembros de un clan.
    :param clan: Nombre del clan.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user
            FROM clanes
            WHERE clan = ?
        ''', (clan,))
        result = cursor.fetchall()

        members = [row[0] for row in result]
        cerrar_conexion(conn, cursor)
        
        if members:
            return members
        else:
            return "Sin miembros / Clan inexistente."

    except sqlite3.Error as e:
        printlog(f"Error al obtener la lista de miembros del clan: {e}","ERROR")
        return None

    finally:
        if conn:
            conn.close()
            cerrar_conexion(conn, cursor)