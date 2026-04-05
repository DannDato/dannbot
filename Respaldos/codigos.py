if username not in ('streamelements','danndato','nightbot'):
    # Obtener la fecha actual para el timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")  # Nombre del archivo basado en la fecha
    file_path = os.path.join(os.path.dirname(__file__), "chat_history",'users', f"{date_str}_joined_users.txt")

    # Crear el directorio 'stream_history' si no existe
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Validar si el archivo existe y escribir el registro
    try:
        with open(file_path, "a") as file:  # El modo 'a' crea el archivo si no existe
            file.write(f"{timestamp} - {username}\n")
    except Exception as e:
        print(f"Error al guardar el usuario: {e}")




def read_save_chat(message):
    if message.author:
            autor = message.author.name
            mensaje = message.content
            
            # Obtener la fecha actual
            current_date = datetime.now().strftime("%Y-%m-%d")
            timestamp = int(datetime.now().timestamp())  # Timestamp en segundos

            # Crear el diccionario con la información del mensaje
            message_data = {
                "timestamp": timestamp,
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": autor,
                "message": mensaje
            }

            # Ruta del archivo JSON para el día actual
            json_file_path = os.path.join(chat_history_folder, f"{current_date}.json")

            # Verificar si el archivo ya existe
            if os.path.exists(json_file_path):
                # Si existe, agregar el nuevo mensaje al archivo
                with open(json_file_path, 'r+', encoding='utf-8') as file:
                    chat_history = json.load(file)
                    chat_history.append(message_data)
                    # Volver a guardar el archivo con los mensajes actualizados
                    file.seek(0)  # Regresar al inicio del archivo
                    json.dump(chat_history, file, indent=4)
            else:
                # Si no existe, crear un nuevo archivo con el primer mensaje
                with open(json_file_path, 'w', encoding='utf-8') as file:
                    chat_history = [message_data]  # Crear lista con el primer mensaje
                    json.dump(chat_history, file, indent=4)

            # Imprimir el mensaje en consola
            print(f'{message_data["datetime"]} | {message_data["user"]}: {message_data["message"]}')
            # Procesar cualquier comando del bot


async def update_global_stats(stat_category, user, value):
    """
    Actualiza las estadísticas globales.
    :param stat_category: Categoría de la estadística (ej. 'wordle_wins', 'top_chatter')
    :param user: Nombre del usuario
    :param value: Cantidad a incrementar
    """
    print("categoria")
    # Cargar estadísticas actuales
    with open(channel_file, 'r') as file:
        stats = json.load(file)
    # Verificar que la categoría existe
    if stat_category not in stats:
        stats[stat_category] = {}
    # Actualizar el valor del usuario en la categoría
    user = normalize_username(user)
    if user in stats[stat_category]:
        stats[stat_category][user] += value
    else:
        stats[stat_category][user] = value

    # Guardar las estadísticas actualizadas
    with open(channel_file, 'w') as file:
        json.dump(stats, file, indent=4)




    # Comando para mostrar estadísticas globales de Wordle
    @bot.command(name='wordlestats')
    async def wordlestats(ctx):
        # Obtener estadísticas de Wordle
        ranking = get_stats("wordle_wins")
        if not ranking:
            await ctx.send("[BOT] - No hay estadísticas de Wordle todavía.")
            return
        # Crear un mensaje con el ranking de ganadores
        ranking_msg = ", ".join([f"@{user} ({wins})" for user, wins in ranking])
        await ctx.send(f'[BOT] - Las estadísticas de Wordle [🔥TOP 5]:')
        await ctx.send(f'{ranking_msg}')