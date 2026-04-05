# patch/dummy_ctx.py
from types import SimpleNamespace
from twitchio.ext import commands


def create_dummy_ctx(bot, data):
    event = data.get("payload", {}).get("event", {})

    user_id = event.get("chatter_user_id")
    user_name = event.get("chatter_user_login")
    display_name = event.get("chatter_user_name")
    message_content = event.get("message", {}).get("text", "")

    badges_raw = event.get("badges", [])
    badges = {badge.get("set_id"): badge.get("id") for badge in badges_raw if badge.get("set_id") and badge.get("id")}

    # Crear una clase simple para simular el autor
    author = SimpleNamespace(
        id=user_id,
        name=user_name,
        display_name=display_name,
        is_mod="moderator" in badges,
        is_subscriber="subscriber" in badges,
        # is_broadcaster=user_name.lower() == bot.nick.lower(),
        badges=badges,
    )

    # Crear una clase simple para simular el canal
    channel = SimpleNamespace(
        # name=bot.nick,
        send=lambda message: bot._ws.send_privmsg(bot.nick, message),
    )

    # Crear el objeto de mensaje simulado
    message = SimpleNamespace(
        content=message_content,
        author=author,
        channel=channel,
        echo=False,
    )

    # Crear el contexto simulado
    ctx = commands.Context(
        # message=message,
        bot=bot,
        # command=None,
        # content=message_content,
        # prefix=bot.prefix if hasattr(bot, 'prefix') else '!',
        payload=data,
    )

    return ctx
