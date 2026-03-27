import re
import unicodedata
import difflib

import aiohttp

from Helpers.token_loader import load_token
from Helpers.printlog import printlog


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
