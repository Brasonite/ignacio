from discord.sinks import Filters, MP3Sink, WaveSink
import time


class TimestampedMP3Sink(MP3Sink):
    def __init(self, *, filters=None):
        super().__init__(filters=filters)

        self.start = None

    @Filters.container
    def write(self, data, user):
        super().write(data, user)

        if self.start is None:
            self.start = float(time.time())


class TimestampedWaveSink(WaveSink):
    def __init__(self, *, filters=None):
        super().__init__(filters=filters)

        self.start = None

    @Filters.container
    def write(self, data, user):
        super().write(data, user)

        if self.start is None:
            self.start = float(time.time())
