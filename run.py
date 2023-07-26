import json
import os
import discord
from discord.ext import commands
from source.slash_commands import BaseCommand
from source.events import BaseEvent
from source.persistent_ui import BasePersistentUI

TEST_MODE = True


# load the config file, create relevant objects
config = json.load(open(
    'test_config.json' if TEST_MODE else 'config.json'
))
guild = discord.Object(config['server_id'])

# create bot instances
bot = commands.Bot(command_prefix='$', intents=discord.Intents.all(), help_command=None)
tree = bot.tree

# set up server slash commands
for cmd_class in BaseCommand.__subclasses__():
    try:
        cmd = cmd_class(bot=bot, config=config)
    except TypeError as e:
        raise NotImplementedError(f'{cmd_class.__name__} failed to implement action method') from e

    tree.command(name=cmd.name, description=cmd.desc, guild=guild)(cmd.action)

# set up events
for event_class in BaseEvent.__subclasses__():
    try:
        event = event_class(bot=bot, config=config)
    except TypeError as e:
        raise NotImplementedError(f'{cmd_class.__name__} failed to implement action method') from e

    setattr(bot, event.event, event.action)

# set up persistent UI listeners
# even though this can technically work in 'events.py',
# i feel that it's best to include it here due to its nature
@bot.event
async def setup_hook():
    for ui_class in BasePersistentUI.__subclasses__():
        try:
            ui = ui_class(bot=bot, config=config)
        except TypeError as e:
            raise NotImplementedError(f'{ui_class.__name__} failed to implement either view or message property') from e
        
        bot.add_view(ui.view(), message_id=ui.message)

# finally, run the bot.
bot.run(os.environ['DS-OAUTH-KEY'])
