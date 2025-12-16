import data
from sqlite3 import Cursor
import json


class Locale:
    def __init__(self, language: str):
        with open(f"lang/{language}.json", "r", encoding="utf-8") as file:
            data: dict[str, str] = json.load(file)

            self.data: dict[str, str] = data

    def entry(self, id: str) -> str:
        return self.data[id]


loaded: dict[str, Locale] = {}


def load(language: str):
    global loaded

    loaded[language] = Locale(language)


def locale(language: str) -> Locale:
    global loaded

    if language not in loaded:
        load(language)

    return loaded[language]


def lang(db: Cursor, guild: int) -> Locale:
    data.setup_guild_cache(db, guild)

    language: str | None = db.execute(
        "SELECT language FROM settings WHERE guild=(?)", [guild]
    ).fetchone()[0]

    if language is not None:
        return locale(language)
    else:
        return locale("en")
