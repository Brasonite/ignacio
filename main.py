import data
from recording import RecordingState, RecordingFile, RecordedMessage
import time
from audio import TimestampedMP3Sink
import discord
from lang import lang
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


@bot.slash_command(name="help")
async def help(ctx: discord.ApplicationContext):
    await ctx.respond(lang(cache, ctx.guild.id).entry("help"))


@bot.slash_command(name="language")
@discord.option("id")
async def set_language(ctx: discord.ApplicationContext, id: str):
    data.setup_guild_cache(cache, ctx.guild.id)

    cache.execute(
        "UPDATE settings SET language=(?) WHERE guild=(?)", [id, ctx.guild.id]
    )

    await ctx.respond(lang(cache, ctx.guild.id).entry("language.set"))


@bot.slash_command(name="reset")
async def reset(ctx: discord.ApplicationContext):
    await ctx.defer()

    cache.execute("DELETE FROM settings WHERE guild=(?)", [ctx.guild.id])
    cache.execute("DELETE FROM tracked WHERE guild=(?)", [ctx.guild.id])

    guild_id = str(ctx.guild.id)

    for file in os.listdir(data.RECORDING_DIR):
        filename = os.fsdecode(file)

        if filename.startswith(guild_id):
            os.remove(f"{data.RECORDING_DIR}/{filename}")

    await ctx.respond(lang(cache, ctx.guild.id).entry("reset"))


@bot.slash_command(name="record")
async def record(ctx: discord.ApplicationContext):
    await ctx.defer()

    voice = ctx.author.voice

    if voice is None:
        await ctx.respond(
            lang(cache, ctx.guild.id).entry("recording.start.error.no_target")
        )
        return

    if not isinstance(voice.channel, discord.VoiceChannel):
        await ctx.respond(
            lang(cache, ctx.guild.id).entry("recording.start.error.invalid_target")
        )
        return

    vc = await voice.channel.connect()

    state = RecordingState(ctx.guild.id, vc, ctx.channel, time.time())
    recordings.update({ctx.guild.id: state})

    vc.start_recording(
        TimestampedMP3Sink(),
        save_recording,
        state,
        sync_start=True,
    )

    await ctx.respond(lang(cache, ctx.guild.id).entry("recording.start"))


@bot.slash_command(name="finish")
async def finish(ctx: discord.ApplicationContext):
    if ctx.guild.id in recordings:
        state = recordings.pop(ctx.guild.id)
        state.vc.stop_recording()

        await ctx.delete()
    else:
        await ctx.respond(
            lang(cache, ctx.guild.id).entry("recording.finish.error.no_recording")
        )


@bot.slash_command(name="watch")
async def watch(ctx: discord.ApplicationContext):
    if is_channel_tracked(ctx.channel.id):
        await ctx.respond(
            lang(cache, ctx.guild.id)
            .entry("watch.error.superfluous")
            .format(channel=ctx.channel.name)
        )
        return

    cache.execute(
        "INSERT OR IGNORE INTO tracked (id, guild) VALUES (?, ?)",
        [ctx.channel.id, ctx.guild.id],
    )

    await ctx.respond(
        lang(cache, ctx.guild.id).entry("watch").format(channel=ctx.channel.name)
    )


@bot.slash_command(name="unwatch")
async def unwatch(ctx: discord.ApplicationContext):
    if not is_channel_tracked(ctx.channel.id):
        await ctx.respond(
            lang(cache, ctx.guild.id)
            .entry("unwatch.error.superfluous")
            .format(channel=ctx.channel.name)
        )
        return

    cache.execute("DELETE FROM tracked WHERE id=(?)", [ctx.channel.id])

    await ctx.respond(
        lang(cache, ctx.guild.id).entry("unwatch").format(channel=ctx.channel.name)
    )


async def save_recording(sink: TimestampedMP3Sink, state: RecordingState):
    await sink.vc.disconnect()

    _ = RecordingFile(sink, state)

    await state.origin.send(
        lang(cache, state.origin.guild.id).entry("recording.finish")
    )


def is_channel_tracked(id: int) -> bool:
    return (
        cache.execute("SELECT COUNT(*) FROM tracked WHERE id=(?)", [id]).fetchone()[0]
        > 0
    )


def setup_cache():
    cache.execute(
        "CREATE TABLE IF NOT EXISTS settings (guild INTEGER NOT NULL PRIMARY KEY, language TINYTEXT)"
    )
    cache.execute(
        "CREATE TABLE IF NOT EXISTS tracked (id INTEGER NOT NULL PRIMARY KEY, guild INTEGER)"
    )


def main():
    setup_cache()
    bot.run(os.getenv("DISCORD_TOKEN"))

    cache.close()
    db_connection.commit()
    db_connection.close()


if __name__ == "__main__":
    main()
