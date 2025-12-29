# Ignácio

**Ignácio** is an easy to use Discord bot for call recording. As well as recording each person's voice individually, it also records messages sent in marked channels, including attachments such as images images and audio files.

# Usage

## Discord app and bot user

In order to use Ignácio, you first need to create a Discord app and bot user.

The bot needs to have the "Sever Members" and "Message Content" priviledged intents enabled in order to work.

The recommended permissions integer is `1166336`, which amounts to the following permissions:

- Attach files.
- Connect.
- Embed Links.
- Read Message History.
- Send Messages.
- View Channels.

These can be set in the "Default Install Settings" section, where the `applications.commands` and `bot` scopes must also be set.

Other than that, you can customize the bot to be however you prefer.

## Running Ignácio

Ignacio uses the [UV](https://github.com/astral-sh/uv) project manager. Thus, it is highly recommended to use it.

To install and run Ignácio, simply run:

```Bash
git clone https://github.com/Brasonite/ignacio.git
cd ignacio
uv run main.py
```

This will install all dependencies and start the bot, **provided a `.env` file was correctly setup**.

The `.env` file must contain the bot token:

```
DISCORD_TOKEN = (token goes here)
``` 

## Saved recordings

Recordings are saved as a SQLite 3 database at the user's config dir. This is `%APPDATA%/Brasonite/ignacio/recordings` on Windows.

For a description of how these files are organized, have a look at [`recording.sql`](/schemas/recording.sql).

If you wish to extract the recorded data from the recording file, you must either use the SQLite CLI or write your own code to do so.

# License

This project is licensed under the GNU General Public License version 3 ([LICENSE](/LICENSE) or https://opensource.org/license/gpl-3-0).