import logging
import twitchio.eventsub.websockets as websockets

def patch_eventos():
    #  ESTA PARTE ES IMPORTANTE PARA HACER UN MONKEY PATCH A LA LIBRERIA DE TWITCHIO
    """
        Esta parte es importante para hacer un monkey patch a la librería de TwitchIO
        para que el bot pueda manejar eventos de Twitch de manera personalizada.
        Básicamente estaremos reemplazando un metodo de la clase client
        por uno que haremos perzonalizado llamado 'dannbot_all_events'
    """
    # Encuentra la clase que maneja los WebSockets de TwitchIO
    WebsocketClass = None
    for obj in vars(websockets).values(): # Recorre todos los objetos en el módulo websockets
        if isinstance(obj, type) and hasattr(obj, "_process_notification"): # Verifica si es una clase y tiene el método _process_notification
            print("🎯 Clase WebSocket encontrada:", obj.__name__)   
            WebsocketClass = obj # Asigna la clase encontrada a WebsocketClass
            break

    # Guardamos el proceso original
    original_process_notification = WebsocketClass._process_notification

    # Definimos el nuevo comportamiento
    async def patched_process_notification(self, notification_data): # Este es el nuevo método que reemplazará al original
        """
        print("Interceptado EventSub:")
        print("  Tipo:", notification_data["metadata"]["message_type"])
        print("  Sub:", notification_data["metadata"].get("subscription_type"))
        print("  Payload:", notification_data.get("payload"))
        """
        if self._client: # Verifica si el cliente está conectado
            self._client.dispatch("dannbot_all_event", notification_data) # Lanza un evento personalizado para manejar todos los eventos de Twitch
        # Ejecutar el original
        return await original_process_notification(self, notification_data) # Llama al método original para que siga funcionando como antes

    # Parcheamos
    WebsocketClass._process_notification = patched_process_notification # Reemplazamos el método original con el nuevo
    
    
    # # Silenciar logs detallados de Websockets
    # logging.getLogger("twitchio.eventsub.websockets").setLevel(logging.INFO)

    # # Silenciar logs del archivo client.py de TwitchIO
    # logging.getLogger("twitchio.client").setLevel(logging.INFO)

    # # Silenciar logs del archivo http.py de TwitchIO
    # logging.getLogger("twitchio.http").setLevel(logging.INFO)
#_________________________________________________________________________________