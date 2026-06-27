from functools import lru_cache
from importlib import resources
from typing import Any

import yaml

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "ru")


def normalize_locale(language_code: str | None) -> str:
    if not language_code:
        return DEFAULT_LOCALE
    locale = language_code.replace("_", "-").split("-", maxsplit=1)[0].lower()
    return locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE


def user_locale(user: object | None) -> str:
    return normalize_locale(getattr(user, "language_code", None))


@lru_cache
def _load_locale(locale: str) -> dict[str, Any]:
    normalized = normalize_locale(locale)
    resource = resources.files("cinedive.lang").joinpath(f"{normalized}.yml")
    data = yaml.safe_load(resource.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"Locale file {normalized}.yml must contain a mapping.")
    return data


def _lookup(locale_data: dict[str, Any], key: str) -> object | None:
    value: object = locale_data
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def t(locale: str | None, key: str, **params: object) -> str:
    normalized = normalize_locale(locale)
    value = _lookup(_load_locale(normalized), key)
    if value is None and normalized != DEFAULT_LOCALE:
        value = _lookup(_load_locale(DEFAULT_LOCALE), key)
    if value is None:
        return key
    text = value if isinstance(value, str) else str(value)
    return text.format(**params) if params else text


def text_variants(key: str) -> set[str]:
    return {t(locale, key) for locale in SUPPORTED_LOCALES}
