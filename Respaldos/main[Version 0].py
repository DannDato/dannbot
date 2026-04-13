from twitchio.ext import commands
import json
import os
from datetime import datetime
import random
import time 

# Ruta del archivo token.json para obtener credenciales
token_path = os.path.join(os.path.dirname(__file__), 'token.json')
access_token = None

# Ruta para el archivo de estadísticas globales
stats_path = os.path.join(os.path.dirname(__file__), 'stats.json')
if not os.path.exists(stats_path):
    with open(stats_path, 'w') as file:
        json.dump({}, file, indent=4)  # Crear un archivo vacío

# Ruta para la carpeta de almacenamiento, datos por stream
history_dir = os.path.join(os.path.dirname(__file__), 'stream_history')
os.makedirs(history_dir, exist_ok=True)  # Crea la carpeta si no existe

# Ruta del archivo donde se guardarán los mensajes
chat_history_folder = os.path.join(os.path.dirname(__file__), 'chat_history')
if not os.path.exists(chat_history_folder):
    os.makedirs(chat_history_folder)


# Leer el archivo de datos de oAuth para nivel de administrador en mi canal
try:
    with open(token_path, 'r') as file:
        token_data = json.load(file)  # Carga el contenido del archivo en un diccionario
        access_token = token_data.get("access_token")  # Obtén el token de acceso
        client_id = token_data.get("client_id")  # Obtén el Client ID
        initial_channels = token_data.get("initial_channels")  # Canales iniciales
        broadcaster_id = token_data.get("broadcaster_id")  # ID del canal

        if not access_token or not client_id or not broadcaster_id:
            print(f"Error: Falta 'access_token', 'client_id' o 'broadcaster_id' en {token_path}.")
            exit()

except FileNotFoundError:
    print(f"Error: No se encontró el archivo {token_path}.")
    exit()
except json.JSONDecodeError:
    print(f"Error: El archivo {token_path} no tiene un formato JSON válido.")
    exit()

print("Token cargado correctamente.")


#____________________ INICIAN FUNCIONES _________________________________
#__________________ Funcion que valida al primer usuario en usar el comando !primero_________________
async def handle_first_user(ctx):
    # Obtener la fecha y hora actual
    current_date = datetime.now().strftime('%Y-%m-%d')  # Formato de fecha YYYY-MM-DD
    file_path = os.path.join(history_dir, f'{current_date}.json')  # Ruta del archivo basado en la fecha

    # Verificar si el archivo ya existe
    if os.path.exists(file_path):
        # Si el archivo existe, cargamos la información existente
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Verificar si ya se ha registrado el primer usuario
        if 'first_user' in data:
            await ctx.send(f'Lo siento @{ctx.author.name} pero @{data["first_user"]} fue el primero en ejecutar el comando.')
        else:
            # Si el primer usuario no está registrado, lo agregamos
            data['first_user'] = ctx.author.name
            data['first_user_time'] = datetime.now().strftime('%H:%M:%S')  # Hora de cuando ejecutó el comando
            
            # Guardamos los cambios en el archivo
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
            await ctx.send(f'¡Apoco si llegaste primero @{ctx.author.name}? 👀')
    else:
        # Si el archivo no existe, creamos uno nuevo con la información del primer usuario
        data = {
            'stream_start_time': datetime.now().strftime('%H:%M:%S'),  # Hora en que comenzó el stream
            'first_user': ctx.author.name,  # Primer usuario
            'first_user_time': datetime.now().strftime('%H:%M:%S')  # Hora de cuando ejecutó el comando
        }
        
        # Guardar la nueva información en el archivo
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

        await ctx.send(f'¡Apoco si llegaste primero @{ctx.author.name}? 👀')


#__________________ Funcion que valida al primer usuario en usar el comando !primero_________________
def update_global_stats(stat_category, user, value=1):
    """
    Actualiza las estadísticas globales.
    :param stat_category: Categoría de la estadística (ej. 'wordle_wins', 'top_chatter')
    :param user: Nombre del usuario
    :param value: Cantidad a incrementar
    """
    # Cargar estadísticas actuales
    with open(stats_path, 'r') as file:
        stats = json.load(file)

    # Asegurar que la categoría existe
    if stat_category not in stats:
        stats[stat_category] = {}

    # Actualizar el valor del usuario en la categoría
    if user in stats[stat_category]:
        stats[stat_category][user] += value
    else:
        stats[stat_category][user] = value

    # Guardar las estadísticas actualizadas
    with open(stats_path, 'w') as file:
        json.dump(stats, file, indent=4)

#__________________ Funcion para anotarle un punto al jugador de wordle ganador _________________
def update_wordle_winner(user):
    """
    Actualiza las estadísticas de ganadores de Wordle.
    :param user: Nombre del usuario que ganó.
    """
    # Cargar estadísticas actuales
    with open(stats_path, 'r') as file:
        stats = json.load(file)

    # Asegurar que la categoría 'wordle_wins' existe
    if 'wordle_wins' not in stats:
        stats['wordle_wins'] = {}

    # Actualizar el valor del usuario en la categoría
    if user in stats['wordle_wins']:
        stats['wordle_wins'][user] += 1
    else:
        stats['wordle_wins'][user] = 1

    # Verificar si el usuario alcanzó 5 puntos
    if stats['wordle_wins'][user] >= 5:
        del stats['wordle_wins'][user]  # Eliminar al usuario de las estadísticas
        with open(stats_path, 'w') as file:
            json.dump(stats, file, indent=4)
        return True  # Indicar que ganó una suscripción

    # Guardar las estadísticas actualizadas
    with open(stats_path, 'w') as file:
        json.dump(stats, file, indent=4)
    return False  # Indicar que no ha alcanzado los 5 puntos aún


def get_wordle_stats():
    """
    Obtiene y muestra las estadísticas de ganadores de Wordle ordenadas por mayor cantidad de victorias.
    Solo muestra el top 3 de los usuarios.
    """
    with open(stats_path, 'r') as file:
        stats = json.load(file)

    wordle_stats = stats.get('wordle_wins', {})
    sorted_stats = sorted(wordle_stats.items(), key=lambda x: x[1], reverse=True)
    top_3 = sorted_stats[:3]  # Obtener solo el top 3

    print("Top 3 Ganadores de Wordle:")
    for i, (user, wins) in enumerate(top_3, start=1):
        print(f"{i}. {user}: {wins} victoria(s)")

    return top_3



# Crea la clase del bot heredando de commands.Bot
class ddpyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            token=access_token,
            prefix='!',  # El prefijo para los comandos
            initial_channels=initial_channels if isinstance(initial_channels, list) else [initial_channels]
        )

    # _____________________ INICIALIZACION DEL BOT _______________________
    async def event_ready(self):
        print(f'Bot conectado como {self.nick}')
        print(f'En el canal: {self.user_id}')
    # _____________________ EVENTOS DE PUBSUB __________________________


    # _____________________ EVENTOS DE CHAT __________________________
    async def event_message(self, message):
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
            await self.handle_commands(message)

    # _____________________ COMANDOS DE MENSAJE ____________________

    @commands.command(name='hola')
    async def hola(self, ctx):
        await ctx.send(f'Hola @{ctx.author.name}, ¿cómo estás?!')

    @commands.command(name='adios')
    async def adios(self, ctx):
        await ctx.send(f'¡Adiós, @{ctx.author.name} ¡Nos vemos despues! :D ')
    
    @commands.command(name='lurk')
    async def lurk(self, ctx):
        await ctx.send(f'Hummm... parece que @{ctx.author.name} se fue con las cariñosas! 🕵️‍♂️ Disfrutará del stream en modo sigiloso.')

    @commands.command(name='onlyfans')
    async def onlyfans(self, ctx):
        await ctx.send(f'¡Señoraaaa! @{ctx.author.name} anda de cochin@!')
    
            # amigos
    @commands.command(name='koala')
    async def koala(self, ctx):
        await ctx.send(f'Cállense todos, ya llego @elkoalam 👀🙄')
    
    @commands.command(name='llama')
    async def llama(self, ctx):
        await ctx.send(f'@loslordllama se la come doblada 🥵 dannda3Llamamo')
    
    @commands.command(name='daarlaaaaa')
    async def daarlaaaaa(self, ctx):
        await ctx.send(f' Como @DAARLAAAAA 🤯')

            # informativo
    @commands.command(name='horario')
    async def horario(self, ctx):
        await ctx.send(f'Hola! @{ctx.author.name} Tenemos Stream los Lunes, Miercoles y Viernes ')
        await ctx.send(f'🇲🇽:7:00pm,   🇨🇴:8:00pm,   🇻🇪:9:00pm,  ')
        await ctx.send(f'🇦🇷:10:00pm,   🇪🇨:8:00pm,   🇧🇴:9:00pm, ')
        await ctx.send(f'🇪🇸:3:00am,   🇵🇪:8:00pm,   🇺🇾: 10:00pm, ')
         
            # Componentes
    @commands.command(name='pc')
    async def pc(self,ctx):
            await ctx.send(f'Mi Pc está armada con estos componentes: [ Asus Z170-A ]  [ Core i5 6600k ]  [ 32gb RAM 3600hz ]  [ Nvidia RTX 3070 ]  [ Gabinete NZXT H440 ]')
    
    @commands.command(name='camara')
    async def camara(self, ctx):
        await ctx.send(f'Mi cámara es una: Canon Rebel T6icon un lente 18-135 f3.5')

    @commands.command(name='microfono')
    async def microfono(self,ctx):
            await ctx.send(f'Uso un micrófono super económico que encontré en Amazon: https://www.amazon.com.mx/gp/product/B08ZYB7NN2/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1 Con una interfaz (Tarjeta de audio) Focusrite Scarlett 2i2 Gen 1Y la mágia de la mezcla correcta de audio realizada en Dannprod ;)')

            # Redes
    @commands.command(name='instagram')
    async def instagram(self, ctx):
        await ctx.send(f'📸Instagrm: https://www.instagram.com/datotovar ')
    
    @commands.command(name='youtube')
    async def youtube(self, ctx):
        await ctx.send(f' 🔥 Suscríbete a mi canal de Youtube 📹Youtube: https://www.youtube.com/@DatoTovar ')
    
    @commands.command(name='whastapp')
    async def whastapp(self, ctx):
        await ctx.send(f'✉ Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14')

    @commands.command(name='wapp')
    async def wapp(self, ctx):
        await ctx.send(f'✉ Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14')

    @commands.command(name='discord')
    async def discord(self, ctx):
        await ctx.send(f'🎙Únete a mi canal de Discord y juega con nosotros! 🟢 https://discord.gg/aZaQRgSG')

    @commands.command(name='redes')
    async def redes(self, ctx):
        await ctx.send(f'Aquí están mis redes 😎! ')
        await ctx.send(f'📹Youtube: https://www.youtube.com/@DatoTovar ')
        await ctx.send(f'📸Instagrm: https://www.instagram.com/datotovar ')
        await ctx.send(f'✉ Whatsapp: https://whatsapp.com/channel/0029VaDUL8V7j6fwym4usU14')
        await ctx.send(f'🔥 Discord: https://discord.gg/aZaQRgSG')
    

                # dynamics
    @commands.command(name='comandos')
    async def comandos(self, ctx):
        """
        Muestra una lista de todos los comandos disponibles en el bot.
        """
        # Obtener los nombres de los comandos registrados
        command_list = [command.name for command in self.commands.values()]
        command_string = ", ".join(command_list)

        # Responder con la lista de comandos
        await ctx.send(f' 🤖 Comandos disponibles: {command_string}')

    @commands.command(name='memide')
    async def memide(self, ctx):
        lnCm = random.randint(0, 50)
        if lnCm <= 5: 
            lcExtra  ="🥺"
        elif lnCm > 5 and lnCm < 18:
            lcExtra ="👀"
        elif lnCm > 18 and lnCm < 25:
            lcExtra ="🥵"
        elif lnCm > 25 and lnCm  <35:
            lcExtra ="🤯"
        elif lnCm >= 35:
            lcExtra ="OMG  🤯🥵😈 increible"
        await ctx.send(f'A  @{ctx.author.name} le mide {lnCm}cm {lcExtra}')
    
    @commands.command(name='ruleta')
    async def ruleta(self, ctx):
        await ctx.send(f'@{ctx.author.name} quiere jugar a la ruleta rusa... toma el arma, se prepara...')
        time.sleep(1)
        lnOpcion = random.randint(0,1)
        if lnOpcion == 0: 
            lcRespuesta  ="La bala le dió en el pie... se salva"
        elif lnOpcion == 1:
             lcRespuesta  ="Bye, se ha matao mi hijo"
        await ctx.send(f'{lcRespuesta}')
    
    @commands.command(name='mecaben')
    async def mecaben(self, ctx):
        lnBoca = random.randint(0,3)
        lnCulo = random.randint(0,3)
        await ctx.send(f'A @{ctx.author.name} 😈 le caben {lnBoca} en la boca y {lnCulo} en el Qlo 🥵')

    @commands.command(name='bola8')
    async def bola8(self, ctx):
        lnResp = random.randint(0, 29)
        lcText = ''
        match lnResp:
            case 0:
                lcText = "Afirmativo, capitán."
            case 1:
                lcText = "Nel pastel."
            case 2:
                lcText = "Hmm... en una dimensión alternativa, tal vez."
            case 3:
                lcText = "Claro que yes, obvio que yeah."
            case 4:
                lcText = "Nope, ni lo sueñes."
            case 5:
                lcText = "Puede ser, pero también puede que no."
            case 6:
                lcText = "Sí, como que no."
            case 7:
                lcText = "Ni aunque me pagues en tacos."
            case 8:
                lcText = "Tal vez... dependiendo del clima."
            case 9:
                lcText = "De una, bro."
            case 10:
                lcText = "¡No! (Pero con estilo dramático)."
            case 11:
                lcText = "Deja que lo consulte con mi almohada."
            case 12:
                lcText = "SÍ, en mayúsculas."
            case 13:
                lcText = "Me niego rotundamente, pero gracias."
            case 14:
                lcText = "Tal vez sí, tal vez no, quién sabe."
            case 15:
                lcText = "Por supuesto, Sherlock."
            case 16:
                lcText = "No, pero gracias por preguntar."
            case 17:
                lcText = "Podría ser, pero no te hagas ilusiones."
            case 18:
                lcText = "Seh, pero con estilo."
            case 19:
                lcText = "Nelson Mandela."
            case 20:
                lcText = "Puede ser... si los astros se alinean."
            case 21:
                lcText = "Sí, como los memes del perrito."
            case 22:
                lcText = "Nah, pero aprecio el intento."
            case 23:
                lcText = "Tal vez, pero no pongo las manos en el fuego."
            case 24:
                lcText = "¡Oh, sí! (Insertar baile dramático)."
            case 25:
                lcText = "No, ni aunque me ofrezcas pizza."
            case 26:
                lcText = "Puede ser... si me das chocolate."
            case 27:
                lcText = "Sí, y te lo confirmo tres veces: sí, sí, sí."
            case 28:
                lcText = "No, ni en esta vida ni en la otra."
            case 29:
                lcText = "Tal vez... pero sólo si lo dices con un por favor."
        await ctx.send(f'{lcText} @{ctx.author.name}')

    @commands.command(name='duelo')
    async def duelo(self, ctx):
        if not ctx.message.content.strip().startswith('!duelo @'):
            await ctx.send("Por favor, usa el comando en el formato: !duelo @usuario")
            return
        parts = ctx.message.content.strip().split('@', 1)
        mentioned_user = parts[1].strip().split()[0] if len(parts) > 1 and parts[1].strip() else ""
        if not mentioned_user:
            await ctx.send("Por favor, usa el comando en el formato: !duelo @usuario")
            return
        await ctx.send(f'@{ctx.author.name} ha retado a @{mentioned_user} a un duelo de cuchillos...')
        lnResp = random.randint(1, 3)
        lnGanador = ctx.author.name if random.randint(0,1) else mentioned_user
        match lnResp:
            case 1:
                lcText = "Golpe certero: La hoja atraviesa el aire, final brutal. @"+lnGanador+" ha ganado"
            case 2:
                lcText = "Desenlace inesperado: Ambos sueltan los cuchillos y ríen."
            case 3:
                lcText = "Empate mortal: Caen juntos, aferrados a sus armas."
        time.sleep(1)
        await ctx.send(f'{lcText}')

    @commands.command(name='amor')
    async def amor(self, ctx):
        if not ctx.message.content.strip().startswith('!amor @'):
            await ctx.send("Por favor, usa el comando en el formato: !amor @usuario")
            return
        parts = ctx.message.content.strip().split('@', 1)
        mentioned_user = parts[1].strip().split()[0] if len(parts) > 1 and parts[1].strip() else ""
        if not mentioned_user:
            await ctx.send("Por favor, usa el comando en el formato: !amor @usuario")
            return
        lnAmor = random.randint(1, 100)
        if lnAmor <= 33: 
            lcExtra  ="❤️"
        elif lnAmor > 33 and lnAmor < 66:
            lcExtra ="❤️❤️"
        elif lnAmor >= 66:
            lcExtra ="❤️❤️❤️"
        time.sleep(1)
        await ctx.send(f'El amor entre @{ctx.author.name} y @{mentioned_user} es del {lnAmor}% {lcExtra}')

    @commands.command(name='midinero')
    async def midinero(self, ctx):
        lnBanco = random.randint(1, 10000)
        lnCartera = random.randint(1, 1000)
        lnTotal = lnBanco+lnCartera
        await ctx.send(f'@{ctx.author.name} tiene {lnBanco}$ en el banco  y {lnCartera}$ en la cartera 💵💲')

    @commands.command(name='primero')
    async def primero(self, ctx):
        # Llamamos a la función para manejar el primer usuario y el archivo JSON
        await handle_first_user(ctx)
    
    # Comando para registrar el ganador del Wordle
    @commands.command(name='ganadorw')
    async def ganadorw(self, ctx):
        # Validar si el mensaje contiene una mención de usuario
        if ctx.author.is_mod:
            if not ctx.message.content.strip().startswith('!ganadorw @'):
                await ctx.send("Por favor, usa el comando en el formato: !ganadorw @usuario")
                return
            # Obtener el nombre del usuario mencionado
            parts = ctx.message.content.strip().split('@', 1)
            mentioned_user = parts[1].strip().split()[0] if len(parts) > 1 and parts[1].strip() else ""
            if not mentioned_user:
                await ctx.send("Por favor, usa el comando en el formato: !ganadorw @usuario")
                return
            # Actualizar las estadísticas de Wordle
            has_won_subscription = update_wordle_winner(mentioned_user)

            # Enviar respuesta al chat
            if has_won_subscription:
                await ctx.send(f'¡@{mentioned_user} ha alcanzado 5 victorias y ha ganado una suscripción! 🎉')
            else:
                await ctx.send(f'¡@{mentioned_user} ha ganado el Wordle del día! 🏆')
        else:
            await ctx.send(f'Lo siento {ctx.author.name}, este comando es solo para moderadores.')


    # Comando para mostrar estadísticas globales de Wordle
    @commands.command(name='wordlestats')
    async def wordlestats(self, ctx):
        # Obtener estadísticas de Wordle
        ranking = get_wordle_stats()

        if not ranking:
            await ctx.send("No hay estadísticas de Wordle todavía.")
            return

        # Crear un mensaje con el ranking de ganadores
        ranking_msg = ", ".join([f"@{user} ({wins})" for user, wins in ranking])
        await ctx.send(f'Estadísticas de Wordle:')
        await ctx.send(f'{ranking_msg}')
    
    #____________________ TERMINAN COMANDOS DE TEXTO ! ______________________


# Inicializa y ejecuta el bot
if __name__ == "__main__":
    bot = ddpyBot()  # Crea solo una instancia
    bot.run()  # Ejecuta el bot