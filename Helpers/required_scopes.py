# Helpers/required_scopes.py

required_scopes = [
    # Chat + EventSub chat messages
    'chat:read',
    'chat:edit',
    'user:read:chat',
    'user:write:chat',
    'user:bot',
    'channel:bot',

    # EventSub / comandos de followers, subs, bits, chatters
    'bits:read',
    'channel:read:subscriptions',
    'moderator:read:followers',
    'moderator:read:chatters',

    # Comando !vips
    'channel:read:vips',

    # Comandos de moderacion del stream: !titulo, !categoria, !mark
    'channel:manage:broadcast',

    # Comando !clip
    'clips:edit',

    # EventSub channel.ban / channel.unban
    'channel:moderate',
]