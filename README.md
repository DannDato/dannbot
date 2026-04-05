# DannBot

Bot de Twitch construido con Python y TwitchIO para automatizar chat, registrar estadisticas del stream, gestionar comandos modulares y generar reportes HTML enviados por correo.

## Resumen

DannBot actualmente incluye:

- Integracion con Twitch EventSub (mensajes, follows, subs, bits, ban/unban, updates de canal, online/offline).
- Sistema de comandos modular por componentes.
- Registro de actividad en SQLite (usuarios, mensajes, follows, subs, stream_data, etc.).
- Polling de chatters cada 5s para metrica real de personas en chat.
- Reporte de fin de stream con comparativas, conclusiones y grafica embebida en el correo.
- Integracion opcional con OpenAI para funciones de lenguaje natural (por ejemplo parseo flexible de fechas).

## Estructura principal

- `bot.py`: arranque principal del bot y suscripciones EventSub.
- `server.py`: flujo OAuth local para autorizar Twitch.
- `Commands/`: componentes de comandos.
- `Handlers/`: handlers de eventos EventSub/chat.
- `Helpers/`: utilidades de API, DB, OAuth, correo, stats, etc.
- `Html/mails/end_stream.html`: plantilla del correo de reporte.
- `Credentials/token.json`: token OAuth y datos de Twitch del canal autorizado (archivo local, no versionado).
- `.env`: credenciales sensibles de app y SMTP (archivo local, no versionado).

## Componentes de comandos

Carga dinamica desde `Commands/` en `setup_hook`.

- `admin.py`: comandos administrativos de stream/control (`!ini`, `!end`, `!restart`, `!status`).
- `moderator.py`: comandos de moderacion de stream (`!titulo`, `!categoria`, `!mark`).
- `general.py`: comandos generales del chat y `!clip`.
- `dynamic.py`: comandos dinamicos/juegos/utilidades (`!viewers`, `!followage`, `!bd`, etc.).
- `stats.py`, `player.py`: estadisticas de usuario y progresion.

## Requisitos

- Python 3.12+
- Dependencias de `Tools/requirements.txt`

Instalacion sugerida (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r Tools/requirements.txt
```

Ejecucion:

```powershell
python bot.py
```

## Configuracion de entorno (.env)

Crea `.env` a partir de `.env.example`.

Variables usadas actualmente:

```env
# Twitch OAuth app
DANNBOT_CLIENT_ID=...
DANNBOT_CLIENT_SECRET=...

# SMTP para envio de reportes
DANNBOT_MAIL_USER=tu_correo@gmail.com
DANNBOT_MAIL_PASS=tu_app_password
```

Aliases soportados:

- `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`
- `SMTP_USER`, `SMTP_PASS`

## OAuth y token

### Que guarda `Credentials/token.json`

`token.json` se usa para datos de conexion del usuario/canal autorizado en Twitch, por ejemplo:

- `access_token`, `refresh_token`
- `client_id`, `client_secret`
- `bot_id`, `owner_id`, `channel_name`
- `scopes`, `token_type`, `expires_in`, `token_obtained_at`

Nota: credenciales SMTP/OpenAI/Steam no dependen de `token.json`; se leen de `.env`.

### Flujo OAuth

Si no hay token utilizable, el bot inicia flujo OAuth con `server.py` en `http://localhost:8080`.

- Si el usuario autoriza: se genera/actualiza `Credentials/token.json`.
- Si el usuario cancela o deniega: el flujo termina limpio sin dejar procesos colgados ni logs ruidosos.

## Scopes requeridos (minimos actuales)

Definidos en `Helpers/required_scopes.py`.

Incluyen lo necesario para funcionalidades activas:

- Chat/EventSub chat: `chat:read`, `chat:edit`, `user:read:chat`, `user:write:chat`, `user:bot`, `channel:bot`
- Metricas/comandos: `bits:read`, `channel:read:subscriptions`, `moderator:read:followers`, `moderator:read:chatters`, `channel:read:vips`
- Moderacion de stream: `channel:manage:broadcast`
- Clips: `clips:edit`
- EventSub ban/unban: `channel:moderate`

## Funcionalidades destacadas

### Metricas de viewers por chat real

`Helpers/helpers_bot.py` realiza polling de chatters cada 5 segundos y persiste en `stream_data`:

- `stream_actual_viewers`
- `stream_max_viewers`
- `stream_avg_viewers`

El comando `!viewers` usa chatters reales, no `viewer_count` del stream.

### Followage con cache

`!followage` usa Helix + cache SQLite (`followage_cache`) para reducir llamadas y mantener fecha original de follow.

### Cumpleanos flexible

`!bd` soporta parseo de fecha flexible (formatos comunes y lenguaje natural con fallback).

### Moderacion de stream

- `!titulo`: actualiza titulo y agrega sufijo ` [ !redes !discord !sr ]`.
- `!categoria`: seleccion tolerante por similitud con sugerencias.
- `!mark`: crea stream marker para ubicar momentos en VOD.
- `!clip` (general): crea clip directo por Helix.

## Reporte de fin de stream por correo

Al ejecutar `!end`, se procesa el stream y se envia correo con:

- Resumen principal (visitantes, follows, mensajes, tiempo, donaciones aproximadas).
- Peak/avg viewers.
- Lista de participantes unicos.
- Grafica unica comparativa (3 streams) con eje X/Y:
  - Serie 1: usuarios unicos
  - Serie 2: mensajes

Implementacion:

- Plantilla base: `Html/mails/end_stream.html`
- Logica de armado/reemplazos: `Helpers/helpers_admin.py`
- Envio SMTP + guardado de copia HTML en `Reportes/`: `Helpers/mailer.py`

Robustez agregada:

- Manejo de division por cero en porcentajes.
- Tolerancia a tablas mensuales de chat faltantes (`chat_YYYYMM`).
- Evita uso de cursor cerrado en consultas complementarias.

## Seguridad y versionado

`.gitignore` esta configurado para excluir secretos y artefactos locales, incluyendo:

- `.env`
- `Credentials/*` sensibles
- `token.json`
- bases locales (`*.db`, `*.sqlite`, `*.sqbpro`)
- `Logs/`, `Reportes/`, `Gpt/`, caches y entornos virtuales

### Eliminar `token.json` del repo de forma segura

Si quieres sacar `Credentials/token.json` por completo sin romper el proyecto:

1. Rotar secretos primero (obligatorio):
  - Regenera/revoca `access_token` y `refresh_token`.
  - Si hubo exposicion, rota tambien `client_secret` en tu app de Twitch.

2. Mantener archivo local pero no versionado:
  - `Credentials/token.json` debe quedar solo en tu maquina.
  - El repo incluye `Credentials/token.example.json` como plantilla segura.

3. Si alguna vez estuvo en historial Git y quieres purgarlo:
  - Requiere reescritura de historial y forzar push.
  - Con `git filter-repo` (recomendado):

```bash
git filter-repo --path Credentials/token.json --invert-paths
git push --force --all
git push --force --tags
```

4. Despues de purgar historial:
  - Invalidar tokens anteriores nuevamente por seguridad.
  - Pedir al equipo que vuelva a clonar o haga hard reset a ramas compartidas.

## Troubleshooting rapido

- Error OAuth/cancelacion: vuelve a ejecutar `python bot.py`; el cierre ya es limpio.
- Error de correo: verifica `DANNBOT_MAIL_USER` y `DANNBOT_MAIL_PASS` en `.env`.
- Problemas de scopes: reautoriza OAuth para refrescar token con scopes actuales.
- Problemas de import en VS Code: revisa que el interprete seleccionado sea el del entorno con dependencias instaladas.

## Desarrollo

Para extender el bot:

1. Agrega/modifica componentes en `Commands/`.
2. Agrega helpers en `Helpers/` separados por dominio.
3. Manten `token.json` para datos de Twitch y `.env` para secretos operativos (SMTP/otros).
4. Si agregas funcionalidades nuevas de Twitch, actualiza `Helpers/required_scopes.py` y reautoriza OAuth.

## Comandos rapidos por rol

| Rol | Comandos | Uso principal |
|---|---|---|
| Admin autorizado | `!ini`, `!end`, `!restart`, `!status` | Iniciar/cerrar stream en DB, reinicio y salud del bot |
| Moderador autorizado | `!titulo`, `!categoria`, `!mark` | Gestion de metadata del stream y markers en VOD |
| General chat | `!clip`, `!viewers`, `!followage`, `!bd`, `!cumple` | Utilidades de chat, clips, viewers y datos de usuario |

Notas:

- `!titulo`, `!categoria` y `!mark` validan tanto `is_authorized` como `is_mod`.
- `!clip` crea clip por Helix (`clips:edit`) y responde con URL de clip/edicion.
- `!viewers` usa chatters reales (`fetch_chatters`), no el `viewer_count` del stream.

## Flujo recomendado para mod en vivo

Secuencia sugerida al iniciar o ajustar un directo:

1. `!categoria <nombre aproximado>`
2. `!titulo <titulo del stream>`
3. `!mark inicio`

Durante momentos importantes:

1. `!mark <momento clave>`
2. `!clip`

Antes de cerrar:

1. Confirmar estado con `!status` (admin)
2. Cerrar stream con `!end` (admin)
