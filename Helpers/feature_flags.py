import os
from pathlib import Path


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_ENV_MTIME = None
_ENV_VALUES = {}


_TRUE_VALUES = {"1", "true", "yes", "y", "on", "si", "s"}
_FALSE_VALUES = {"0", "false", "no", "n", "off"}


def _load_env_values() -> None:
    global _ENV_MTIME, _ENV_VALUES

    if not ENV_PATH.exists():
        _ENV_MTIME = None
        _ENV_VALUES = {}
        return

    try:
        mtime = ENV_PATH.stat().st_mtime
    except OSError:
        return

    if _ENV_MTIME == mtime:
        return

    parsed = {}
    try:
        with ENV_PATH.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue

                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                parsed[key] = value
    except OSError:
        return

    _ENV_VALUES = parsed
    _ENV_MTIME = mtime


def get_feature_raw(name: str, default: str | None = None) -> str | None:
    _load_env_values()

    if name in os.environ:
        return os.environ.get(name)

    if name in _ENV_VALUES:
        return _ENV_VALUES.get(name)

    return default


def is_feature_enabled(name: str, default: bool = True) -> bool:
    raw = get_feature_raw(name)
    if raw is None:
        return default

    normalized = str(raw).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False

    return default
