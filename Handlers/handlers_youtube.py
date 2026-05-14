import os
import re
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import aiohttp

from Helpers.helpers import db_cursor
from Helpers.discord_notifier import notify_youtube_video
from Helpers.feature_flags import is_feature_enabled
from Helpers.printlog import printlog


DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_env_file() -> None:
    if not ENV_PATH.exists():
        return

    try:
        with ENV_PATH.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue

                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                os.environ[key] = value
    except Exception as exc:
        printlog(f"[YouTube] No se pudo cargar .env: {exc}", "WARNING")


def _get_youtube_channel_id() -> str:
    _load_env_file()
    return os.getenv("YOUTUBE_CHANNEL_ID", "").strip()


def _get_youtube_channel_url() -> str:
    _load_env_file()
    return os.getenv("YOUTUBE_CHANNEL_URL", "").strip()


def _get_youtube_channel_url_for(channel_id: str) -> str:
    configured = _get_youtube_channel_url()
    if configured:
        return configured
    return f"https://www.youtube.com/channel/{channel_id}"


def _get_youtube_poll_interval(default_seconds: int = 600) -> int:
    _load_env_file()
    raw = os.getenv("YOUTUBE_POLL_INTERVAL_SECONDS", "").strip()
    if not raw:
        return default_seconds

    try:
        value = int(raw)
        return max(60, value)
    except ValueError:
        return default_seconds


def _ensure_youtube_state_table() -> None:
    with db_cursor(DB_PATH, commit=True) as (_, cursor):
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS youtube_state (
                channel_id TEXT PRIMARY KEY,
                last_video_id TEXT,
                last_published_at TEXT,
                updated_at TEXT
            )
            '''
        )


def _get_last_video_id(channel_id: str) -> str | None:
    with db_cursor(DB_PATH) as (_, cursor):
        cursor.execute(
            "SELECT last_video_id FROM youtube_state WHERE channel_id = ?",
            (channel_id,),
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else None


def _save_last_video(channel_id: str, video_id: str, published_at: str | None) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_cursor(DB_PATH, commit=True) as (_, cursor):
        cursor.execute(
            '''
            INSERT INTO youtube_state (channel_id, last_video_id, last_published_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                last_video_id = excluded.last_video_id,
                last_published_at = excluded.last_published_at,
                updated_at = excluded.updated_at
            ''',
            (channel_id, video_id, published_at or "", now),
        )


async def _resolve_channel_id_from_url(session: aiohttp.ClientSession, channel_url: str) -> str | None:
    """Intenta obtener el channel_id real parseando la página del canal de YouTube."""
    try:
        async with session.get(channel_url) as resp:
            if resp.status != 200:
                return None
            html = await resp.text()
        match = re.search(r'"channelId"\s*:\s*"(UC[\w-]{22})"', html)
        if not match:
            match = re.search(r'"externalId"\s*:\s*"(UC[\w-]{22})"', html)
        return match.group(1) if match else None
    except Exception:
        return None


async def _fetch_latest_video(channel_id: str) -> dict | None:
    timeout = aiohttp.ClientTimeout(total=20)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            async with session.get(feed_url) as response:
                if response.status == 404:
                    # channel_id incorrecto — intentar resolverlo desde la URL del canal configurada
                    channel_url = _get_youtube_channel_url()
                    if channel_url:
                        printlog(f"[YouTube] Feed 404 para {channel_id}. Intentando resolver ID desde {channel_url} ...", "WARNING")
                        resolved_id = await _resolve_channel_id_from_url(session, channel_url)
                        if resolved_id and resolved_id != channel_id:
                            printlog(f"[YouTube] Channel ID resuelto: {resolved_id} (era {channel_id}). Actualiza YOUTUBE_CHANNEL_ID en .env.", "WARNING")
                            # Reintentar con el ID correcto
                            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={resolved_id}"
                            async with session.get(feed_url) as retry_resp:
                                if retry_resp.status != 200:
                                    body = await retry_resp.text()
                                    printlog(f"[YouTube] Error al consultar feed con ID resuelto ({retry_resp.status}): {body[:220]}", "WARNING")
                                    return None
                                xml_text = await retry_resp.text()
                        else:
                            printlog(f"[YouTube] No se pudo resolver el channel_id desde la página del canal.", "WARNING")
                            return None
                    else:
                        printlog(f"[YouTube] Feed 404. YOUTUBE_CHANNEL_URL no configurado; no se puede resolver el ID.", "WARNING")
                        return None
                elif response.status != 200:
                    body = await response.text()
                    printlog(f"[YouTube] Error al consultar feed ({response.status}): {body[:220]}", "WARNING")
                    return None
                else:
                    xml_text = await response.text()
    except aiohttp.ClientError as exc:
        printlog(f"[YouTube] Error de red consultando feed: {exc}", "WARNING")
        return None

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        printlog(f"[YouTube] Feed XML invalido: {exc}", "WARNING")
        return None

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }

    entry = root.find("atom:entry", ns)
    if entry is None:
        return None

    video_id = (entry.findtext("yt:videoId", default="", namespaces=ns) or "").strip()
    title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
    published_at = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()

    link_el = entry.find("atom:link", ns)
    video_url = (link_el.get("href", "").strip() if link_el is not None else "")
    if not video_url and video_id:
        video_url = f"https://www.youtube.com/watch?v={video_id}"

    thumbnail_url = ""
    media_group = entry.find("media:group", ns)
    if media_group is not None:
        thumbnail_el = media_group.find("media:thumbnail", ns)
        if thumbnail_el is not None:
            thumbnail_url = thumbnail_el.get("url", "").strip()

    if not video_id or not title or not video_url:
        return None

    return {
        "video_id": video_id,
        "title": title,
        "video_url": video_url,
        "published_at": published_at,
        "thumbnail_url": thumbnail_url,
    }


async def poll_youtube_uploads(stop_check):
    """Monitorea el feed de YouTube y notifica a Discord cuando detecta un video nuevo."""
    _ensure_youtube_state_table()
    missing_config_warned = False
    monitor_started_logged = False
    first_probe_logged = False
    feature_disabled_logged = False

    while not stop_check():
        if not is_feature_enabled("FEATURE_YOUTUBE", True):
            if not feature_disabled_logged:
                printlog("[YouTube] Monitoreo deshabilitado por FEATURE_YOUTUBE=0.", "INFO")
                feature_disabled_logged = True
                monitor_started_logged = False
                first_probe_logged = False
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            continue

        feature_disabled_logged = False
        channel_id = _get_youtube_channel_id()
        interval = _get_youtube_poll_interval(default_seconds=600)

        if not channel_id:
            if not missing_config_warned:
                printlog("[YouTube] YOUTUBE_CHANNEL_ID no configurado. Se omite monitoreo.", "WARNING")
                missing_config_warned = True
            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            continue

        missing_config_warned = False

        if not monitor_started_logged:
            printlog(f"[YouTube] Monitor activo para canal {channel_id} (intervalo {interval}s).", "INFO")
            monitor_started_logged = True

        latest_video = await _fetch_latest_video(channel_id)
        if latest_video:
            last_video_id = _get_last_video_id(channel_id)
            current_video_id = latest_video["video_id"]

            # Primera ejecución: guarda estado sin enviar notificación retroactiva.
            if not last_video_id:
                _save_last_video(channel_id, current_video_id, latest_video.get("published_at"))
                printlog(f"[YouTube] Estado inicial establecido con video {current_video_id}.", "INFO")
            elif last_video_id != current_video_id:
                notified = await notify_youtube_video(
                    title=latest_video["title"],
                    video_url=latest_video["video_url"],
                    channel_url=_get_youtube_channel_url_for(channel_id),
                    published_at=latest_video.get("published_at"),
                    thumbnail_url=latest_video.get("thumbnail_url"),
                )
                if notified:
                    _save_last_video(channel_id, current_video_id, latest_video.get("published_at"))
                    printlog(f"[YouTube] Nuevo video detectado y notificado: {current_video_id}", "INFO")
                else:
                    printlog(f"[YouTube] Se detectó video nuevo pero no se pudo enviar a Discord: {current_video_id}", "WARNING")
            elif not first_probe_logged:
                printlog(f"[YouTube] Monitor OK sin novedades. Último video actual: {current_video_id}", "INFO")

            first_probe_logged = True
        elif not first_probe_logged:
            printlog("[YouTube] Monitor activo, pero el feed no devolvió entradas.", "WARNING")
            first_probe_logged = True

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break
