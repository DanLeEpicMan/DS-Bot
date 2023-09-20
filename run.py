import json
import discord
from discord.app_commands import Command, Group, ContextMenu, guild_only
from discord.ext import commands
from source.slash_commands import BaseCommand, BaseGroup
from source.context_menu import BaseContextMenu
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

def check_implementation(cls, **kwargs):
    '''
    Attempt to initialize a given class.\n
    If successful, return an instance. Otherwise, raise an exception.
    '''
    try:
        return cls(**kwargs)
    except TypeError as e:
        raise NotImplementedError(f'{cls.__name__} failed to override abstract method.') from e

# set up server slash commands
@guild_only
class GuildGroup(Group):
    pass

@guild_only
class GuildCommand(Command):
    pass

for group_class in BaseGroup.__subclasses__():
    group = check_implementation(group_class)
    guild_group = GuildGroup(name=group.name, description=group.desc)

    for cmd_class in group.commands:
        cmd_class._is_registered = True
        cmd = check_implementation(cmd_class, bot=bot, config=config)
        guild_group.add_command(GuildCommand(name=cmd.name, description=cmd.desc, callback=cmd.action))    
    
    tree.add_command(guild_group, guild=guild)

for cmd_class in BaseCommand.__subclasses__():
    if cmd_class._is_registered: continue

    cmd = check_implementation(cmd_class, bot=bot, config=config)
    tree.add_command(
        GuildCommand(name=cmd.name, description=cmd.desc, callback=cmd.action), 
        guild=guild
    )

@guild_only
class GuildContext(ContextMenu):
    pass

# set up context menus
for ctx_class in BaseContextMenu.__subclasses__():
    ctx = check_implementation(ctx_class, bot=bot, config=config)
    
    tree.add_command(
        GuildContext(name=ctx.name, callback=ctx.action),
        guild=guild
    )

# set up events
for event_class in BaseEvent.__subclasses__():
    event = check_implementation(event_class, bot=bot, config=config)
    setattr(bot, event.event, event.action)

# set up persistent UI listeners and background tasts
@bot.event
async def setup_hook():
    for ui_class in BasePersistentUI.__subclasses__():
        ui = check_implementation(ui_class, bot=bot, config=config)
        bot.add_view(ui.view(timeout=None), message_id=ui.message)

# sync commands and start background tasks
@bot.event
async def on_ready():
    await bot.tree.sync(guild=guild)
    for task_class in BaseBackgroundTask.__subclasses__():
        task = task_class(bot=bot, config=config)
        task.action.start()
    print('Ready!')

# finally, run the bot
with open('secrets/bot_key.json') as file:
    key = json.load(file)['key']

bot.run(key)
