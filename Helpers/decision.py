import re
import unicodedata

from Helpers.chatgpt import decide_bot_route


def normalize_route_text(text):
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9_!?@\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_alias_to_canonical_map(bot_commands):
    alias_to_canonical = {}
    for cmd in bot_commands.values():
        main_name = getattr(cmd, "name", None)
        if not main_name:
            continue
        canonical = str(main_name).strip().lower()
        all_names = [canonical] + [str(a).strip().lower() for a in (getattr(cmd, "aliases", []) or [])]
        for raw_name in all_names:
            normalized = normalize_route_text(raw_name)
            if normalized:
                alias_to_canonical[normalized] = canonical
    return alias_to_canonical


def quick_route(prompt, alias_to_canonical):
    normalized = normalize_route_text(prompt)
    if not normalized:
        return None

    # Si manda un comando directo o solo nombre de comando, sugerir y no ejecutar.
    if normalized.startswith("!"):
        token = normalize_route_text(normalized[1:].split(" ", 1)[0])
        cmd = alias_to_canonical.get(token)
        if cmd:
            return {"action": "suggest", "command": cmd, "args": "NONE"}

    only_token = normalize_route_text(normalized.split(" ", 1)[0])
    if normalized == only_token and only_token in alias_to_canonical:
        return {"action": "suggest", "command": alias_to_canonical[only_token], "args": "NONE"}

    ask_how = any(phrase in normalized for phrase in (
        "como", "cual", "que comando", "como era", "como hago", "como ver", "para ver"
    ))

    ask_self_info = any(phrase in normalized for phrase in (
        "mi", "mis", "yo", "tengo", "soy", "cuanto", "cuantos", "cual es"
    ))

    # Intenciones frecuentes sin gastar tokens.
    if "cumple" in normalized:
        cmd = alias_to_canonical.get("cumpleanos") or alias_to_canonical.get("cumple")
        if cmd:
            return {"action": "suggest" if ask_how else "execute", "command": cmd, "args": "SELF"}

    if "wordle" in normalized and any(k in normalized for k in ("punto", "score", "cuanto", "cuantos", "tengo")):
        cmd = alias_to_canonical.get("wordlescore") or alias_to_canonical.get("wordlepuntos")
        if cmd:
            return {"action": "suggest" if ask_how else "execute", "command": cmd, "args": "SELF"}

    if any(k in normalized for k in ("primero", "first")):
        cmd = alias_to_canonical.get("primero")
        if cmd:
            return {"action": "suggest" if ask_how else "execute", "command": cmd, "args": "NONE"}

    if any(k in normalized for k in ("segundo", "second")):
        cmd = alias_to_canonical.get("segundo")
        if cmd:
            return {"action": "suggest" if ask_how else "execute", "command": cmd, "args": "NONE"}

    if any(k in normalized for k in ("nivel", "level")):
        cmd = alias_to_canonical.get("nivel")
        if cmd:
            return {
                "action": "suggest" if ask_how else "execute",
                "command": cmd,
                "args": "SELF" if ask_self_info else "NONE",
            }

    if any(k in normalized for k in ("player", "jugador")):
        cmd = alias_to_canonical.get("player") or alias_to_canonical.get("jugador")
        if cmd:
            return {
                "action": "suggest" if ask_how else "execute",
                "command": cmd,
                "args": "SELF" if ask_self_info else "NONE",
            }

    if any(k in normalized for k in ("estadistica", "estadisticas", "stats", "perfil")):
        cmd = alias_to_canonical.get("player") or alias_to_canonical.get("jugador")
        if cmd:
            return {
                "action": "suggest" if ask_how else "execute",
                "command": cmd,
                "args": "SELF",
            }

    
    return None


async def resolve_bot_route(prompt, bot_commands):
    alias_to_canonical = build_alias_to_canonical_map(bot_commands)
    route = quick_route(prompt, alias_to_canonical)
    if route is None:
        command_names = sorted(alias_to_canonical.keys())
        route = await decide_bot_route(prompt, command_names)

    raw_command = normalize_route_text(route.get("command")) if route.get("command") else None
    target_command = alias_to_canonical.get(raw_command, raw_command)

    return {
        "action": route.get("action"),
        "command": target_command,
        "args": route.get("args", "NONE"),
    }
