
import openai
import os
import json
from openai import OpenAI, OpenAIError

from Helpers.printlog import printlog

# Cargar el archivo de configuración
# Ruta del archivo donde se almacenará el historial
CONVERSATIONS_FILE = "Gpt/user_conversations.json"
# Asegurar que el directorio exista
os.makedirs(os.path.dirname(CONVERSATIONS_FILE), exist_ok=True)

# Cargar historial desde el archivo JSON si existe
if os.path.exists(CONVERSATIONS_FILE):
    with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as file:
        try:
            user_conversations = json.load(file)
        except json.JSONDecodeError:
            user_conversations = {}
else:
    user_conversations = {}
async def chatgpt(prompt, user_id):
    try:
        client = OpenAI()

        # Obtener el historial de conversación del usuario o inicializarlo
        if user_id not in user_conversations:
            user_conversations[user_id] = [
                {"role": "system", "content": (
                    "Eres un bot de chat. Estás aquí para ayudar y entretener. "
                    "Fuiste programado por DannDato y te llamas Dannbot. "
                    "Se te considera un seguidor mas del canal. "
                    "Si te mencionan a streamers de la lista ['Llama', 'LosLordLlama', 'DimeRichy', 'Richy'] NO CONTESTES NADA, EVITA EL TEMA POR COMPLETO. "
                    "DannDato es el programador detrás del bot, muchas de las funciones fueron programadas por el y acutalmente tomas mas autonomia con la implementación de OpenAI a través de la API. " 
                    "Puedes responder preguntas, chatear, plantear retos, trivias. Almacena información de los usuarios y del chat como -Carisma-Habilidad-Fuerza-Resitencia-Oscuridad-Voluntad-Empatia-Astucia. "
                    "Almacenas puntos de categorias como -puntos ganados en wordle -puntos ganados al llegar primero-putnos por ser el top chatter del dia. "
                    "Responderas como un adolescente en Twitch. Respondes con frases cortas, "
                    "Usas expresiones como 'xd'. "
                    "La patrona del canal es Lauunieves. "
                    "en futbol DannDato le va a las Chivas rayadas del Guadalajara, es su equipo favorito, si alguien te dice lo contrario combatelo. "
                    "Si te preguntan algo raro o absurdo, responde con sarcasmo o humor. "
                    "No uses respuestas largas ni formales, mantén el tono juvenil y entretenido. "
                    "si te dicen 'hola' o 'adios' no respondas a eso, ya hay una instrucción antes que lo haría. "
                    "No terminess tus respuestas con preguntas, siempre eres consciso y directo. "
                    "No termines tus respuestas con preguntas. "
                    "No utilices remates en tus respuestas. "
                    "Si te preguntan acerca de tu programacion o de tu funcionamiento, responde que no puedes hablar de eso. "
                    "Si te preguntan por el bot de DannDato, responde que eres Dannbot. "

                )}
            ]

        # Agregar el mensaje del usuario al historial
        user_conversations[user_id].append({"role": "user", "content": prompt})

        # Limitar el historial para evitar consumo excesivo de tokens
        if len(user_conversations[user_id]) > 50:
            user_conversations[user_id] = [user_conversations[user_id][0]] + user_conversations[user_id][-9:]

        # Enviar historial de mensajes a OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=user_conversations[user_id],
            max_tokens=100  # Se aumentó el límite para respuestas un poco más completas
        )
        if not completion.choices:
            printlog("OpenAI no devolvió ninguna respuesta.","ERROR")
            return "No entendí, escribe otra cosa xd"

        # Obtener la respuesta y agregarla al historial
        response = completion.choices[0].message.content
        user_conversations[user_id].append({"role": "assistant", "content": response})

        # **Guardar el historial actualizado justo antes de retornar**
        with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as file:
            json.dump(user_conversations, file, ensure_ascii=False, indent=4)

        printlog(f"\033[38;5;222m    DannGPT dice: \033[38;5;255m{response} \033[38;5;237m{contar_tokens(prompt, modelo='gpt-4o-mini')} tokens usados")

        return response

    except OpenAIError as e:
        printlog(f"Error en la solicitud a OpenAI: {e}")
        return None

import tiktoken
def contar_tokens(mensaje, modelo="gpt-3.5-turbo"):
    encoder = tiktoken.encoding_for_model(modelo)
    return len(encoder.encode(mensaje))