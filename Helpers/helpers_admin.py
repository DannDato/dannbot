import sqlite3
import os
from datetime import datetime


from Helpers.helpers_stats import update_global_stats, get_top_chatter_day
from Helpers.helpers_xp import update_xp
from Helpers.helpers_bot import update_stream_data
from Helpers.mailer import enviar_correo
from Helpers.helpers import safe_int, cerrar_conexion
from Helpers.printlog import printlog

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

# ACTUALIZAR ESTADISTICAS DE LA CATEGORIA PARAMETRIZADA
async def end_stream():
    """
    Finaliza un stream si está iniciado y no se ha cerrado.
    
    :param db_path: Ruta a la base de datos SQLite.
    :return: True si se finalizó el stream, False en caso contrario.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

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
            start_date = result[0]
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            dollar = 18.75
            cursor.execute(
                '''
                SELECT 
                    COALESCE(MAX(CASE WHEN accion = "new_bits" THEN value END), 0) AS bits,
                    COALESCE(MAX(CASE WHEN accion = "new_subs" THEN value END), 0) AS subs
                FROM stream_data
                WHERE DATE(date) = DATE(?)
                ''',
                (current_date,)
            )
            bits, subs = cursor.fetchone()
            mSubs = (safe_int(subs)*1.52) * dollar
            mBits = (safe_int(bits)/100) * dollar

            total_money = safe_int(mSubs+mBits)

            # Insertar el registro de finalización
            cursor.execute('''
                INSERT INTO stream_data (accion, value, date)
                VALUES ("total_money", ?, ?),("end_stream", "channel", ?);
            ''', (total_money,current_date,current_date))
            conn.commit()       

            # Módulos de finalización
            top_chatter_day = await get_top_chatter_day()
            if top_chatter_day is not None:
                await update_global_stats("xp_Fuerza",top_chatter_day,3)
                await update_global_stats("top_chatter_day", top_chatter_day, 1)

            await update_xp()
            await end_mail()
            printlog(f"Stream finalizado correctamente: {current_date}.")
            cerrar_conexion(conn, cursor)
            return True
        else:
            printlog("No se encontró ningún stream iniciado y sin cerrar.","WARNING")
            cerrar_conexion(conn, cursor)
            return False

    except sqlite3.Error as e:
        printlog(f"Error en la base de datos: {e}","ERROR")
        return False

    finally:
        if conn:
            conn.close()
            cerrar_conexion(conn, cursor)

    
async def start_stream():
    """
    Inicia un nuevo stream si no hay uno iniciado o si el último stream fue terminado.
    
    :param db_path: Ruta a la base de datos SQLite.
    :return: True si se inició el stream, False en caso contrario.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

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
            ORDER BY date DESC
            LIMIT 1;
        ''')
        result = cursor.fetchone()

        if result:
            printlog("Ya hay un stream iniciado y sin cerrar.","WARNING")
            return False

        # Verificar si el último stream finalizó correctamente
        cursor.execute('''
            SELECT date
            FROM stream_data
            WHERE accion = "end_stream"
            ORDER BY date DESC
            LIMIT 1;
        ''')
        result_end = cursor.fetchone()

        if result_end:
            last_end_date = result_end[0]
            printlog(f"Último stream finalizado correctamente el {last_end_date}.")
        else:
            printlog("No se encontró ningún stream finalizado anteriormente.","WARNING")

        # Insertar el registro de inicio del nuevo stream
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO stream_data (accion, value, date)
            VALUES ("start_stream", "channel", ?),("new_followers", "0", ?);
        ''', (current_date,current_date))
        conn.commit()
        
        await update_stream_data("total_users",1)
        await update_stream_data("total_messages",1)
        printlog(f"Nuevo stream iniciado correctamente a las {current_date}.")
        cerrar_conexion(conn, cursor)
        return True

    except sqlite3.Error as e:
        printlog(f"Error en la base de datos: {e}","ERROR")
        cerrar_conexion(conn, cursor)
        return False

    finally:
        if conn:
            conn.close()
            cerrar_conexion(conn, cursor)
    
async def end_mail():
    """Lee el contenido de un archivo HTML y lo devuelve como texto"""
    HTML_PATH = os.path.join(os.path.dirname(__file__), '..', 'Html', 'mails', 'end_stream.html')
    printlog("Generando reporte de stream...")
    with open(HTML_PATH, "r", encoding="utf-8") as archivo:
        contenido_html = archivo.read()
        printlog("Leyendo HTML de reporte")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        printlog("Iniciando lectura de base de datos")
        # Verificar si hay un stream iniciado y no cerrado
        cursor.execute('''
            WITH StreamPeriods AS (
            SELECT start.id AS start_id,
                start.date AS start_date,
                end_.id AS end_id,
                end_.date AS end_date,
                ROW_NUMBER() OVER (ORDER BY start.date DESC) AS stream_number
            FROM stream_data start
            JOIN stream_data end_
            ON start.accion = 'start_stream'
            AND end_.accion = 'end_stream'
            AND end_.date > start.date
            WHERE NOT EXISTS (
                SELECT 1 FROM stream_data e
                WHERE e.accion = 'end_stream'
                AND e.date > start.date AND e.date < end_.date
            )
            ORDER BY start.date DESC
            LIMIT 3
        )
        SELECT s.id, s.accion, s.value, s.date, sp.stream_number
        FROM stream_data s
        JOIN StreamPeriods sp
        ON s.date BETWEEN sp.start_date AND sp.end_date
        ORDER BY sp.stream_number, s.date;
        ''')
        result = cursor.fetchall()
        printlog("Datos obtenidos en cursor")
        # Estructura para almacenar los datos
        streams = {}

        # Procesar los resultados
        printlog("Recoriendo DATA del cursor")
        for row in result:
            id, accion, value, date, stream_number = row
            # Si el stream no está en el diccionario, inicializarlo
            if stream_number not in streams:
                streams[stream_number] = {}
            # Si la acción no está en el stream, inicializarla
            if accion not in streams[stream_number]:
                # Almacenar como lista si hay múltiples valores (ej: mensajes)
                if accion in ["first_user", "total_messages", "total_users", "top_chatter","new_bits","new_subs","total_money","new_followers"]:
                    streams[stream_number][accion] = []
                else:
                    streams[stream_number][accion] = {}

            # Guardar el valor correctamente
            if isinstance(streams[stream_number][accion], list):
                streams[stream_number][accion].append(value)
            else:
                streams[stream_number][accion] = {"id": id, "value": value, "date": date}

        printlog("Asignando variables del Stream mas reciente")
        # Stream más reciente (1)
        start_time_1 = streams[1]["start_stream"]["date"]
        end_time_1 = streams[1]["end_stream"]["date"]
        first_user_1 = streams[1]["first_user"][0] if "first_user" in streams[1] else None
        top_chatter_1 = streams[1]["top_chatter"][0] if "top_chatter" in streams[1] else None
        total_messages_1 = streams[1]["total_messages"][0] if "total_messages" in streams[1] else None
        total_users_1 = streams[1]["total_users"][0] if "total_users" in streams[1] else None
        total_follows = streams[1]["new_followers"][0] if "new_followers" in streams[1] else None
        new_bits = streams[1]["new_bits"][0] if "new_bits" in streams[1] else None
        new_subs = streams[1]["new_subs"][0] if "new_subs" in streams[1] else None
        total_money = streams[1]["total_money"][0] if "total_money" in streams[1] else None
        

        # Stream segundo más reciente (2)
        printlog("Asignacion de variables del stream anterior")
        total_messages_2 = streams[2]["total_messages"][0] if "total_messages" in streams[2] else None
        total_users_2 = streams[2]["total_users"][0] if "total_users" in streams[2] else None

        # Stream tercer más reciente (3)
        printlog("Asignacion de variables del stream previo al anterior")
        total_messages_3 = streams[3]["total_messages"][0] if "total_messages" in streams[3] else None
        total_users_3 = streams[3]["total_users"][0] if "total_users" in streams[3] else None

        incremento_users = safe_int(total_users_1) - safe_int(total_users_2)
        pViwers=(incremento_users/safe_int(total_users_2))*100
        if safe_int(pViwers)>0:
            contenido_html =contenido_html.replace('var(--pViewers-color)','var(--main-color)')
        elif safe_int(pViwers)==0:
            contenido_html =contenido_html.replace('var(--pViewers-color)','var(--third-color)')
        elif safe_int(pViwers)<0:
            contenido_html =contenido_html.replace('var(--pViewers-color)','var(--second-color)')
        else:
            contenido_html =contenido_html.replace('var(--pViewers-color)','gray')

        printlog("Realizando conversiones de data y colores")
        incremento_messages = safe_int(total_messages_1) - safe_int(total_messages_2)
        pMensajes=(incremento_messages/int(total_messages_2))*100
        if safe_int(pMensajes)>0:
            contenido_html =contenido_html.replace('var(--pMensajes-color)','var(--main-color)')
        elif safe_int(pMensajes)==0:
            contenido_html =contenido_html.replace('var(--pMensajes-color)','var(--third-color)')
        elif safe_int(pMensajes)<0:
            contenido_html =contenido_html.replace('var(--pMensajes-color)','var(--second-color)')
        else:
            contenido_html =contenido_html.replace('var(--pMensajes-color)','gray')
            
        # Convertir las cadenas de texto a objetos datetime
        start_time_1 = datetime.strptime(start_time_1, "%Y-%m-%d %H:%M:%S")
        end_time_1 = datetime.strptime(end_time_1, "%Y-%m-%d %H:%M:%S")
        duration = end_time_1 - start_time_1
        duration=str(duration)

        criterios = {
            "Mensajes": safe_int(pMensajes),
            "Viewers": safe_int(pViwers),
        }
        # Ordenar por valor convirtiéndolos a enteros (o flotantes si es necesario)
        criterios_ordenados = dict(sorted(criterios.items(), key=lambda item: item[1], reverse=True))

        # Obtener el primer elemento (clave y valor)
        criterio, criterio_valor = next(iter(criterios_ordenados.items()))
        segundo_criterio, segundo_criterio_valor = list(criterios_ordenados.items())[1]

        printlog("Ordenando criterios de conclusión")
        
        if criterio_valor > 0: rasunto = f'''Incremento del {criterio_valor}% en {criterio} '''
        if criterio_valor == 0: rasunto = f'''Todo igual en {criterio} '''
        if criterio_valor < 0: rasunto = f'''Disminución del {criterio_valor}% en {criterio} '''

        rConclusion = f'''Todo parece indicar que en el último stream se ha registrado un movimiento del {criterio_valor}% en {criterio} y un {segundo_criterio_valor}% en {segundo_criterio}%'''

        pViwers=str(pViwers)[:5]+"%"
        pMensajes=str(pMensajes)[:5]+"%"

        cursor.execute(f'''
            SELECT username FROM users WHERE twitch_id=?
        ''',(top_chatter_1,))
        topChatterName = cursor.fetchone()

  
        now = datetime.now()
        year = now.year
        month = now.month
        table_name = f"chat_{year}{month:02}"
        pmonth = 12 if month-1 == 0 else month - 1
        pyear = year if pmonth != 12 else year - 1
        ptable_name = f"chat_{pyear}{pmonth:02}"

        printlog("Ejecutando consultas complementarias")
        # OBTENER EL CONTEO DE LAS PERSONAS QUE CHATEARON EN DIRECTO AL MENOS UNA VEZ
        cursor.execute(f'''
            WITH allmessages AS (
                SELECT DISTINCT user FROM {ptable_name}
                WHERE timestamp BETWEEN DATETIME('{start_time_1}') AND DATETIME('{end_time_1}')
                union
                SELECT DISTINCT user FROM {table_name}
                WHERE timestamp BETWEEN DATETIME('{start_time_1}') AND DATETIME('{end_time_1}')
                GROUP BY user
                )
            SELECT count(*) AS chatters FROM allmessages
        ''')
        chatters = cursor.fetchone()
        nChatters = str(chatters[0])
        # _________________________________________________________________

        cursor.execute(f'''
            SELECT (SELECT username FROM users WHERE twitch_id=user) as user FROM history_users 
            WHERE date BETWEEN DATETIME('{start_time_1}') AND DATETIME('{end_time_1}')
            UNION
            SELECT (SELECT username FROM users WHERE twitch_id=user) as user FROM {table_name}
            WHERE timestamp BETWEEN DATETIME('{start_time_1}') AND DATETIME('{end_time_1}')
            GROUP BY user
        ''')
        # Obtener los usuarios y extraer solo los nombres (evitar que queden como tuplas)
        users = [user[0] for user in cursor.fetchall()]  

        # Convertir la cadena a un objeto datetime
        # fecha_obj = datetime.strptime(start_time_1, "%Y-%m-%d %H:%M:%S")

        # Formatear la fecha al formato deseado
        fecha_reporte = start_time_1.strftime("%d de %B del %Y")

        # Verificar si hay usuarios
        if users:
            total_users = len(users)
            split_size = (total_users + 2) // 3  # Redondeo hacia arriba para distribuir mejor

            # Dividir los usuarios en tres grupos
            aUsers = "<br>".join(users[:split_size])
            bUsers = "<br>".join(users[split_size:split_size * 2])
            cUsers = "<br>".join(users[split_size * 2:])
        else:
            # Si no hay usuarios, asignar "No users"
            aUsers = "No users"
            bUsers = "No users"
            cUsers = "No users"

        # Cerrar conexión
        conn.close()
        cerrar_conexion(conn, cursor)

        printlog("Reemplazando datos en HTML")
        reemplazos = {
            "[nViwers]": str(total_users_1),
            "[TotalUsers3]":str(total_users_3),
            "[TotalUsers2]":str(total_users_2),
            "[TotalUsers1]":str(total_users_1),
            "[nFollowers]":str(total_follows),
            "[TotalMessages1]":str(total_messages_1),
            "[TotalMessages2]":str(total_messages_2),
            "[TotalMessages3]":str(total_messages_3),
            "[nMensajes]": str(total_messages_1),
            "[pMensajes]": str(pMensajes),
            "[topChatter]": str(topChatterName),
            "[pViewers]": str(pViwers),
            "[nTiempo]": str(duration),
            "[nChatters]":str(nChatters),
            "[MoneyToday]":str(total_money),
            "[tBits]": str(new_bits),
            "[tSubs]": str(new_subs),
            "[aUsers]":str(aUsers),
            "[bUsers]":str(bUsers),
            "[fecha_reporte]":str(fecha_reporte),
            "[cUsers]":str(cUsers),
            "[rConclusion]":str(rConclusion)
        }

        

        # Aplicar reemplazos correctamente
        for palabra, nuevo_valor in reemplazos.items():
            contenido_html = contenido_html.replace(palabra, nuevo_valor)

        
        variables_css = {
            "--bg-color": "#121212",
            "--main-color": "#00f5ff",
            "--second-color": "#ff00a4",
            "--third-color": "#ff9e00",
            "--letter-color":"white",
            "--letter-black":"#2b2b2b",
            "--money-color":"#00ff80",
            "--bg-box":"#161616"
        }

        for var, value in variables_css.items():
            contenido_html = contenido_html.replace(f"var({var})", value)
        # Verificar el resultado
        # print(f'\n\n\n\n\n{contenido_html}\n\n')

        printlog("Inicializando SMTP")
        return await enviar_correo("danieltova97@gmail.com", rasunto, contenido_html)

    except sqlite3.Error as e:
        cerrar_conexion(conn, cursor)
        printlog(f"Error en al intentar generar el mail de reporte : {e}","ERROR")
        return False

    finally:
        if conn:
            conn.close()
            cerrar_conexion(conn, cursor)
    
    
