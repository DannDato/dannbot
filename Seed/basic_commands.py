import os
import sqlite3

from Helpers.helpers import db_cursor
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
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS commands (
                command TEXT PRIMARY KEY,
                response TEXT NOT NULL
            )
            '''
        )


def ensure_seed_basic_commands() -> tuple[int, int]:
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
                    (normalized_name, response),
                )
                if cursor.rowcount > 0:
                    inserted += 1
    except sqlite3.Error as e:
        printlog(f'Error haciendo seed de comandos base: {e}', 'ERROR')

    return inserted, total
