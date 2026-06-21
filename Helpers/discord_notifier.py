import os
from datetime import datetime
from pathlib import Path

import aiohttp

from Helpers.printlog import printlog
from Helpers.token_loader import load_token
from Helpers.feature_flags import is_feature_enabled


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
        printlog(f"[Discord] No se pudo cargar .env para webhooks: {exc}", "WARNING")


def _get_public_webhook_url() -> str:
    _load_env_file()
    return os.getenv("DISCORD_WEBHOOK", "").strip()


def _get_private_webhook_url() -> str:
    _load_env_file()
    return os.getenv("DISCORD_PRIVATE_WEBHOOK", "").strip()


def _get_subs_role_id() -> str:
    _load_env_file()
    return os.getenv("DISCORD_SUBS_ROLE_ID", "").strip()


def _get_twitch_channel_url(channel_name: str) -> str:
    _load_env_file()
    return os.getenv("TWITCH_CHANNEL_URL", "").strip() or f"https://twitch.tv/{channel_name}"


def _role_mention(role_id: str) -> str:
    return f"<@&{role_id}>" if role_id else ""


async def _send_webhook(payload: dict, *, public: bool = False) -> bool:
    if not is_feature_enabled("FEATURE_DISCORD", True):
        return False

    url = _get_public_webhook_url() if public else _get_private_webhook_url()
    if public and not is_feature_enabled("FEATURE_DISCORD_PUBLIC", True):
        return False
    if not public and not is_feature_enabled("FEATURE_DISCORD_PRIVATE", True):
        return False

    # Fallback: si falta webhook privado, intenta enviar al webhook publico.
    # Esto evita perder notificaciones cuando solo se configura DISCORD_WEBHOOK.
    if not public and not url:
        fallback_url = _get_public_webhook_url()
        if fallback_url:
            printlog("[Discord] DISCORD_PRIVATE_WEBHOOK no configurado; usando DISCORD_WEBHOOK como fallback.", "WARNING")
            url = fallback_url

    if not url:
        if public:
            printlog("[Discord] DISCORD_WEBHOOK no configurado; se omite envio publico.", "WARNING")
        else:
            printlog("[Discord] DISCORD_PRIVATE_WEBHOOK no configurado; se omite envio privado.", "WARNING")
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status in (200, 204):
                    return True

                body = await resp.text()
                printlog(f"[Discord] Error enviando webhook ({resp.status}): {body}", "WARNING")
                return False
    except aiohttp.ClientError as exc:
        printlog(f"[Discord] Error de red enviando webhook: {exc}", "WARNING")
        return False


async def _fetch_twitch_live_metadata(channel_name: str) -> dict:
    token_data = load_token()
    access_token = token_data.get("access_token")
    client_id = token_data.get("client_id")
    if not access_token or not client_id or not channel_name:
        return {}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-ID": client_id,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers,
                params={"user_login": channel_name},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                stream_payload = await resp.json(content_type=None) if resp.status == 200 else {}

            async with session.get(
                "https://api.twitch.tv/helix/users",
                headers=headers,
                params={"login": channel_name},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                user_payload = await resp.json(content_type=None) if resp.status == 200 else {}

        stream_data = (stream_payload or {}).get("data") or []
        user_data = (user_payload or {}).get("data") or []
        stream = stream_data[0] if stream_data else {}
        user = user_data[0] if user_data else {}

        thumbnail_url = (stream.get("thumbnail_url") or "").replace("{width}", "1280").replace("{height}", "720")
        return {
            "title": stream.get("title") or "",
            "category_name": stream.get("game_name") or "",
            "started_at": stream.get("started_at") or "",
            "thumbnail_url": thumbnail_url,
            "profile_image_url": user.get("profile_image_url") or "",
            "display_name": user.get("display_name") or channel_name,
        }
    except aiohttp.ClientError as exc:
        printlog(f"[Discord] No se pudo obtener metadata de Twitch: {exc}", "WARNING")
        return {}


async def send_discord_embed(title: str, description: str, *, color: int = 0x5865F2, fields: list | None = None, public: bool = False, content: str | None = None, url: str | None = None, thumbnail_url: str | None = None, image_url: str | None = None, author_name: str | None = None, author_icon_url: str | None = None) -> bool:
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if url:
        embed["url"] = url

    if fields:
        embed["fields"] = fields

    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url}

    if image_url:
        embed["image"] = {"url": image_url}

    if author_name:
        embed["author"] = {"name": author_name}
        if author_icon_url:
            embed["author"]["icon_url"] = author_icon_url

    payload = {
        "embeds": [embed],
    }

    if content:
        payload["content"] = content

    return await _send_webhook(payload, public=public)


async def notify_stream_online(channel_name: str, channel_url: str | None = None):
    if not is_feature_enabled("FEATURE_STREAM_ONLINE_NOTIFY", True):
        return

    channel_url = (channel_url or _get_twitch_channel_url(channel_name)).strip()
    metadata = await _fetch_twitch_live_metadata(channel_name)
    display_name = metadata.get("display_name") or channel_name
    stream_title = metadata.get("title") or "Directo en progreso"
    fields = []
    if metadata.get("title"):
        fields.append({"name": "Titulo", "value": metadata["title"][:1024], "inline": False})
    if metadata.get("category_name"):
        fields.append({"name": "Categoria", "value": metadata["category_name"][:1024], "inline": True})
    if metadata.get("started_at"):
        started_at = metadata["started_at"].replace("T", " ").replace("Z", " UTC")
        fields.append({"name": "Inicio", "value": started_at[:1024], "inline": True})
    fields.append({"name": "Ver directo", "value": channel_url, "inline": False})

    await send_discord_embed(
        title=f"{display_name} está en vivo",
        description=f"Ven y no pierdas tu racha! Que crees que suceda hoy? ",
        color=0x57F287,
        fields=fields or None,
        url=channel_url,
        thumbnail_url=metadata.get("profile_image_url"),
        image_url=metadata.get("thumbnail_url"),
        author_name=display_name,
        author_icon_url=metadata.get("profile_image_url"),
        content=f"\n\n 🟢 Ya comenzó el stream! ➡️ {channel_url} @everyone",
        public=True,
    )


async def notify_new_follow(username: str):
    if not is_feature_enabled("FEATURE_NOTIFY_FOLLOW", True):
        return

    await send_discord_embed(
        title="[Twitch] Nuevo seguidor",
        description=f"@{username} comenzo a seguir el canal de twitch!.",
        color=0x800080,
    )


async def notify_bits(username: str, bits: int, message: str = ""):
    if not is_feature_enabled("FEATURE_NOTIFY_BITS", True):
        return

    fields = [{"name": "Bits", "value": str(bits), "inline": True}]
    if message:
        fields.append({"name": "Mensaje", "value": message[:400], "inline": False})

    await send_discord_embed(
        title="Nueva donacion de bits",
        description=f"@{username} envio bits al canal.",
        color=0xFAA61A,
        fields=fields,
    )


async def notify_sub(username: str, tier: str, gift: bool = False, total_gifted: int | None = None):
    if not is_feature_enabled("FEATURE_NOTIFY_SUBS", True):
        return

    role_ping = _role_mention(_get_subs_role_id())
    fields = [
        {"name": "Tier", "value": tier or "Desconocido", "inline": True},
        {"name": "Tipo", "value": "Regalo" if gift else "Nueva sub", "inline": True},
    ]

    if total_gifted:
        fields.append({"name": "Subs regaladas", "value": str(total_gifted), "inline": True})

    await send_discord_embed(
        title="Nueva suscripcion",
        description=f"@{username} se suscribio al canal.",
        color=0xEB459E,
        fields=fields,
        content=role_ping if role_ping else None,
    )


async def notify_critical_error(source: str, detail: str):
    if not is_feature_enabled("FEATURE_NOTIFY_CRITICAL", True):
        return

    await send_discord_embed(
        title="Error critico DannBot",
        description=f"Fuente: {source}\nDetalle: {detail[:800]}",
        color=0xED4245,
    )


async def notify_post_stream_summary(summary: dict):
    if not is_feature_enabled("FEATURE_STREAM_SUMMARY", True):
        return

    followers = int(summary.get("followers", 0) or 0)
    bits = int(summary.get("bits", 0) or 0)
    subs = int(summary.get("subs", 0) or 0)
    messages = int(summary.get("messages", 0) or 0)
    users = int(summary.get("users", 0) or 0)
    money = int(summary.get("money", 0) or 0)
    previous = summary.get("previous") or {}

    def _trend(current: int, prev: int | None) -> tuple[str, int]:
        if prev is None:
            return "•", 0
        delta = current - prev
        if delta > 0:
            return "↑", delta
        if delta < 0:
            return "↓", delta
        return "→", delta

    def _bar(current: int, prev: int | None, width: int = 12) -> str:
        reference = max(current, prev or 0, 1)
        filled = int(round((current / reference) * width))
        filled = max(0, min(width, filled))
        return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"

    def _fmt_metric(label: str, current: int, prev: int | None) -> dict:
        arrow, delta = _trend(current, prev)
        delta_text = f"{delta:+}" if prev is not None else "n/a"
        value = f"**{current}**  {arrow} ({delta_text})\n`{_bar(current, prev)}`"
        return {"name": label, "value": value, "inline": True}

    prev_followers = previous.get("followers")
    prev_subs = previous.get("subs")
    prev_bits = previous.get("bits")
    prev_messages = previous.get("messages")
    prev_users = previous.get("users")
    prev_money = previous.get("money")

    # Color del embed según rendimiento general del stream
    score = followers + subs * 5 + bits // 100 + messages // 200
    if score >= 40:
        color = 0x57F287  # verde
    elif score >= 20:
        color = 0xFEE75C  # amarillo
    else:
        color = 0x5865F2  # azul

    fields = [
        _fmt_metric("👥 Followers", followers, prev_followers),
        _fmt_metric("🎉 Subs", subs, prev_subs),
        _fmt_metric("💎 Bits", bits, prev_bits),
        _fmt_metric("💬 Mensajes", messages, prev_messages),
        _fmt_metric("🧑‍🤝‍🧑 Usuarios", users, prev_users),
        _fmt_metric("💵 Estimado USD", money, prev_money),
    ]

    top_chatter = summary.get("top_chatter")
    if top_chatter:
        fields.append({"name": "🏆 Top chatter", "value": f"@{top_chatter}", "inline": False})

    fields.append(
        {
            "name": "📊 Resumen rápido",
            "value": (
                f"`Impacto:` {'ALTO' if score >= 40 else 'MEDIO' if score >= 20 else 'BAJO'}\n"
                f"`Engagement:` {messages} mensajes / {users} usuarios\n"
                f"`Comparativa:` {'vs stream anterior' if previous else 'sin stream anterior para comparar'}"
            ),
            "inline": False,
        }
    )

    await send_discord_embed(
        title="📈 Resumen final del stream",
        description="Stream cerrado correctamente. Aquí van los números clave:",
        color=color,
        fields=fields,
    )


async def notify_daily_birthdays(usernames: list[str], *, offline: bool = False):
    if not is_feature_enabled("FEATURE_BIRTHDAYS_DISCORD", True):
        return

    if not usernames:
        return

    mentions = ", ".join([f"@{username}" for username in usernames])
    if len(usernames) == 1:
        description = f"\n\n💜 Hoy celebramos el cumpleaños de {mentions}."
    else:
        description = f"\n\n💜 Hoy celebramos los cumpleaños de {mentions}."

    if offline:
        description += f" Aunque no hay stream en este momento, no queríamos dejar pasar la felicitación. \n\n\n #FELIZCUMPLEAÑOS 🥳"

    await send_discord_embed(
        title="🎊 Cumpleaños del día 🎂",
        description=description,
        color=0xF1C40F,
        public=True,
    )


async def notify_youtube_video(
    *,
    title: str,
    video_url: str,
    channel_url: str | None = None,
    published_at: str | None = None,
    thumbnail_url: str | None = None,
)-> bool:
    if not is_feature_enabled("FEATURE_YOUTUBE", True):
        return False

    fields = [{"name": "Ver video", "value": video_url, "inline": False}]
    if channel_url:
        fields.append({"name": "Canal", "value": channel_url, "inline": False})
    if published_at:
        fields.append({"name": "Publicado", "value": published_at.replace("T", " ").replace("Z", " UTC")[:1024], "inline": True})

    return await send_discord_embed(
        title="📺 Nuevo video en YouTube",
        description=title[:1024],
        color=0xFF0000,
        fields=fields,
        url=video_url,
        image_url=thumbnail_url,
        content=f"🎬 Video nuevo publicado: {video_url}",
        public=True,
    )
