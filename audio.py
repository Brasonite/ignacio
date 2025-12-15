from discord.sinks import Filters, WaveSink
import discord
import time


class TimestampedWaveSink(WaveSink):
    def __init__(self, *, filters=None):
        if filters is None:
            filters = discord.sinks.core.default_filters
        self.filters = filters
        Filters.__init__(self, **self.filters)

        self.encoding = "wav"
        self.vc = None
        self.audio_data = {}

        self.start = None

    @Filters.container
    def write(self, data, user):
        super().write(data, user)

        if self.start is None:
            self.start = float(time.time())
