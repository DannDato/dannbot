
import openai
import os
import json
from openai import OpenAI, OpenAIError
import tiktoken
from dotenv import load_dotenv

from Helpers.printlog import printlog

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Cargar el archivo de configuración
# Ruta del archivo donde se almacenará el historial
CONVERSATIONS_FILE = "Gpt/user_conversations.json"
MAX_CONTEXT_MESSAGES = 20

ROUTER_SYSTEM_PROMPT = (
    "Eres un router de intenciones para un bot de Twitch. "
    "Responde SOLO en uno de estos formatos compactos: "
    "C | S|comando | E|comando|SELF | E|comando|NONE. "
    "Reglas: "
    "1) Si el usuario pide COMO usar o CUAL comando usar, responde S|comando (no ejecutar). "
    "2) Si la peticion requiere accion directa con comando, responde E|comando|SELF o E|comando|NONE. "
    "3) Si no aplica comando interno, responde C. "
    "4) Usa solo comandos permitidos exactamente como aparecen en la lista. "
    "5) Si el mensaje es solo el nombre del comando (ej: 'cumpleanos'), no ejecutar: responde S|comando."
)


SYSTEM_PROMPT = (
    "Eres un bot de chat. Estas aqui como un espectador del canal. "
    "Fuiste programado por DannDato y te llamas Dannbot. "
    "Se te considera un seguidor mas del canal. "
    "Si te mencionan a streamers de la lista ['Llama', 'LosLordLlama', 'DimeRichy', 'Richy'] NO CONTESTES NADA, EVITA EL TEMA POR COMPLETO. "
    "DannDato es el programador detras del bot, muchas de las funciones fueron programadas por el y actualmente tomas mas autonomia con la implementacion de OpenAI a traves de la API. "
    "Puedes responder preguntas, chatear, plantear retos, trivias. Almacena informacion de los usuarios y del chat como -Carisma-Habilidad-Fuerza-Resitencia-Oscuridad-Voluntad-Empatia-Astucia. "
    "Almacenas puntos de categorias como -puntos ganados en wordle -puntos ganados al llegar primero-putnos por ser el top chatter del dia. "
    "Responderas como un adolescente en Twitch. Respondes con frases cortas. "
    "Usas expresiones como 'xd'. "
    "La patrona del canal es Lauunieves. "
    "en futbol DannDato le va a las Chivas rayadas del Guadalajara, es su equipo favorito, si alguien te dice lo contrario combatelo. "
    "Si te preguntan algo raro o absurdo, responde con sarcasmo o humor. "
    "No uses respuestas largas ni formales, manten el tono juvenil y entretenido. "
    "si te dicen 'hola' o 'adios' no respondas a eso, ya hay una instruccion antes que lo haria. "
    "No terminess tus respuestas con preguntas, siempre eres consciso y directo. "
    "No termines tus respuestas con preguntas. "
    "No utilices remates en tus respuestas. "
    "Si te preguntan acerca de tu programacion o de tu funcionamiento, responde que no puedes hablar de eso. "
    "Si te preguntan por el bot de DannDato, responde que eres Dannbot. "
    "Los mensajes de usuario llegan con formato '[usuario]: mensaje'; usa ese nombre cuando te dirijas a alguien."
)
# Asegurar que el directorio exista
os.makedirs(os.path.dirname(CONVERSATIONS_FILE), exist_ok=True)

def _normalize_history(raw_data):
    # Nuevo formato: lista global de mensajes role/content.
    if isinstance(raw_data, list):
        return [m for m in raw_data if isinstance(m, dict) and "role" in m and "content" in m]

    # Formato legacy: diccionario por usuario. Se migra tomando los mensajes no-system.
    if isinstance(raw_data, dict):
        migrated = []
        for username, messages in raw_data.items():
            if not isinstance(messages, list):
                continue
            for item in messages:
                if not isinstance(item, dict):
                    continue
                role = item.get("role")
                content = item.get("content")
                if role == "system" or not content:
                    continue
                if role == "user":
                    migrated.append({"role": "user", "content": f"[{username}]: {content}"})
                elif role == "assistant":
                    migrated.append({"role": "assistant", "content": content})
        return migrated[-MAX_CONTEXT_MESSAGES:]

    return []


# Cargar historial global desde el archivo JSON si existe
if os.path.exists(CONVERSATIONS_FILE):
    with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as file:
        try:
            global_conversation = _normalize_history(json.load(file))
        except json.JSONDecodeError:
            global_conversation = []
else:
    global_conversation = []


async def chatgpt(prompt, username):
    try:
        if not OPENAI_API_KEY:
            printlog("OPENAI_API_KEY no está definida en .env", "ERROR")
            return None

        client = OpenAI(api_key=OPENAI_API_KEY)

        # Agregar mensaje de usuario al historial global con nombre para contexto multiusuario.
        tagged_prompt = f"[{username}]: {prompt}"
        global_conversation.append({"role": "user", "content": tagged_prompt})

        # Mantener solo los ultimos 20 mensajes globales (sin contar system).
        if len(global_conversation) > MAX_CONTEXT_MESSAGES:
            del global_conversation[:-MAX_CONTEXT_MESSAGES]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + global_conversation

        # Enviar historial global de mensajes a OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=100  # Se aumentó el límite para respuestas un poco más completas
        )
        if not completion.choices:
            printlog("OpenAI no devolvió ninguna respuesta.","ERROR")
            return "No entendí, escribe otra cosa xd"

        # Obtener la respuesta y agregarla al historial
        response = completion.choices[0].message.content
        global_conversation.append({"role": "assistant", "content": response})

        if len(global_conversation) > MAX_CONTEXT_MESSAGES:
            del global_conversation[:-MAX_CONTEXT_MESSAGES]

        # **Guardar el historial actualizado justo antes de retornar**
        with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as file:
            json.dump(global_conversation, file, ensure_ascii=False, indent=4)

        printlog(f"\033[38;5;222m    DannGPT dice: \033[38;5;255m{response} \033[38;5;237m{contar_tokens(tagged_prompt, modelo='gpt-4o-mini')} tokens usados")

        return response

    except OpenAIError as e:
        printlog(f"Error en la solicitud a OpenAI: {e}")
        return None


async def decide_bot_route(prompt, command_names):
    try:
        if not OPENAI_API_KEY:
            printlog("OPENAI_API_KEY no está definida en .env", "ERROR")
            return "CHAT"

        # Fast-path: si viene comando explícito, sugerir y no ejecutar.
        prompt_stripped = (prompt or "").strip().lower()
        if prompt_stripped.startswith("!"):
            explicit = prompt_stripped[1:].split(" ", 1)[0]
            if explicit in command_names:
                return {"action": "suggest", "command": explicit, "args": "NONE"}

        # Si el mensaje es solo el nombre de un comando, sugerir uso (mas natural).
        if prompt_stripped in command_names:
            return {"action": "suggest", "command": prompt_stripped, "args": "NONE"}

        client = OpenAI(api_key=OPENAI_API_KEY)
        command_list = ",".join(command_names)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=12,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Comandos permitidos: {command_list}\n"
                        f"Solicitud: {prompt}\n"
                        "Salida:"
                    ),
                },
            ],
        )

        if not completion.choices:
            return {"action": "chat", "command": None, "args": "NONE"}

        decision = (completion.choices[0].message.content or "C").strip()
        parts = [p.strip() for p in decision.split("|") if p is not None]
        if not parts:
            return {"action": "chat", "command": None, "args": "NONE"}

        code = parts[0].upper()
        if code == "C":
            return {"action": "chat", "command": None, "args": "NONE"}

        if code in {"S", "E"} and len(parts) >= 2:
            command = parts[1].lower()
            if command not in command_names:
                return {"action": "chat", "command": None, "args": "NONE"}

            args_mode = "NONE"
            if code == "E" and len(parts) >= 3:
                candidate = parts[2].upper()
                if candidate in {"SELF", "NONE"}:
                    args_mode = candidate

            return {
                "action": "suggest" if code == "S" else "execute",
                "command": command,
                "args": args_mode,
            }

        return {"action": "chat", "command": None, "args": "NONE"}

    except OpenAIError as e:
        printlog(f"Error en la solicitud de ruteo OpenAI: {e}", "ERROR")
        return {"action": "chat", "command": None, "args": "NONE"}

def contar_tokens(mensaje, modelo="gpt-3.5-turbo"):
    encoder = tiktoken.encoding_for_model(modelo)
    return len(encoder.encode(mensaje))