# Helpers/required_scopes.py

# Fuente unica de verdad para OAuth.
# Esta lista se usa en Helpers/oauth_flow.py para construir la URL de autorizacion
# y para validar que el token tenga todos los permisos requeridos.
required_scopes = [
    # Chat (EventSub chat + envio de mensajes)
    # - eventsub.ChatMessageSubscription
    # - send_message / respuestas de comandos
    'chat:read',
    'chat:edit',
    'user:read:chat',
    'user:write:chat',
    'user:bot',
    'channel:bot',

    # Followers (EventSub + Helix /channels/followers para !followage y !followers)
    'bits:read',
    'moderator:read:followers',

    # Subs (EventSub subs/gift subs)
    'channel:read:subscriptions',

    # Chatters (Helix fetch_chatters para !viewers y polling)
    'moderator:read:chatters',

    # VIPs (Helix /channels/vips para !vips)
    'channel:read:vips',

    # Broadcast management (Helix /channels, /streams/markers)
    # - !titulo, !categoria, !mark
    'channel:manage:broadcast',

    # Clips (Helix /clips)
    'clips:edit',

    # Moderation (EventSub ban/unban)
    'channel:moderate',
]