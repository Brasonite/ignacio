import discord
import os
import platformdirs

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True
INTENTS.messages = True
INTENTS.voice_states = True

DATA_DIR = platformdirs.user_config_dir(
    "ignacio", "Brasonite", roaming=True, ensure_exists=True
)
RECORDING_DIR = f"{DATA_DIR}/recordings"

if not os.path.exists(RECORDING_DIR):
    os.makedirs(RECORDING_DIR)
