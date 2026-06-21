# DannBot

Bot de Twitch construido con Python + TwitchIO para automatizar chat, registrar metricas del stream y gestionar comandos mixtos (hardcodeados + base de datos).

## Estado actual del proyecto

Esta version ya no usa un archivo de comandos generales hardcodeados para respuestas estaticas.

Ahora hay dos capas de comandos:

1. Comandos hardcodeados (logica real)
- Se implementan en componentes de `Commands/`.
- Se usan cuando el comando requiere programacion, llamadas API, cooldowns, validaciones o efectos colaterales.
- Ejemplos: `!clip`, `!titulo`, `!categoria`, `!mark`, `!bd`, `!followage`, `!end`.

2. Comandos fijos de texto (seed + BD)
- Se guardan en tabla `commands` de `data.db`.
- Se inicializan desde `Seed/basic_commands.py` al arrancar.
- Se pueden crear/editar/eliminar desde chat con `!newcmd`, `!editcmd`, `!delcmd`.

## Arquitectura principal

- `bot.py`
  - Arranque del bot.
  - Suscripciones EventSub.
  - Carga dinamica de componentes en `Commands/`.
  - Ejecuta seed de comandos base con `ensure_seed_basic_commands()`.

- `Seed/basic_commands.py`
  - Fuente oficial del seed de comandos fijos.
  - Define comandos canonicamente (uno por fila) con aliases en lista.
  - Migra esquema para soportar columna `aliases`.
  - Consolida filas legacy que antes estaban duplicadas por alias.

- `Helpers/helpers_moderator.py`
  - Gestion CRUD de comandos en BD.
  - Resolucion de comandos por nombre o alias.
  - Listado de comandos canonicos o con aliases.
  - Helpers de Twitch para titulo/categoria/clip/marker.

- `Handlers/handlers_message.py`
  - Guarda chat y estadisticas.
  - Si el mensaje inicia con `!` y no existe comando hardcodeado, busca en BD.
  - Soporta placeholder `{user}` en respuestas de BD.

- `Commands/moderator.py`
  - `!newcmd`, `!editcmd`, `!delcmd`.
  - Bloquea edicion/eliminacion de comandos nativos del bot.
  - Solo permite operar sobre comandos existentes en BD.

- `Commands/dynamic.py`
  - Comandos con logica dinamica.
  - `!comandos` mezcla comandos hardcodeados + comandos de BD.
  - Aplica visibilidad segun permisos y lista de excluidos.

## Seed de comandos (nuevo flujo)

Ubicacion:
- `Seed/basic_commands.py`

Estructura del seed:

```python
DEFAULT_BASIC_COMMAND_SEEDS = [
    {
        'command': 'user',
        'aliases': ['usuario', 'name', 'id'],
        'response': '[BOT] - Mi usuario en todos los juegos es DannDato'
    },
    ...
]
```

Comportamiento de `ensure_seed_basic_commands()`:

1. Asegura tabla `commands`.
2. Si falta la columna `aliases`, la agrega (`ALTER TABLE ... ADD COLUMN`).
3. Inserta comandos canonicos faltantes.
4. Si el comando ya existe, fusiona aliases existentes + aliases del seed.
5. Si detecta filas antiguas duplicadas por alias con misma respuesta, las elimina para compactar la BD.

Resultado:
- La lista de comandos ya no crece artificialmente por aliases duplicados.
- Los aliases siguen funcionando para invocar el comando.

## Esquema de base de datos para comandos

Tabla: `commands`

- `command TEXT PRIMARY KEY`
  - Nombre canonico (normalizado, ej. `!user`).
- `response TEXT NOT NULL`
  - Mensaje de respuesta.
- `aliases TEXT DEFAULT '[]'`
  - JSON array de aliases normalizados (ej. `["!id","!name","!usuario"]`).

## Diferencia entre comandos fijos y dinamicos

Comandos fijos (BD):
- Son respuestas de texto.
- Se pueden gestionar sin tocar codigo.
- Se ejecutan cuando no existe comando hardcodeado con ese nombre.

Comandos dinamicos (codigo):
- Requieren logica, estado o llamadas externas.
- Viven en `Commands/*.py`.
- Tienen prioridad sobre BD.

Prioridad de ejecucion en mensajes:

1. Si existe comando hardcodeado, se procesa por TwitchIO.
2. Si no existe, se intenta resolver en BD (nombre o alias).

## Comando !comandos (visibilidad por rol)

Implementado en `Commands/dynamic.py`.

Hace merge de:
- Comandos hardcodeados cargados en runtime.
- Comandos de BD (canonicos).

Filtro de seguridad:
- Lee `Helpers/textos/comandos_excluidos.txt`.
- Usuario regular: no ve comandos excluidos.
- Moderador o `is_authorized`: ve todos, incluidos excluidos.

## Nuevas funciones clave (documentadas)

### En `Seed/basic_commands.py`

- `_ensure_basic_commands_table()`
  - Crea tabla `commands` y asegura columna `aliases`.

- `_parse_aliases(raw_aliases)`
  - Interpreta aliases desde JSON (o fallback CSV legacy).

- `_serialize_aliases(aliases)`
  - Normaliza y serializa aliases a JSON.

- `ensure_seed_basic_commands()`
  - Ejecuta seed, fusiona aliases y consolida duplicados legacy.

### En `Helpers/helpers_moderator.py`

- `_resolve_stored_command_name(raw_command)`
  - Resuelve comando canonico por nombre principal o alias.

- `save_basic_command(raw_command, raw_response)`
  - Crea/actualiza comando principal (sin forzar aliases).

- `edit_basic_command(raw_command, raw_response)`
  - Edita respuesta buscando por comando o alias.

- `delete_basic_command(raw_command)`
  - Elimina comando canonico buscando por comando o alias.

- `get_basic_command_response(raw_command)`
  - Obtiene respuesta por comando o alias.

- `custom_command_exists(raw_command)`
  - Verifica existencia real en BD (incluye alias).

- `list_basic_command_names(include_aliases=False)`
  - Lista nombres de comandos de BD.
  - Por defecto solo canonicos (lista compacta).
  - Opcionalmente incluye aliases.

### En `Commands/moderator.py`

- `!newcmd` / `!ncmd`
  - Crea comando en BD (sin aliases obligatorios).

- `!editcmd` / `!ecmd`
  - Edita comando existente en BD.

- `!delcmd` / `!dcmd` / `!rmcmd`
  - Elimina comando existente en BD.

Validaciones relevantes:
- Solo mod/autorizados.
- No permite tocar comandos nativos.
- Solo actua si el comando existe en BD.

## Uso de aiohttp en el proyecto

El bot usa `aiohttp` para todas las llamadas HTTP async a Twitch/OAuth, evitando bloqueos del loop.

Patron general:

```python
async with aiohttp.ClientSession() as session:
    async with session.get|post|patch(url, headers=..., params|json|data=...) as resp:
        data = await resp.json(...)
```

Donde se usa principalmente:

1. `Helpers/helpers_moderator.py`
- `PATCH /helix/channels` para `!titulo` y `!categoria`.
- `GET /helix/search/categories` + `GET /helix/games/top` para matching de categorias.
- `POST /helix/streams/markers` para `!mark`.
- `POST /helix/clips` y polling de `GET /helix/clips` para `!clip`.

2. `Helpers/helpers_dynamic.py`
- Followers, VIPs, viewers, followage, Steam, etc.

3. `Helpers/helpers.py`
- Validaciones de broadcaster y tokens.

4. `Helpers/oauth_flow.py`
- Validacion/intercambio/refresh de tokens OAuth.

Buenas practicas aplicadas:
- Requests asincronas.
- Manejo de status codes y fallback seguro.
- Mensajes de error controlados para chat/log.

## Comandos por modulo (resumen)

- `Commands/admin.py`
  - `!ini`, `!end`, `!restart`, `!status`

- `Commands/moderator.py`
  - `!titulo`, `!categoria`, `!mark`
  - `!newcmd`, `!editcmd`, `!delcmd`

- `Commands/dynamic.py`
  - `!comandos` (merge hardcodeados + BD, con filtro por permisos)
  - y el resto de comandos dinamicos del bot (stats, utilidades, juegos, etc.)

- `Commands/player.py`, `Commands/stats.py`
  - Progresion/estadisticas de usuario y funcionalidades relacionadas.

## Configuracion y ejecucion

Requisitos:
- Python 3.11+
- Dependencias de `Tools/requirements.txt`

Instalacion recomendada (Windows PowerShell):

```powershell
python -m venv bot
.\bot\Scripts\Activate.ps1
pip install -r Tools/requirements.txt
```

Ejecucion:

```powershell
python bot.py
```

## Credenciales y seguridad

Archivos locales importantes:
- `Credentials/token.json` (token Twitch runtime)
- `.env` (secretos de entorno como SMTP/OpenAI/Steam)

Variables utiles para Discord (webhooks):
- `DISCORD_WEBHOOK`: webhook principal para eventos del stream (canal publico/general).
- `DISCORD_PRIVATE_WEBHOOK`: webhook privado para alertas criticas y datos sensibles.
- `DISCORD_SUBS_ROLE_ID`: rol de Discord a mencionar en nuevas subs (opcional).

No versionar secretos.

## Ejecutar como servicio en Debian (systemd)

1. Ajusta rutas y usuario en `Tools/dannbot.service`.
2. Copia el archivo a systemd:

```bash
sudo cp Tools/dannbot.service /etc/systemd/system/dannbot.service
```

3. Recarga systemd y habilita el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dannbot
sudo systemctl start dannbot
```

4. Verifica estado y logs:

```bash
sudo systemctl status dannbot
sudo journalctl -u dannbot -f
```

Notas de funcionamiento en modo servicio:
- El bot detecta entorno sin TTY y desactiva UI interactiva de consola.
- No dispara OAuth interactivo automáticamente en modo no interactivo.
- Si el token no puede refrescarse/reutilizarse, falla con mensaje claro para intervención manual.
- El servicio usa `Type=notify` + `WatchdogSec`, y el bot envia pulsos `WATCHDOG=1` para supervision activa.

## Integracion con Discord (MVP)

Eventos notificados por webhook:
- Inicio de directo (`stream_online`).
- Nuevos follows.
- Donaciones de bits.
- Nuevas subs y subs regaladas.
- Errores criticos del bot.
- Resumen post-stream (followers, bits, subs, mensajes, usuarios, estimado USD, top chatter).

### Roadmap recomendado (3 fases)

Fase 1 - Rapida (1 semana):
- Webhooks (ya implementado): inicio, follows, bits, subs, errores criticos, resumen post-stream.
- Separar webhook principal vs webhook de alertas.

Fase 2 - Media (1 mes):
- Bot de Discord con slash commands (`/status`, `/stream`, `/errores`).
- Canal de auditoria (quien ejecuto `!end`, `!restart`, `!logout`).
- Cola anti-spam para eventos explosivos (raids/regalos masivos).

Fase 3 - Avanzada (2-3 meses):
- Vinculacion Twitch<->Discord para asignacion automatica de rol por sub real.
- Job de reconciliacion periodica para revocar rol cuando termina la sub.
- Dashboard de comunidad (leaderboard, milestones y alertas inteligentes).

Comandos utiles de watchdog:

```bash
sudo systemctl show dannbot -p Type -p WatchdogUSec -p MainPID
sudo journalctl -u dannbot -f
```

## Notas de mantenimiento

1. Si modificas seed:
- Edita solo `Seed/basic_commands.py`.
- Reinicia bot para aplicar `ensure_seed_basic_commands()`.

2. Si agregas comandos dinamicos nuevos:
- Crear/editar componente en `Commands/`.
- Mantener validaciones de permisos donde aplique.

3. Si tocas el flujo de comandos BD:
- Revisar `Helpers/helpers_moderator.py` y `Handlers/handlers_message.py` juntos.

4. Si agregas integraciones HTTP:
- Usar `aiohttp` async.
- Manejar status y timeouts.
- Loggear errores sin romper el loop principal.

## Troubleshooting rapido

- `!comandos` muy largo:
  - Verifica que el listado use nombres canonicos (sin aliases repetidos).

- Alias no responde:
  - Revisa columna `aliases` en tabla `commands`.
  - Reinicia bot para re-ejecutar seed y consolidacion.

- Error de permisos en comandos de gestion:
  - Verifica `is_authorized` y rol moderador en Twitch.

- No aparece comando seed:
  - Confirma que `bot.py` importa y ejecuta `ensure_seed_basic_commands()` en `setup_hook`.
