import requests
import discord
from sqlite3 import Cursor


def store_channel(db: Cursor, channel: discord.TextChannel):
    if (
        db.execute(
            "SELECT COUNT(*) FROM channels WHERE id=(?)",
            [channel.id],
        ).fetchone()[0]
        > 0
    ):
        return  # Channel already registered

    db.execute(
        "INSERT OR IGNORE INTO channels VALUES (?, ?)", [channel.id, channel.name]
    )


def store_user(db: Cursor, user: discord.User | discord.Member):
    if (
        db.execute(
            "SELECT COUNT(*) FROM users WHERE id=(?)",
            [user.id],
        ).fetchone()[0]
        > 0
    ):
        return  # User already registered

    avatar = requests.get(user.display_avatar.url)

    db.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)",
        [
            user.id,
            user.name,
            user.display_name,
            avatar.content,
            avatar.headers.get("Content-Type"),
        ],
    )
