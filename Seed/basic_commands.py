import os
import json
import sqlite3

from Helpers.helpers import db_cursor
from Helpers.printlog import printlog

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')

DEFAULT_BASIC_COMMAND_SEEDS: list[dict[str, object]] = [
    {
        'command': 'user',
        'aliases': ['usuario', 'name', 'id'],
        'response': '[BOT] - Mi usuario en todos los juegos es DannDato',
    },
    {
        'command': 'tdt',
        'aliases': [],
        'response': '[BOT] - En esta pagina esta toda la informacion para entrar al servidor de minecraft TIERRA DE TODOS https://dato.dannprod.com/tdt/info.html?reglas Tienes que leer las reglas para entender como funciona...',
    },
    {'command': 'iptdt', 'aliases': [], 'response': '[BOT] - La ip de TDT es: tierradetodos.vultam.host'},
    {
        'command': 'lurk',
        'aliases': ['ghost'],
        'response': '[BOT] - Dice @{user} estara viendo el directo de fondo mientras platica con una carinosa...',
    },
    {
        'command': 'unlurk',
        'aliases': ['unghost'],
        'response': '[BOT] - Parece que @{user} regreso muy feliz de con las carinosas!',
    },
    {'command': 'onlyfans', 'aliases': ['of'], 'response': '[BOT] - Senoraaaa! @{user} anda de cochin@!'},
    {'command': 'koala', 'aliases': ['elkoala', 'koalafc'], 'response': '[BOT] - Callense todos, ya llego @elkoalam'},
    {'command': 'daarlaaaaa', 'aliases': ['darla'], 'response': '[BOT] - Como @DAARLAAAAA'},
    {'command': 'maikol', 'aliases': [], 'response': '[BOT] - Abran paso al MOD + Anciano @maikolteve'},
    {
        'command': 'horario',
        'aliases': ['horarios', 'agenda'],
        'response': '[BOT] - Hola @{user}! Tenemos stream Lunes, Miercoles y Viernes | MX 7:00pm | CO 8:00pm | VE 9:00pm | AR 10:00pm | EC 8:00pm | BO 9:00pm | ES 3:00am | PE 8:00pm | UY 10:00pm',
    },
    {
        'command': 'pc',
        'aliases': ['componentes', 'computadora', 'computador'],
        'response': '[BOT] - Mi PC esta armada con estos componentes: Asus RogStrix X670 | Ryzen 9 9900X | 64gb 5600hz | RTX 3060Ti | NZXT H440 | NZXT Kraken 360 | LG 1440p 144Hz | BENQ 1080 100Hz',
    },
    {
        'command': 'camara',
        'aliases': ['cam', 'webcam'],
        'response': '[BOT] - Mi camara es una Canon Rebel T6i con lente 18-135 f3.5',
    },
    {
        'command': 'microfono',
        'aliases': ['mic', 'micro'],
        'response': '[BOT] - Uso un microfono economico de Amazon + Focusrite Scarlett 2i2 Gen 1 y buena mezcla de audio en Dannprod.',
    },
    {
        'command': 'instagram',
        'aliases': ['insta', 'ig'],
        'response': '[BOT] - Instagram: https://www.instagram.com/datotovar',
    },
    {'command': 'youtube', 'aliases': ['yt'], 'response': '[BOT] - Youtube: https://www.youtube.com/@DatoTovar'},
    {
        'command': 'whatsapp',
        'aliases': ['wapp', 'wsp'],
        'response': '[BOT] - Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14',
    },
    {
        'command': 'discord',
        'aliases': ['dc', 'dis'],
        'response': '[BOT] - Unite al Discord: https://discord.gg/PaqYUz69Zx',
    },
    {
        'command': 'spotify',
        'aliases': ['spoty', 'spoti'],
        'response': '[BOT] - Spotify: https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A',
    },
    {
        'command': 'redes',
        'aliases': ['social', 'socials'],
        'response': '[BOT] - Redes: Youtube https://www.youtube.com/@DatoTovar | Instagram https://www.instagram.com/datotovar | Whatsapp https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14 | Discord https://discord.gg/PaqYUz69Zx | Spotify https://open.spotify.com/intl-es/artist/5TMlDvCbDsvQYkvU1uMCF9?si=EN097NInRl-ignGXRQAm1A',
    },
]


def _normalize_custom_command_name(raw_command: str) -> str:
    command_name = (raw_command or '').strip().lower()
    if not command_name:
        return ''
    if not command_name.startswith('!'):
        command_name = f'!{command_name}'
    return command_name.split()[0]


def _ensure_basic_commands_table() -> None:
    with db_cursor(DB_PATH, commit=True) as (_, cursor):
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS commands (
                command TEXT PRIMARY KEY,
                response TEXT NOT NULL,
                aliases TEXT DEFAULT '[]'
            )
            '''
        )
        cursor.execute('PRAGMA table_info(commands)')
        columns = [row[1] for row in cursor.fetchall()]
        if 'aliases' not in columns:
            cursor.execute("ALTER TABLE commands ADD COLUMN aliases TEXT DEFAULT '[]'")


def _parse_aliases(raw_aliases: str | None) -> list[str]:
    if not raw_aliases:
        return []
    try:
        parsed = json.loads(raw_aliases)
        if isinstance(parsed, list):
            return [
                _normalize_custom_command_name(alias)
                for alias in parsed
                if _normalize_custom_command_name(alias)
            ]
    except json.JSONDecodeError:
        pass

    return [
        _normalize_custom_command_name(alias)
        for alias in str(raw_aliases).split(',')
        if _normalize_custom_command_name(alias)
    ]


def _serialize_aliases(aliases: list[str]) -> str:
    normalized_unique = sorted({
        _normalize_custom_command_name(alias)
        for alias in aliases
        if _normalize_custom_command_name(alias)
    })
    return json.dumps(normalized_unique, ensure_ascii=True)


def ensure_seed_basic_commands() -> tuple[int, int]:
    inserted = 0
    total = len(DEFAULT_BASIC_COMMAND_SEEDS)
    consolidated_alias_rows = 0

    try:
        _ensure_basic_commands_table()
        with db_cursor(DB_PATH, commit=True) as (_, cursor):
            for item in DEFAULT_BASIC_COMMAND_SEEDS:
                command_name = _normalize_custom_command_name(str(item.get('command', '')))
                response = str(item.get('response', '')).strip()
                raw_aliases = item.get('aliases') or []
                aliases = [
                    _normalize_custom_command_name(str(alias))
                    for alias in raw_aliases
                    if _normalize_custom_command_name(str(alias))
                ]
                aliases = [alias for alias in aliases if alias != command_name]

                if not command_name or not response:
                    continue

                cursor.execute(
                    'SELECT response, aliases FROM commands WHERE command = ? LIMIT 1',
                    (command_name,),
                )
                existing = cursor.fetchone()

                if existing:
                    _, existing_aliases_raw = existing
                    merged_aliases = sorted(set(_parse_aliases(existing_aliases_raw)) | set(aliases))
                    cursor.execute(
                        'UPDATE commands SET aliases = ? WHERE command = ?',
                        (_serialize_aliases(merged_aliases), command_name),
                    )
                else:
                    cursor.execute(
                        'INSERT INTO commands (command, response, aliases) VALUES (?, ?, ?)',
                        (command_name, response, _serialize_aliases(aliases)),
                    )
                    if cursor.rowcount > 0:
                        inserted += 1

                # Limpia filas antiguas duplicadas por alias del seed previo.
                for alias in aliases:
                    cursor.execute('SELECT response FROM commands WHERE command = ? LIMIT 1', (alias,))
                    alias_row = cursor.fetchone()
                    if alias_row and alias_row[0] == response:
                        cursor.execute('DELETE FROM commands WHERE command = ?', (alias,))
                        if cursor.rowcount > 0:
                            consolidated_alias_rows += 1

        if consolidated_alias_rows > 0:
            printlog(f'Seed de comandos consolido {consolidated_alias_rows} filas alias antiguas.', 'DEBUG')
    except sqlite3.Error as e:
        printlog(f'Error haciendo seed de comandos base: {e}', 'ERROR')

    return inserted, total
