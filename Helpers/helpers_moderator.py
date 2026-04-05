import asyncio
import re
import unicodedata
import difflib
import os
import sqlite3

import aiohttp

from Helpers.helpers import db_cursor
from Helpers.token_loader import load_token
from Helpers.printlog import printlog

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

DEFAULT_BASIC_COMMAND_SEEDS: dict[str, str] = {
    # user
    'user': '[BOT] - Mi usuario en todos los juegos es DannDato',
    'usuario': '[BOT] - Mi usuario en todos los juegos es DannDato',
    'name': '[BOT] - Mi usuario en todos los juegos es DannDato',
    'id': '[BOT] - Mi usuario en todos los juegos es DannDato',

    # tdt
    'tdt': '[BOT] - En esta pagina esta toda la informacion para entrar al servidor de minecraft TIERRA DE TODOS https://dato.dannprod.com/tdt/info.html?reglas Tienes que leer las reglas para entender como funciona...',
    'iptdt': '[BOT] - La ip de TDT es: tierradetodos.vultam.host',

    # social/fun
    'lurk': '[BOT] - Dice @{user} estara viendo el directo de fondo mientras platica con una carinosa...',
    'ghost': '[BOT] - Dice @{user} estara viendo el directo de fondo mientras platica con una carinosa...',
    'unlurk': '[BOT] - Parece que @{user} regreso muy feliz de con las carinosas!',
    'unghost': '[BOT] - Parece que @{user} regreso muy feliz de con las carinosas!',
    'onlyfans': '[BOT] - Senoraaaa! @{user} anda de cochin@!',
    'of': '[BOT] - Senoraaaa! @{user} anda de cochin@!',

    # amigos
    'koala': '[BOT] - Callense todos, ya llego @elkoalam',
    'elkoala': '[BOT] - Callense todos, ya llego @elkoalam',
    'koalafc': '[BOT] - Callense todos, ya llego @elkoalam',
    'daarlaaaaa': '[BOT] - Como @DAARLAAAAA',
    'darla': '[BOT] - Como @DAARLAAAAA',
    'maikol': '[BOT] - Abran paso al MOD + Anciano @maikolteve',

    # informativo
    'horario': '[BOT] - Hola @{user}! Tenemos stream Lunes, Miercoles y Viernes | MX 7:00pm | CO 8:00pm | VE 9:00pm | AR 10:00pm | EC 8:00pm | BO 9:00pm | ES 3:00am | PE 8:00pm | UY 10:00pm',
    'horarios': '[BOT] - Hola @{user}! Tenemos stream Lunes, Miercoles y Viernes | MX 7:00pm | CO 8:00pm | VE 9:00pm | AR 10:00pm | EC 8:00pm | BO 9:00pm | ES 3:00am | PE 8:00pm | UY 10:00pm',
    'agenda': '[BOT] - Hola @{user}! Tenemos stream Lunes, Miercoles y Viernes | MX 7:00pm | CO 8:00pm | VE 9:00pm | AR 10:00pm | EC 8:00pm | BO 9:00pm | ES 3:00am | PE 8:00pm | UY 10:00pm',

    # setup
    'pc': '[BOT] - Mi PC esta armada con estos componentes: Asus RogStrix X670 | Ryzen 9 9900X | 64gb 5600hz | RTX 3060Ti | NZXT H440 | NZXT Kraken 360 | LG 1440p 144Hz | BENQ 1080 100Hz',
    'componentes': '[BOT] - Mi PC esta armada con estos componentes: Asus RogStrix X670 | Ryzen 9 9900X | 64gb 5600hz | RTX 3060Ti | NZXT H440 | NZXT Kraken 360 | LG 1440p 144Hz | BENQ 1080 100Hz',
    'computadora': '[BOT] - Mi PC esta armada con estos componentes: Asus RogStrix X670 | Ryzen 9 9900X | 64gb 5600hz | RTX 3060Ti | NZXT H440 | NZXT Kraken 360 | LG 1440p 144Hz | BENQ 1080 100Hz',
    'computador': '[BOT] - Mi PC esta armada con estos componentes: Asus RogStrix X670 | Ryzen 9 9900X | 64gb 5600hz | RTX 3060Ti | NZXT H440 | NZXT Kraken 360 | LG 1440p 144Hz | BENQ 1080 100Hz',
    'camara': '[BOT] - Mi camara es una Canon Rebel T6i con lente 18-135 f3.5',
    'cam': '[BOT] - Mi camara es una Canon Rebel T6i con lente 18-135 f3.5',
    'webcam': '[BOT] - Mi camara es una Canon Rebel T6i con lente 18-135 f3.5',
    'microfono': '[BOT] - Uso un microfono economico de Amazon + Focusrite Scarlett 2i2 Gen 1 y buena mezcla de audio en Dannprod.',
    'mic': '[BOT] - Uso un microfono economico de Amazon + Focusrite Scarlett 2i2 Gen 1 y buena mezcla de audio en Dannprod.',
    'micro': '[BOT] - Uso un microfono economico de Amazon + Focusrite Scarlett 2i2 Gen 1 y buena mezcla de audio en Dannprod.',

    # redes
    'instagram': '[BOT] - Instagram: https://www.instagram.com/datotovar',
    'insta': '[BOT] - Instagram: https://www.instagram.com/datotovar',
    'ig': '[BOT] - Instagram: https://www.instagram.com/datotovar',
    'youtube': '[BOT] - Youtube: https://www.youtube.com/@DatoTovar',
    'yt': '[BOT] - Youtube: https://www.youtube.com/@DatoTovar',
    'whatsapp': '[BOT] - Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14',
    'wapp': '[BOT] - Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14',
    'wsp': '[BOT] - Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14',
    'discord': '[BOT] - Unite al Discord: https://discord.gg/PaqYUz69Zx',
    'dc': '[BOT] - Unite al Discord: https://discord.gg/PaqYUz69Zx',
    'dis': '[BOT] - Unite al Discord: https://discord.gg/PaqYUz69Zx',
    'spotify': '[BOT] - Spotify: https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A',
    'spoty': '[BOT] - Spotify: https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A',
    'spoti': '[BOT] - Spotify: https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A',
    'redes': '[BOT] - Redes: Youtube https://www.youtube.com/@DatoTovar | Instagram https://www.instagram.com/datotovar | Whatsapp https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14 | Discord https://discord.gg/PaqYUz69Zx | Spotify https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A',
    'social': '[BOT] - Redes: Youtube https://www.youtube.com/@DatoTovar | Instagram https://www.instagram.com/datotovar | Whatsapp https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14 | Discord https://discord.gg/PaqYUz69Zx | Spotify https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A',
    'socials': '[BOT] - Redes: Youtube https://www.youtube.com/@DatoTovar | Instagram https://www.instagram.com/datotovar | Whatsapp https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14 | Discord https://discord.gg/PaqYUz69Zx | Spotify https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A',
}

def _normalize_custom_command_name(raw_command: str) -> str:
    command_name = (raw_command or '').strip().lower()
    if not command_name:
        return ''
    if not command_name.startswith('!'):
        command_name = f'!{command_name}'
    return command_name.split()[0]


def _ensure_basic_commands_table() -> None:
    with db_cursor(DB_PATH, commit=True) as (_, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                command TEXT PRIMARY KEY,
                response TEXT NOT NULL
            )
        ''')


def ensure_seed_basic_commands() -> tuple[int, int]:
    """Inserta comandos base una sola vez sin sobreescribir personalizados existentes."""
    inserted = 0
    total = len(DEFAULT_BASIC_COMMAND_SEEDS)

    try:
        _ensure_basic_commands_table()
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            for command_name, response in DEFAULT_BASIC_COMMAND_SEEDS.items():
                normalized_name = _normalize_custom_command_name(command_name)
                if not normalized_name:
                    continue
                cursor.execute(
                    'INSERT OR IGNORE INTO commands (command, response) VALUES (?, ?)',
                    (normalized_name, response)
                )
                if cursor.rowcount > 0:
                    inserted += 1
    except sqlite3.Error as e:
        printlog(f'Error haciendo seed de comandos base: {e}', 'ERROR')

    return inserted, total


async def save_basic_command(raw_command: str, raw_response: str) -> tuple[bool, str]:
    command_name = _normalize_custom_command_name(raw_command)
    response = (raw_response or '').strip()

    if not command_name:
        return False, 'El comando no puede estar vacio.'
    if command_name == '!':
        return False, 'El comando no es valido.'
    if len(command_name) < 2:
        return False, 'El comando no es valido.'
    if not response:
        return False, 'La respuesta no puede estar vacia.'

    try:
        _ensure_basic_commands_table()
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute(
                '''
                INSERT INTO commands (command, response)
                VALUES (?, ?)
                ON CONFLICT(command)
                DO UPDATE SET response = excluded.response
                ''',
                (command_name, response)
            )
        return True, command_name
    except sqlite3.Error as e:
        printlog(f'Error guardando comando basico {command_name}: {e}', 'ERROR')
        return False, 'No pude guardar el comando en la base de datos.'


async def edit_basic_command(raw_command: str, raw_response: str) -> tuple[bool, str]:
    command_name = _normalize_custom_command_name(raw_command)
    response = (raw_response or '').strip()

    if not command_name:
        return False, 'El comando no puede estar vacio.'
    if command_name == '!':
        return False, 'El comando no es valido.'
    if len(command_name) < 2:
        return False, 'El comando no es valido.'
    if not response:
        return False, 'La nueva respuesta no puede estar vacia.'

    try:
        _ensure_basic_commands_table()
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('SELECT 1 FROM commands WHERE command = ? LIMIT 1', (command_name,))
            exists = cursor.fetchone() is not None
            if not exists:
                return False, 'Ese comando personalizado no existe. Crea uno con !newcmd.'

            cursor.execute(
                'UPDATE commands SET response = ? WHERE command = ?',
                (response, command_name)
            )

        return True, command_name
    except sqlite3.Error as e:
        printlog(f'Error editando comando basico {command_name}: {e}', 'ERROR')
        return False, 'No pude editar el comando en la base de datos.'


async def delete_basic_command(raw_command: str) -> tuple[bool, str]:
    command_name = _normalize_custom_command_name(raw_command)

    if not command_name:
        return False, 'El comando no puede estar vacio.'
    if command_name == '!':
        return False, 'El comando no es valido.'
    if len(command_name) < 2:
        return False, 'El comando no es valido.'

    try:
        _ensure_basic_commands_table()
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            cursor.execute('DELETE FROM commands WHERE command = ?', (command_name,))
            if cursor.rowcount <= 0:
                return False, 'Ese comando personalizado no existe.'

        return True, command_name
    except sqlite3.Error as e:
        printlog(f'Error eliminando comando basico {command_name}: {e}', 'ERROR')
        return False, 'No pude eliminar el comando de la base de datos.'


def get_basic_command_response(raw_command: str) -> str | None:
    command_name = _normalize_custom_command_name(raw_command)
    if not command_name:
        return None

    try:
        _ensure_basic_commands_table()
        with db_cursor(DB_PATH) as (_, cursor):
            cursor.execute('SELECT response FROM commands WHERE command = ? LIMIT 1', (command_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    except sqlite3.Error as e:
        printlog(f'Error leyendo comando basico {command_name}: {e}', 'ERROR')
        return None


def custom_command_exists(raw_command: str) -> bool:
    command_name = _normalize_custom_command_name(raw_command)
    if not command_name:
        return False

    try:
        _ensure_basic_commands_table()
        with db_cursor(DB_PATH) as (_, cursor):
            cursor.execute('SELECT 1 FROM commands WHERE command = ? LIMIT 1', (command_name,))
            return cursor.fetchone() is not None
    except sqlite3.Error as e:
        printlog(f'Error validando existencia de comando basico {command_name}: {e}', 'ERROR')
        return False


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

    # Favorece coincidencias con typos cuando los espacios cambian.
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


def _expand_category_queries(query: str) -> list[str]:
    normalized = _normalize_text(query)
    variants = [query.strip()]

    alias_map = {
        # Typos comunes de Fortnite
        "fornai": "Fortnite",
        "fortnai": "Fortnite",
        "fornite": "Fortnite",
        "forknite": "Fortnite",
        "forknine": "Fortnite",
        "fortnite": "Fortnite",

        # Tecnologia en espanol/ingles
        "tecnologia": "Science & Technology",
        "tecnology": "Science & Technology",
        "technology": "Science & Technology",
        "science and technology": "Science & Technology",
        "science technology": "Science & Technology",
    }

    mapped = alias_map.get(normalized)
    if mapped and mapped not in variants:
        variants.append(mapped)

    return variants


def _preferred_category_name(query: str) -> str | None:
    normalized = _normalize_text(query)
    preferred = {
        "tecnologia": "Science & Technology",
        "tecnology": "Science & Technology",
        "technology": "Science & Technology",
        "fornai": "Fortnite",
        "fortnai": "Fortnite",
        "fornite": "Fortnite",
        "forknite": "Fortnite",
        "forknine": "Fortnite",
    }
    return preferred.get(normalized)


def _preferred_category_id(query: str) -> str | None:
    normalized = _normalize_text(query)
    preferred_ids = {
        # Twitch category IDs conocidas y estables para casos frecuentes.
        "tecnologia": "509670",  # Science & Technology
        "tecnology": "509670",
        "technology": "509670",
        "science and technology": "509670",
        "science technology": "509670",
        "fornai": "33214",      # Fortnite
        "fortnai": "33214",
        "fornite": "33214",
        "forknite": "33214",
        "forknine": "33214",
        "fortnite": "33214",
    }
    return preferred_ids.get(normalized)


def _score_category_candidate(
    user_query: str,
    query_variants: list[str],
    candidate_name: str,
    top_rank: int | None,
) -> float:
    # Similaridad base contra query original y variantes (aliases/correcciones).
    score = _similarity_score(user_query, candidate_name)
    for variant in query_variants:
        score = max(score, _similarity_score(variant, candidate_name))

    # Bonus por popularidad (top categories) para resolver mejor typos ambiguos.
    if top_rank is not None:
        # rank 1 -> +0.20, rank 100 -> ~+0.00
        popularity_bonus = max(0.0, (101 - top_rank) / 100.0) * 0.20
        score += popularity_bonus

    return score


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

    query_variants = _expand_category_queries(query)
    preferred_name = _preferred_category_name(query)
    preferred_id = _preferred_category_id(query)

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

    # Atajo confiable para intenciones muy comunes (evita matches raros por typo).
    if preferred_id and preferred_name:
        try:
            async with aiohttp.ClientSession() as session:
                params = {"broadcaster_id": str(broadcaster_id)}
                payload = {"game_id": preferred_id}
                async with session.patch(
                    "https://api.twitch.tv/helix/channels",
                    headers=headers,
                    params=params,
                    json=payload,
                ) as resp:
                    if resp.status == 204:
                        return True, preferred_name
                    body = await resp.text()
                    printlog(f"No se pudo aplicar categoria preferida ({resp.status}): {body}", "WARNING")
        except Exception as e:
            printlog(f"Error aplicando categoria preferida: {e}", "WARNING")

    try:
        async with aiohttp.ClientSession() as session:
            candidates_by_id: dict[str, dict] = {}
            top_rank_by_id: dict[str, int] = {}

            # 1) Buscar por query y por variantes para ampliar cobertura de typos/idioma.
            for q in query_variants:
                async with session.get(
                    "https://api.twitch.tv/helix/search/categories",
                    headers=headers,
                    params={"query": q, "first": 30},
                ) as resp:
                    if resp.status != 200:
                        data = await resp.text()
                        printlog(f"Error buscando categoria ({resp.status}): {data}", "WARNING")
                        return False, "No pude buscar categorias en Twitch."

                    data = await resp.json()
                    for item in data.get("data", []):
                        category_id = item.get("id")
                        if category_id:
                            candidates_by_id[category_id] = item

            # 2) Mezclar con top categorias para priorizar las principales de Twitch.
            async with session.get(
                "https://api.twitch.tv/helix/games/top",
                headers=headers,
                params={"first": 100},
            ) as top_resp:
                if top_resp.status == 200:
                    top_data = await top_resp.json()
                    for idx, item in enumerate(top_data.get("data", []), start=1):
                        category_id = item.get("id")
                        if category_id:
                            top_rank_by_id[category_id] = idx
                            candidates_by_id.setdefault(category_id, item)

            candidates = list(candidates_by_id.values())
            if not candidates:
                return False, "No encontre categorias parecidas."

            scored_candidates = []

            # Preferencia dura para categorias clave (ej. tecnologia -> Science & Technology)
            if preferred_name:
                preferred_norm = _normalize_text(preferred_name)
                for item in candidates:
                    if _normalize_text(item.get("name", "")) == preferred_norm:
                        best = item
                        best_score = 1.0
                        break
                else:
                    best = None
                    best_score = 0.0
            else:
                best = None
                best_score = 0.0

            if best is None:
                for item in candidates:
                    category_id = item.get("id", "")
                    name = item.get("name", "")
                    rank = top_rank_by_id.get(category_id)
                    score = _score_category_candidate(query, query_variants, name, rank)
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
                    if not clip_id:
                        return True, "Clip solicitado. En unos segundos deberia aparecer en el canal."

                    # Twitch puede devolver 202 antes de que el clip este publicado.
                    # Reintentamos brevemente hasta obtener la URL publica final.
                    for _ in range(10):
                        async with session.get(
                            "https://api.twitch.tv/helix/clips",
                            headers=headers,
                            params={"id": clip_id},
                        ) as get_resp:
                            get_data = await get_resp.json(content_type=None)
                            if get_resp.status == 200 and get_data.get("data"):
                                url = get_data["data"][0].get("url")
                                if url:
                                    return True, f"Clip creado: {url}"
                        await asyncio.sleep(1)

                    # Fallback si Helix aun no entrega URL publica.
                    return True, f"Clip creado: https://clips.twitch.tv/{clip_id}"

                if resp.status == 404:
                    return False, "De que hago clip si no está en vivo 😑."
                if resp.status in (401, 403):
                    return False, "Sin permisos para crear clip. Díganle a dato que le falta el scope clips:edit."
                if resp.status == 429:
                    return False, "Demasiados intentos de clip. Esperen un poco..."

                printlog(f"Error creando clip ({resp.status}): {data}", "WARNING")
                return False, "No pude crear el clip en Twitch."
    except Exception as e:
        printlog(f"Error creando clip: {e}", "WARNING")
        return False, "Error al crear el clip en Twitch."
