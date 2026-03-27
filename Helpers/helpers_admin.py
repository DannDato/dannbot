import sqlite3
import os
import re
import unicodedata
import difflib
import aiohttp
from datetime import datetime


from Helpers.helpers_stats import update_global_stats, get_top_chatter_day
from Helpers.helpers_xp import update_xp
from Helpers.helpers_bot import update_stream_data
from Helpers.mailer import enviar_correo
from Helpers.helpers import safe_int, db_cursor
from Helpers.token_loader import load_token
from Helpers.printlog import printlog

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')


def _normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _similarity_score(query: str, candidate: str) -> float:
    q = _normalize_text(query)
    c = _normalize_text(candidate)
    if not q or not c:
        return 0.0

    if q == c:
        return 1.0

    base = difflib.SequenceMatcher(None, q, c).ratio()

    # Favorece coincidencias con typos cuando los espacios cambian (ej: "callofduty").
    q_compact = q.replace(" ", "")
    c_compact = c.replace(" ", "")
    compact_ratio = difflib.SequenceMatcher(None, q_compact, c_compact).ratio()
    base = max(base, compact_ratio)

    if q in c or c in q:
        base = max(base, 0.92)

    q_tokens = set(q.split())
    c_tokens = set(c.split())
    if q_tokens and c_tokens:
        overlap = len(q_tokens & c_tokens) / len(q_tokens)
        base = max(base, overlap)

    return base


def _category_match_threshold(query: str) -> float:
    q_len = len(_normalize_text(query).replace(" ", ""))
    if q_len <= 4:
        return 0.80
    if q_len <= 7:
        return 0.68
    if q_len <= 12:
        return 0.56
    return 0.48


async def set_stream_title(raw_title: str) -> tuple[bool, str]:
    suffix = "[ !redes !discord !sr ]"
    title = (raw_title or "").strip()
    if not title:
        return False, "El titulo no puede estar vacio."

    if title.endswith(suffix):
        final_title = title
    else:
        final_title = f"{title} {suffix}"

    token_data = load_token()
    access_token = token_data.get("access_token")
    client_id = token_data.get("client_id")
    broadcaster_id = token_data.get("owner_id") or token_data.get("bot_id")

    if not access_token or not client_id or not broadcaster_id:
        return False, "Faltan credenciales para actualizar el titulo."

    headers = {
        "Client-Id": client_id,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    params = {"broadcaster_id": str(broadcaster_id)}
    payload = {"title": final_title}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                "https://api.twitch.tv/helix/channels",
                headers=headers,
                params=params,
                json=payload,
            ) as resp:
                if resp.status == 204:
                    return True, final_title

                data = await resp.text()
                printlog(f"No se pudo actualizar titulo ({resp.status}): {data}", "WARNING")
                return False, "No pude cambiar el titulo. Revisa que el token tenga permisos channel:manage:broadcast."
    except Exception as e:
        printlog(f"Error actualizando titulo: {e}", "WARNING")
        return False, "Error al cambiar el titulo en Twitch."


async def set_stream_category(raw_category: str) -> tuple[bool, str]:
    query = (raw_category or "").strip()
    if not query:
        return False, "La categoria no puede estar vacia."

    token_data = load_token()
    access_token = token_data.get("access_token")
    client_id = token_data.get("client_id")
    broadcaster_id = token_data.get("owner_id") or token_data.get("bot_id")

    if not access_token or not client_id or not broadcaster_id:
        return False, "Faltan credenciales para actualizar la categoria."

    headers = {
        "Client-Id": client_id,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.twitch.tv/helix/search/categories",
                headers=headers,
                params={"query": query, "first": 20},
            ) as resp:
                if resp.status != 200:
                    data = await resp.text()
                    printlog(f"Error buscando categoria ({resp.status}): {data}", "WARNING")
                    return False, "No pude buscar categorias en Twitch."

                data = await resp.json()
                candidates = data.get("data", [])
                if not candidates:
                    return False, "No encontre categorias parecidas."

            scored_candidates = []
            for item in candidates:
                name = item.get("name", "")
                score = _similarity_score(query, name)
                scored_candidates.append((score, item))

            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best = scored_candidates[0] if scored_candidates else (0.0, None)

            threshold = _category_match_threshold(query)
            if not best or best_score < threshold:
                suggestions = [item.get("name", "") for _, item in scored_candidates[:3] if item.get("name")]
                if suggestions:
                    return False, f"No encontre una categoria suficientemente parecida. Prueba con: {' | '.join(suggestions)}"
                return False, "No encontre una categoria suficientemente parecida."

            params = {"broadcaster_id": str(broadcaster_id)}
            payload = {"game_id": best.get("id")}
            async with session.patch(
                "https://api.twitch.tv/helix/channels",
                headers=headers,
                params=params,
                json=payload,
            ) as resp:
                if resp.status == 204:
                    return True, best.get("name", query)

                body = await resp.text()
                printlog(f"No se pudo actualizar categoria ({resp.status}): {body}", "WARNING")
                return False, "No pude cambiar la categoria. Revisa permisos channel:manage:broadcast."
    except Exception as e:
        printlog(f"Error actualizando categoria: {e}", "WARNING")
        return False, "Error al cambiar la categoria en Twitch."


def _seconds_to_hms(seconds: int) -> str:
    total = max(0, int(seconds or 0))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


async def create_stream_marker(raw_description: str = "") -> tuple[bool, str]:
    token_data = load_token()
    access_token = token_data.get("access_token")
    client_id = token_data.get("client_id")
    broadcaster_id = token_data.get("owner_id") or token_data.get("bot_id")

    if not access_token or not client_id or not broadcaster_id:
        return False, "Faltan credenciales para crear el marker."

    description = (raw_description or "").strip()
    if len(description) > 140:
        description = description[:140]

    headers = {
        "Client-Id": client_id,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {"user_id": str(broadcaster_id)}
    if description:
        payload["description"] = description

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.twitch.tv/helix/streams/markers",
                headers=headers,
                json=payload,
            ) as resp:
                data = await resp.json(content_type=None)

                if resp.status == 200 and data.get("data"):
                    marker = data["data"][0]
                    marker_id = marker.get("id", "?")
                    position_seconds = marker.get("position_seconds", 0)
                    hms = _seconds_to_hms(position_seconds)
                    return True, f"Marker creado (ID: {marker_id}) en {hms} del VOD."

                if resp.status == 400:
                    return False, "No pude crear marker. Asegurate de estar en vivo."
                if resp.status in (401, 403):
                    return False, "Sin permisos para crear marker. Revisa scopes del token."

                printlog(f"Error creando marker ({resp.status}): {data}", "WARNING")
                return False, "No pude crear el marker en Twitch."
    except Exception as e:
        printlog(f"Error creando marker: {e}", "WARNING")
        return False, "Error al crear el marker en Twitch."


async def create_stream_clip(has_delay: bool = True) -> tuple[bool, str]:
    token_data = load_token()
    access_token = token_data.get("access_token")
    client_id = token_data.get("client_id")
    broadcaster_id = token_data.get("owner_id") or token_data.get("bot_id")

    if not access_token or not client_id or not broadcaster_id:
        return False, "Faltan credenciales para crear el clip."

    headers = {
        "Client-Id": client_id,
        "Authorization": f"Bearer {access_token}",
    }
    params = {
        "broadcaster_id": str(broadcaster_id),
        "has_delay": str(bool(has_delay)).lower(),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.twitch.tv/helix/clips",
                headers=headers,
                params=params,
            ) as resp:
                data = await resp.json(content_type=None)

                if resp.status in (200, 202) and data.get("data"):
                    clip = data["data"][0]
                    clip_id = clip.get("id")
                    edit_url = clip.get("edit_url")
                    public_url = f"https://clips.twitch.tv/{clip_id}" if clip_id else None

                    if edit_url and public_url:
                        return True, f"Clip creado: {public_url} | Editar: {edit_url}"
                    if edit_url:
                        return True, f"Clip creado. Editalo aqui: {edit_url}"
                    if public_url:
                        return True, f"Clip creado: {public_url}"
                    return True, "Clip solicitado. En unos segundos deberia aparecer en el canal."

                if resp.status == 404:
                    return False, "No pude crear clip. Asegurate de estar en vivo."
                if resp.status in (401, 403):
                    return False, "Sin permisos para crear clip. Revisa que el token tenga clips:edit."
                if resp.status == 429:
                    return False, "Demasiados intentos de clip. Espera un poco y vuelve a intentar."

                printlog(f"Error creando clip ({resp.status}): {data}", "WARNING")
                return False, "No pude crear el clip en Twitch."
    except Exception as e:
        printlog(f"Error creando clip: {e}", "WARNING")
        return False, "Error al crear el clip en Twitch."

# ACTUALIZAR ESTADISTICAS DE LA CATEGORIA PARAMETRIZADA
async def end_stream():
    """
    Finaliza un stream si está iniciado y no se ha cerrado.

    :param db_path: Ruta a la base de datos SQLite.
    :return: True si se finalizó el stream, False en caso contrario.
    """
    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
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

            if not result:
                printlog("No se encontró ningún stream iniciado y sin cerrar.","WARNING")
                return False

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
            mSubs = (safe_int(subs) * 1.52) * dollar
            mBits = (safe_int(bits) / 100) * dollar
            total_money = safe_int(mSubs + mBits)

            cursor.execute('''
                INSERT INTO stream_data (accion, value, date)
                VALUES ("total_money", ?, ?),("end_stream", "channel", ?);
            ''', (total_money, current_date, current_date))

        top_chatter_day = await get_top_chatter_day()
        if top_chatter_day is not None:
            await update_global_stats("xp_Fuerza", top_chatter_day, 3)
            await update_global_stats("top_chatter_day", top_chatter_day, 1)

        await update_xp()
        await end_mail()
        printlog(f"Stream finalizado correctamente: {current_date}.")
        return True

    except sqlite3.Error as e:
        printlog(f"Error en la base de datos: {e}","ERROR")
        return False


async def start_stream():
    """
    Inicia un nuevo stream si no hay uno iniciado o si el último stream fue terminado.

    :param db_path: Ruta a la base de datos SQLite.
    :return: True si se inició el stream, False en caso contrario.
    """
    try:
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
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

            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO stream_data (accion, value, date)
                VALUES ("start_stream", "channel", ?),("new_followers", "0", ?);
            ''', (current_date, current_date))

        await update_stream_data("total_users", 1)
        await update_stream_data("total_messages", 1)
        printlog(f"Nuevo stream iniciado correctamente a las {current_date}.")
        return True

    except sqlite3.Error as e:
        printlog(f"Error en la base de datos: {e}","ERROR")
        return False

async def end_mail():
    """Lee el contenido de un archivo HTML y lo devuelve como texto"""
    HTML_PATH = os.path.join(os.path.dirname(__file__), '..', 'Html', 'mails', 'end_stream.html')
    printlog("Generando reporte de stream...")
    with open(HTML_PATH, "r", encoding="utf-8") as archivo:
        contenido_html = archivo.read()
        printlog("Leyendo HTML de reporte")
    try:
        with db_cursor(DB_PATH) as (_, cursor):
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
                if stream_number not in streams:
                    streams[stream_number] = {}
                if accion not in streams[stream_number]:
                    if accion in ["first_user", "total_messages", "total_users", "top_chatter","new_bits","new_subs","total_money","new_followers","stream_max_viewers","stream_avg_viewers"]:
                        streams[stream_number][accion] = []
                    else:
                        streams[stream_number][accion] = {}

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
        stream_max_viewers_1 = streams[1]["stream_max_viewers"][0] if "stream_max_viewers" in streams[1] else 0
        stream_avg_viewers_1 = streams[1]["stream_avg_viewers"][0] if "stream_avg_viewers" in streams[1] else 0


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

        cursor.execute('''
            SELECT username FROM users WHERE twitch_id=?
        ''', (top_chatter_1,))
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

        cursor.execute(f'''
        SELECT (SELECT username FROM users WHERE twitch_id=user) as user FROM history_users
        WHERE date BETWEEN DATETIME('{start_time_1}') AND DATETIME('{end_time_1}')
        UNION
        SELECT (SELECT username FROM users WHERE twitch_id=user) as user FROM {table_name}
        WHERE timestamp BETWEEN DATETIME('{start_time_1}') AND DATETIME('{end_time_1}')
        GROUP BY user
        ''')
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
            total_users = 0
            aUsers = "No users"
            bUsers = "No users"
            cUsers = "No users"

        printlog("Reemplazando datos en HTML")
        reemplazos = {
            "[nViwers]": str(total_users),
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
            "[rConclusion]":str(rConclusion),
            "[peakViewers]": str(stream_max_viewers_1),
            "[avgViewers]": str(stream_avg_viewers_1)
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
        printlog(f"Error en al intentar generar el mail de reporte : {e}","ERROR")
        return False


