import data
from recording import RecordingState, RecordingFile, RecordedMessage
import time
from audio import TimestampedMP3Sink
import discord
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv("./.env")

bot = discord.Bot(intents=data.INTENTS)
recordings: dict[int, RecordingState] = {}

db_connection = sqlite3.connect(f"{data.DATA_DIR}/cache.db")
cache = db_connection.cursor()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.event
async def on_message(message: discord.Message):
    if not is_channel_tracked(message.channel.id):
        return

    state: RecordingState | None = recordings.get(message.guild.id)
    if state is not None:
        state.messages.append(RecordedMessage(message, time.time()))


@bot.slash_command(name="record")
async def record(ctx: discord.ApplicationContext):
    await ctx.defer()

    voice = ctx.author.voice

    if voice is None:
        await ctx.respond("You are not in a voice channel.")
        return

    if not isinstance(voice.channel, discord.VoiceChannel):
        await ctx.respond("The channel you're in is not a voice channel.")
        return

    vc = await voice.channel.connect()

    state = RecordingState(vc, ctx.channel, time.time())
    recordings.update({ctx.guild.id: state})

    vc.start_recording(
        TimestampedMP3Sink(),
        save_recording,
        state,
        sync_start=True,
    )

    await ctx.respond("Recording started.")


@bot.slash_command(name="finish")
async def finish(ctx: discord.ApplicationContext):
    if ctx.guild.id in recordings:
        state = recordings.pop(ctx.guild.id)
        state.vc.stop_recording()

        await ctx.delete()
    else:
        await ctx.respond("I am currently not recording here.")


@bot.slash_command(name="watch")
async def watch(ctx: discord.ApplicationContext):
    if is_channel_tracked(ctx.channel.id):
        await ctx.respond(f"Channel **{ctx.channel.name}** is already being tracked.")
        return

    cache.execute(
        "INSERT OR IGNORE INTO tracked (id, guild) VALUES (?, ?)",
        [ctx.channel.id, ctx.guild.id],
    )

    await ctx.respond(f"Tracking channel **{ctx.channel.name}**")


@bot.slash_command(name="unwatch")
async def unwatch(ctx: discord.ApplicationContext):
    if not is_channel_tracked(ctx.channel.id):
        await ctx.respond(
            f"Channel **{ctx.channel.name}** is already not being tracked."
        )
        return

    cache.execute("DELETE FROM tracked WHERE id=(?)", [ctx.channel.id])

    await ctx.respond(f"Untracking channel **{ctx.channel.name}**")


async def save_recording(sink: TimestampedMP3Sink, state: RecordingState):
    await sink.vc.disconnect()

    _ = RecordingFile(sink, state)

    await state.origin.send(f"Finished recording.")


def is_channel_tracked(id: int) -> bool:
    return (
        cache.execute("SELECT COUNT(*) FROM tracked WHERE id=(?)", [id]).fetchone()[0]
        > 0
    )


def setup_cache():
    cache.execute(
        "CREATE TABLE IF NOT EXISTS tracked(id INTEGER NOT NULL PRIMARY KEY, guild INTEGER)"
    )


def main():
    setup_cache()
    bot.run(os.getenv("DISCORD_TOKEN"))

    cache.close()
    db_connection.commit()
    db_connection.close()


if __name__ == "__main__":
    main()
