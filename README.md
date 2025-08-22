                ██████╗  █████╗ ███╗   ██╗███╗   ██╗██████╗  ██████╗ ████████╗
                ██╔══██╗██╔══██╗████╗  ██║████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
                ██║  ██║███████║██╔██╗ ██║██╔██╗ ██║██████╔╝██║   ██║   ██║   
                ██║  ██║██╔══██║██║╚██╗██║██║╚██╗██║██╔══██╗██║   ██║   ██║   
                ██████╔╝██║  ██║██║ ╚████║██║ ╚████║██████╔╝╚██████╔╝   ██║   
                ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   
                        ___________________________________________

*                       Dev By: Alberto Daniel Tovar Mendoza
                                           
DannBot es un bot desarrollado en Python que se conecta a Twitch mediante la API/librería twitchio. Su principal función es interactuar en el chat canal 'DannDato', generar retos, responder comandos y registrar estadísticas de usuarios y streams en una base de datos.

El bot implementa un sistema de XP y niveles que mide la participación de los usuarios en el chat, otorgando puntos en distintas características como Carisma, Habilidad, Fuerza, entre otras. Además, puede generar reportes y utilizar la API de OpenAI para enriquecer la experiencia de la interacción del bot con lo participanrtes del stream.


---

## ⚙️ Tecnologías y Librerías Usadas

### Lenguaje
* **Python** (versión recomendada: 3.12.8)

### Twitch y Streaming
* **TwitchIO v3** – Interacción con la API/Libreria Twitchio 
* **OBS WebSocket (obsws-python)** – Control de OBS Studio (NO implementado aun)

### Web y APIs
* **Requests** – Peticiones HTTP  
* **Flask** – Microservidor web para endpoints o integraciones

### Base de datos y utilidades
* **SQLite** – Base de datos local  
* **SQLite-utils** – Manejo de SQLite de forma sencilla  
* **Asqlite** – Operaciones asíncronas con SQLite

### Automatización y scraping
* **Selenium** – Automatización de tareas web  
* **PyAutoGUI** – Control de mouse y teclado en automatizaciones

### Variables de entorno
* **Python-dotenv** – Gestión de variables de entorno

### Logs y colores
* **Colorama & Colorlog** – Logs a color en consola  
* **Logging** – Registro de eventos y errores

### Correos y HTML
* **Premailer** – Formateo de HTML para correos

### Otros
* **Emoji** – Soporte para emojis  
* **OpenAI & Tiktoken** – Integración con ChatGPT y procesamiento de tokens  

---


## 🗂 Estructura de la Base de Datos
El bot utiliza SQLite como sistema de almacenamiento para registrar y consultar la actividad del canal y las interacciones de los usuarios. La base de datos está diseñada para soportar la gestión de usuarios, estadísticas y funcionalidades adicionales como cumpleaños y clanes.

###### 📋 Tablas principales:
   * chat_AAAAMM:	Registro detallado de los mensajes enviados en el año/mes . (Estas son tablas dinamicas se van generando una por mes)
   
   * clanes:	Almacena los clanes existentes, quien es el lider y los usuarios que pertenecen a los clanes.
   
   * donated_bits:	Registra las donaciones de bits realizadas por los usuarios. Almacena el usuario, la cantidad de bits y la fecha del donativo.
   
   * followers: registra a los nuevos usuarios que le dan follow al canal, guarda (user, username, date y timestamp)
   
   * history_users:	Historial de las veces que entra un usuario al canal, Guarda twitch_id y datetime
   
   * redeems:	Almacena las recompensas canjeadas por los usuarios usando puntos del canal o integraciones propias del bot. Incluye el usuario, la recompensa y la fecha.
   
   * stats_channel:	Almacena estadísticas generales del canal y los usuarios en diferentes categorias como: Habilidad,
    carisma, resistencia, wordle_wins, mensajes etc.

   * stream_data:	Guarda información de cada transmisión, incluyendo fecha de inicio y fin, duración, top chatter,
    total de usuarios unidos y total de mensajes enviados en el stream

   * subscriptions: registra las subs de un usuario independientemente de si es propia o regalada
   
   * subscriptions_gift: guarda a los usuarios que regalan subs, cuantas, de que tier y la fecha

   * users:	Registra a todos los usuarios que han interactuado en el chat. Se almacena su username, twitch_id, y cumpleaños, se contempla la opción de agregar mas cosas


###### Esta estructura permite:
* ✅ Generar estadísticas detalladas por transmisión
* ✅ Calcular rankings y Datos de cada directo
* ✅ Llevar un historial de actividad y crecimiento de cada usuario
* ✅ Crear dinámicas como clanes, retos y minijuegos 
* ✅ Felicitar a los usuarios el día de su cumpleaños
* ✅ Integrar sistemas de recompensas y redenciones
* ✅ Registrar las donaciones de bits como parte de la interacción del usuario
* ✅ Registrar las donaciones de subs como parte de la interacción del usuario
* ✅ Registrar las subs como parte de la interacción del usuario


## 🚀 Cómo ejecutar el bot
Clona el repositorio oficial desde GitHub:
```
git clone https://github.com/DannDato/dannbot.git
cd dannbot
```

Asegúrate de tener Python 3 instalado en el servidor. En sistemas basados en Debian/Ubuntu puedes instalarlo con:
```
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

Crea y activa el entorno virtual de Python (si aún no está creado):
```
python3 -m venv bot
source bot/bin/activate
Verás que el prefijo de la terminal cambia a (bot), indicando que el entorno virtual está activo.
```

Instala las dependencias del proyecto utilizando el archivo requirements.txt ubicado en la carpeta tools:
```
pip install -r Tools/requirements.txt
```

Una vez instalado todo, ejecuta el bot con:git a
```
python3 bot.py
```

Recomendacion; Para monitorear el consumo de recursos en tiempo real, abre otra terminal y ejecuta:
```
htop
```
Para monitorear la temperatura del servidor, utiliza el script monit_temp.sh. Ubica el directorio y ejecuta el monitor de temperatura con:
```
cd Documents/Temperature
./monit_temp.sh
```
Esto ejecutará el comando sensors cada 3 segundos y actualizará la consola en tiempo real.



## 📜 Funcionamiento General - DannBot
El bot está diseñado como una herramienta modular y escalable para automatizar interacciones dentro del chat de Twitch, así como gestionar eventos de la plataforma mediante PubSub y EventSub.

El bot inicia configurando la consola y cargando las credenciales necesarias desde token.json. Realiza una verificación de los tokens de acceso, client ID y broadcaster ID, asegurándose de que todo esté en orden para establecer la conexión con la API de Twitch.

Al iniciar, el bot se encarga de verificar si existe el archivo token.json con las credenciales necesarias para conectarse a Twitch,
Si existe, el bot carga el access_token desde ese archivo y continúa con la conexión.
❌ Si no existe token.json
El bot solicita el client_id del desarrollador.
Con ese client_id, genera un enlace de autenticación (OAuth) para el usuario.

> **IMPORTANTE:** Antes de dar clic en el enlace de autorización, asegúrate de tener corriendo el archivo server.py incluido en este proyecto.**server.py** es un pequeño servidor local que escucha en http://localhost:8080 y captura la redirección de Twitch con el token de acceso.

Una vez autorizado, el navegador redirigirá automáticamente a http://localhost:8080, donde server.py mostrará la URL completa con el token.
es necesario copiar el token de la URL y pegarlo en el input que solicita el bot
El bot toma ese token y lo guarda en credentials/token.json con el siguiente formato:

>{ 
>    "access_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
>}

Finalmente, reinicia el bot para comenzar a funcionar con el nuevo token.



### 🌐 Conexión a Twitch
Con las credenciales listas el bot está organizado en módulos de comandos separados por funcionalidad:
    Admin: Comandos administrativos para la gestión interna.
    General: Comandos generales de interacción con el chat.
    Stats: Comandos que muestran estadísticas del canal o los usuarios.
    Dynamic: Comandos dinámicos personalizables durante la transmisión.
    XP: Sistema de puntos de experiencia y niveles para los usuarios.
    Cada módulo se carga de manera individual durante la inicialización, permitiendo un fácil mantenimiento y expansión.


### 🎯 Manejo de Eventos
El bot está diseñado para escuchar y manejar eventos importantes como:
Mensajes en el chat: Guarda el chat, analiza contenido y podría ejecutar comandos (por ahora desactivado el handler de comandos).
Usuarios que se unen: Detecta la entrada de nuevos usuarios al canal.
Errores de comandos: Detecta cuando alguien usa un comando inexistente.
Además, aunque por ahora están comentados, el bot cuenta con soporte para PubSub de Twitch, permitiendo reaccionar a:
    Canjeo de Puntos de Canal
    Donación de Bits
    Subscripciones y regalos de subs
    Estos eventos se manejan mediante sus respectivos handlers especializados.


### ⏰ Tareas en Segundo Plano
Cuando el bot está en línea (event_ready), lanza dos tareas paralelas:
Mensajes programados en el chat cada cierto tiempo.
Felicitación de cumpleaños si detecta que algún usuario cumple años (o en fechas especiales predefinidas).
Estas tareas le dan vida y presencia constante en el canal.

### 💻 Control desde Consola
Mientras el bot está corriendo, puedes interactuar con él desde la consola con comandos como:
    status: Verifica que el bot esté en línea.
    exit: Apaga el bot de forma segura y controlada.

### 🛑 Apagado Seguro
Cuando se ejecuta el apagado, el bot:
    Cancela las tareas en segundo plano.
    Cierra la conexión con Twitch de manera ordenada.
    Limpia la consola y notifica el cierre.


## 🤖 Funciones del Bot

#### Comandos de Interacción Básica
* !bot: Inicia una conversación directa con el bot.
* !hola: Saluda en el chat.
* !adios: Se despide en el chat.
* !lurk: Activa el estado de "lurking" (presencia pasiva).
* !unlurk: Desactiva el estado de "lurking".
* !onlyfans: Responde con un enlace o mensaje relacionado con "OnlyFans".
* !koala: Muestra un mensaje relacionada con elKoala.
* !llama: Muestra un mensaje relacionada con losLordLlama.
* !daarlaaaaa: Muestra un mensaje de "daarlaaaaa".
* !maikol: Responde con un mensaje o acción asociada a "maikol".
* !horario: Muestra el horario actual de los streams.
* !pc: Proporciona detalles sobre la PC del Streamer.
* !camara: Muestra la información sobre el micrófono del streamer.
* !microfono: Muestra la información sobre la cámara del streamer.
* !so: Envia un mensaje publicitario de la persona etiquetada en el comando.

#### Redes Sociales
* !instagram: Muestra el perfil de Instagram.
* !youtube: Muestra el canal de YouTube.
* !whatsapp: Proporciona un enlace o información de WhatsApp.
* !discord: Muestra el enlace de invitación al servidor de Discord.
* !spotify: Proporciona el enlace o información de Spotify.
* !redes: Muestra un resumen de todas las redes sociales del canal.

#### Comandos de Juegos y Desafíos
* !ladrillo: Realiza una acción o muestra un mensaje relacionado con "ladrillo".
* !primero: Indica quién fue el primero en un reto o actividad.
* !primeroscore: Muestra el puntaje de la primera persona en un desafío.
* !primerotop: Muestra a la persona que lidera el desafío.
* !wordlewin: Indica que un usuario ha ganado en el juego de Wordle.
* !wordlelose: Indica que un usuario ha perdido en el juego de Wordle.
* !wordlescore: Muestra el puntaje total de un jugador en Wordle.
* !wordletop: Muestra al top 5 jugadores en Wordle.
* !retowin: Indica que un usuario ha ganado un reto.
* !retolose: Indica que un usuario ha perdido un reto.
* !retoscore: Muestra el puntaje en los retos.

#### Comandos de Diversión
* !memide: Muestra o activa un meme o broma.
* !bd: Guarda la información del cumpleaños de un usuario recibiendolo en el formato YYYY-MM-DD.
* !cumpleaños: Muestra el cumpleaños del usuario que ejecuta el comando o el etiquetado.
* !ruleta: Juega una ruleta con opciones aleatorias.
* !mecaben: Realiza una broma con el comando "mecaben".
* !bola8: Responde a una pregunta con una bola 8 mágica.
* !trivia: Genera una pregunta de trivia.
* !insultar: Permite al bot insultar a un usuario.
* !insultame: Insulta al usuario que lo solicita.
* !halago: El bot da un halago al usuario.
* !caraocruz: Realiza una acción aleatoria o divertida.
* !meporte: Muestra un mensaje relacionado con "me porté".
* !nalgada: Ejecuta una acción o mensaje relacionado con una "nalgada".
* !pies: Realiza una acción o broma sobre pies.
* !abrazo: El bot envía un mensaje de abrazo virtual.
* !duelo: Inicia un duelo de cualquier tipo (puede ser un mini-juego o desafío).
* !ip: Muestra la dirección IP (de broma) del usuario.
* !amor: Responde con un mensaje de amor.
* !odio: Responde con un mensaje de odio (de manera divertida).
* !dinero: Muestra el dinero acumulado o alguna información económica del bot.
* !donar: Indica cuanto debe donar un usuario (de broma).
* !setso: Invita a otro usuario a la acción "sexo" de broma.
* !xeno: Realiza una acción o muestra un mensaje relacionado con "xeno".
* !ban?: Inicia una solicitud de ban de usuario.
* !vips: Muestra una lista de usuarios VIP del canal.
* !joteria: Calcula el nivel de "jotería" del usuario.

#### Comandos de XP y Niveles
* !player: Muestra información sobre el jugador o usuario.
* !xp: Muestra el XP del usuario.
* !nivel: Muestra el nivel de un jugador.
* !top: Muestra el ranking de jugadores por puntos o XP.
* !skin: Muestra la skin del usuario.
* !setskin: Establece una nueva skin para el usuario.
* !clan: Muestra o gestiona la información del clan.
* !recompensas: Muestra las recompensas disponibles o gestionadas por el bot.
* !mensajes: Muestra el número de mensajes enviados en el chat.

#### Comandos de Información
* !comandos: Muestra la lista de comandos disponibles.
* !juegos: Muestra los juegos disponibles para jugar.