import json
import os
import discord
from discord.ext import commands
from source.slash_commands import BaseCommand
from source.events import BaseEvent
from source.persistent_ui import BasePersistentUI
from source.background_tasks import BaseBackgroundTask


# load the config file, create relevant objects
with open('secrets/config.json') as file:
    config = json.load(file)
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

# set up persistent UI listeners and background tasts
@bot.event
async def setup_hook():
    for ui_class in BasePersistentUI.__subclasses__():
        try:
            ui = ui_class(bot=bot, config=config)
        except TypeError as e:
            raise NotImplementedError(f'{ui_class.__name__} failed to implement either view or message property') from e
        
        bot.add_view(ui.view(), message_id=ui.message)

# sync commands and start background tasks
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(config['server_id']))
    for task_class in BaseBackgroundTask.__subclasses__():
        task = task_class(bot=bot, config=config)
        task.action.start()
    print('Ready!')

# finally, run the bot.
bot.run(os.environ['DS-OAUTH-KEY'])
