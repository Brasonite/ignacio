import util
import requests
from uuid import uuid4

from io import BytesIO

from discord.sinks import AudioData

from audio import TimestampedWaveSink

import data

import datetime

import discord

import os

import sqlite3


class RecordedMessage:
    def __init__(self, message: discord.Message, timestamp: float):
        self.message = message
        self.timestamp = timestamp


class RecordingState:
    def __init__(self, vc, origin, start: float):
        self.vc = vc
        self.origin = origin
        self.start = start
        self.messages: list[RecordedMessage] = []


class RecordingFile:
    def __init__(self, sink: TimestampedWaveSink, state: RecordingState):
        dt = datetime.datetime.fromtimestamp(state.start)
        filename = f"{dt.year}-{dt.month}-{dt.day}_{dt.hour}-{dt.minute}-{dt.second}.db"
        filepath = f"{data.RECORDING_DIR}/{filename}"

        if os.path.exists(filepath):
            os.remove(filepath)

        file_connection = sqlite3.connect(f"{data.RECORDING_DIR}/{filename}")
        file = file_connection.cursor()

        file.execute(
            "CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK (id = 1), audio_start FLOAT)"
        )
        file.execute(
            "CREATE TABLE users (id INTEGER NOT NULL PRIMARY KEY, name TINYTEXT NOT NULL, display_name TINYTEXT NOT NULL, avatar MEDIUMBLOB NOT NULL, avatar_type TINYTEXT)"
        )
        file.execute(
            "CREATE TABLE audio (user INTEGER NOT NULL PRIMARY KEY, data MEDIUMBLOB)"
        )
        file.execute(
            "CREATE TABLE messages (offset FLOAT NOT NULL, user INTEGER NOT NULL, text TEXT, attachments TEXT)"
        )
        file.execute(
            "CREATE TABLE attachments (id TEXT NOT NULL PRIMARY KEY, mime TINYTEXT, data MEDIUMBLOB NOT NULL)"
        )

        file.execute("INSERT INTO metadata VALUES (1, ?)", [sink.start])

        for user_id, audio in sink.audio_data.items():
            member: discord.Member = state.origin.guild.get_member(user_id)
            util.store_user(file, member)

            if not isinstance(audio, AudioData):
                continue

            if not isinstance(audio.file, BytesIO):
                continue

            file.execute(
                "INSERT INTO audio VALUES (?, ?)", [user_id, audio.file.read()]
            )

        for message in state.messages:
            util.store_user(file, message.message.author)

            attachments = ""

            for attachment in message.message.attachments:
                id = str(uuid4())
                attachments += id

                raw_data = requests.get(attachment.url).content

                file.execute(
                    "INSERT INTO attachments VALUES (?, ?, ?)",
                    [id, attachment.content_type, raw_data],
                )

            file.execute(
                "INSERT INTO messages VALUES (?, ?, ?, ?)",
                [
                    message.timestamp - state.start,
                    message.message.author.id,
                    message.message.content,
                    attachments,
                ],
            )

        file.close()
        file_connection.commit()
        file_connection.close()
