from twitchio.ext import commands
from types import SimpleNamespace

from Helpers.helpers import is_authorized
from Helpers.helpers_admin import end_stream, start_stream, reset_current_stream_stats
from Helpers.helpers import safe_int
from Handlers.handlers_follow import handle_follow
from Handlers.handlers_cheer import handle_cheer
from Handlers.handlers_subs import handle_sub
from Helpers.printlog import printlog


class admin_commands(commands.Component):
    def __init__(self, bot: commands.AutoBot):
        super().__init__()
        self.bot = bot

    def _build_test_user(self, username: str, fallback_id: int) -> SimpleNamespace:
        user_id = abs(hash(username)) % 900000000 + 100000000
        return SimpleNamespace(name=username, id=user_id or fallback_id)

    def _build_test_broadcaster(self, ctx) -> SimpleNamespace:
        broadcaster = getattr(ctx, "broadcaster", None)
        broadcaster_id = safe_int(getattr(broadcaster, "id", None)) or safe_int(getattr(ctx.chatter, "id", 0))
        broadcaster_name = getattr(broadcaster, "name", None) or getattr(ctx.chatter, "name", "danndato")
        return SimpleNamespace(id=broadcaster_id, name=broadcaster_name)

    @commands.command(name='ini')
    async def ini(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        stream_started = await start_stream()
        if stream_started:
            await ctx.send(' [BOT] - 🤖 Excelente! Se ha iniciado el directo correctamente en la base de datos... ¿Estan listos? 🟢')
        else:
            await ctx.send(' [BOT] - 🟡 Ya existe un stream en proceso...')

    @commands.command(name='end')
    async def end(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        stream_ended = await end_stream()
        if stream_ended:
            await ctx.send(' [BOT] - 🤖 Listo, se ha terminado el stream. Gracias por todo! nos vemos en el siguiente directo... Chao ❤️')
        else:
            await ctx.send(' [BOT] - 🔴 No se puede finalizar un stream que no se ha iniciado...')

    @commands.command(name='streamtest', aliases=["st"])
    async def streamtest(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        stream_started = await start_stream()
        if stream_started:
            await ctx.send("[BOT] - 🧪 Stream de prueba iniciado en base de datos. Ya puedes testear comandos.")
        else:
            await ctx.send("[BOT] - 🟡 Ya hay un stream activo en la base de datos, no pude crear uno de prueba.")

    @commands.command(name='streamtestend', aliases=["stend"])
    async def streamtestend(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        stream_ended = await end_stream()
        if stream_ended:
            await ctx.send("[BOT] - 🧪 Stream de prueba finalizado en base de datos.")
        else:
            await ctx.send("[BOT] - 🔴 No hay stream activo para finalizar.")

    @commands.command(name='resetstream', aliases=["rst"])
    async def resetstream(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        ok, deleted_rows = await reset_current_stream_stats()
        if ok:
            await ctx.send(f"[BOT] - 🧪 Stream de prueba reseteado. Registros limpiados: {deleted_rows}.")
        else:
            await ctx.send("[BOT] - 🔴 No hay stream activo para resetear.")

    @commands.command(name='restart')
    async def restart(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        await ctx.send("[BOT] - OK... un momento que me estoy reiniciando 😰")
        await self.bot.restart_process("[Monitor] - Reiniciando bot por comando autorizado...")

    @commands.command(name='status', aliases=["estas", "estas?", "hey"])
    async def botstatus(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        printlog("Chequeando estado del bot...")
        try:
            if not self.bot.connected:
                await ctx.send("[BOT] - Algo anda raro... me voy a reiniciar, pérate")
                await self.bot.restart_process("[Monitor] - WebSocket desconectado. Reiniciando bot...")
            else:
                await ctx.send("[BOT] - Todo joya 😎")
                printlog("DannDato en linea", "\033[38;5;51m")
        except Exception as e:
            printlog("Algo ha ocurrido, reiniciando bot...")
            await ctx.send("[BOT] - Ni supe que hacer, imaginate...")
            await self.bot.restart_process(f"[ Monitor ] - Error en chequeo de salud: {e}. Reiniciando...")

    @commands.command(name='testfollow')
    async def testfollow(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        parts = ctx.message.text.strip().split()
        target_name = parts[1].lstrip('@').lower() if len(parts) > 1 else ctx.chatter.name.lower()

        payload = SimpleNamespace(
            user=self._build_test_user(target_name, safe_int(ctx.chatter.id)),
            broadcaster=self._build_test_broadcaster(ctx),
            followed_at=None,
        )

        await handle_follow(self.bot, payload)
        await ctx.send(f"[BOT] - Test FOLLOW disparado para @{target_name} ✅")

    @commands.command(name='testcheer')
    async def testcheer(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        parts = ctx.message.text.strip().split(maxsplit=3)
        target_name = parts[1].lstrip('@').lower() if len(parts) > 1 else ctx.chatter.name.lower()
        bits = safe_int(parts[2]) if len(parts) > 2 else 100
        message = parts[3] if len(parts) > 3 else "Test de cheer manual"
        if bits <= 0:
            bits = 1

        payload = SimpleNamespace(
            user=self._build_test_user(target_name, safe_int(ctx.chatter.id)),
            broadcaster=self._build_test_broadcaster(ctx),
            bits=bits,
            message=message,
        )

        await handle_cheer(self.bot, payload)
        await ctx.send(f"[BOT] - Test CHEER disparado para @{target_name} con {bits} bits ✅")

    @commands.command(name='testsub')
    async def testsub(self, ctx):
        if not is_authorized(ctx):
            await ctx.send("[BOT] - Hey, ese comando es solo para usuarios autorizados 😑")
            return

        parts = ctx.message.text.strip().split(maxsplit=3)
        target_name = parts[1].lstrip('@').lower() if len(parts) > 1 else ctx.chatter.name.lower()
        tier = parts[2] if len(parts) > 2 else "1000"
        gift = False
        if len(parts) > 3:
            gift = parts[3].strip().lower() in {"1", "true", "si", "yes", "gift"}

        payload = SimpleNamespace(
            user=self._build_test_user(target_name, safe_int(ctx.chatter.id)),
            broadcaster=self._build_test_broadcaster(ctx),
            gift=gift,
            tier=tier,
        )

        await handle_sub(self.bot, payload)
        await ctx.send(
            f"[BOT] - Test SUB disparado para @{target_name} (tier {tier}{', gift' if gift else ''}) ✅"
        )
