import time
from audio import TimestampedMP3Sink
import data
import datetime
import discord
from discord.sinks import AudioData
from enum import Enum
from io import BytesIO
import os
import requests
import sqlite3
import util
from uuid import uuid4


class ChannelEventType(Enum):
    JOIN = 0
    LEAVE = 1


class RecordedChannelEvent:
    def __init__(self, type: ChannelEventType, user: int, timestamp: float):
        self.type = type
        self.user = user
        self.timestamp = timestamp


class RecordedMessage:
    def __init__(self, message: discord.Message, timestamp: float):
        self.message = message
        self.timestamp = timestamp


class RecordingState:
    def __init__(self, guild: int, vc, origin, start: float):
        self.guild = guild
        self.vc = vc
        self.origin = origin
        self.start = start

        self.messages: list[RecordedMessage] = []
        self.events: list[RecordedChannelEvent] = []

        for member in vc.channel.members:
            self.events.append(
                RecordedChannelEvent(ChannelEventType.JOIN, member.id, start)
            )

    def add_disconnect_events(self):
        now = time.time()

        for member in self.vc.channel.members:
            self.events.append(
                RecordedChannelEvent(ChannelEventType.LEAVE, member.id, now)
            )


class RecordingFile:
    def __init__(self, sink: TimestampedMP3Sink, state: RecordingState):
        now = time.time()

        dt = datetime.datetime.fromtimestamp(state.start)
        filename = f"{state.guild}_{dt.year}-{dt.month}-{dt.day}_{dt.hour}-{dt.minute}-{dt.second}.db"
        filepath = f"{data.RECORDING_DIR}/{filename}"

        if os.path.exists(filepath):
            os.remove(filepath)

        file_connection = sqlite3.connect(f"{data.RECORDING_DIR}/{filename}")
        file = file_connection.cursor()

        file.execute(
            "CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK (id = 1), guild INTEGER NOT NULL, length FLOAT, audio_start FLOAT)"
        )
        file.execute(
            "CREATE TABLE users (id INTEGER NOT NULL PRIMARY KEY, name TINYTEXT NOT NULL, display_name TINYTEXT NOT NULL, avatar MEDIUMBLOB NOT NULL, avatar_type TINYTEXT)"
        )
        file.execute(
            "CREATE TABLE audio (user INTEGER NOT NULL PRIMARY KEY, mime TINYTEXT NOT NULL, data MEDIUMBLOB NOT NULL)"
        )
        file.execute(
            "CREATE TABLE events (offset FLOAT NOT NULL, user INTEGER NOT NULL, type INTEGER NOT NULL)"
        )
        file.execute(
            "CREATE TABLE channels (id INTEGER NOT NULL PRIMARY KEY, name TINYTEXT NOT NULL)"
        )
        file.execute(
            "CREATE TABLE messages (offset FLOAT NOT NULL, user INTEGER NOT NULL, channel INTEGER NOT NULL, text TEXT, attachments TEXT)"
        )
        file.execute(
            "CREATE TABLE attachments (id TEXT NOT NULL PRIMARY KEY, mime TINYTEXT, data MEDIUMBLOB NOT NULL)"
        )

        if sink.start is not None and state.start is not None:
            file.execute(
                "INSERT INTO metadata VALUES (1, ?, ?, ?)",
                [state.guild, now - state.start, sink.start - state.start],
            )
        else:
            file.execute(
                "INSERT INTO metadata VALUES (1, ?, ?, 0)",
                [state.guild, now - state.start],
            )

        for user_id, audio in sink.audio_data.items():
            member: discord.Member = state.origin.guild.get_member(user_id)
            util.store_user(file, member)

            if not isinstance(audio, AudioData):
                continue

            if not isinstance(audio.file, BytesIO):
                continue

            file.execute(
                "INSERT INTO audio VALUES (?, ?, ?)",
                [user_id, "audio/mpeg", audio.file.read()],
            )

        for event in state.events:
            file.execute(
                "INSERT INTO events VALUES (?, ?, ?)",
                [event.timestamp - state.start, event.user, int(event.type.value)],
            )

        for message in state.messages:
            if isinstance(message.message.channel, discord.TextChannel):
                util.store_channel(file, message.message.channel)

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
                "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
                [
                    message.timestamp - state.start,
                    message.message.author.id,
                    message.message.channel.id,
                    message.message.content,
                    attachments,
                ],
            )

        file.close()
        file_connection.commit()
        file_connection.close()
