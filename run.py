import aiohttp
import asyncio
import json
import discord
from discord import app_commands
from discord.ext import commands
from source.commands.server_commands import base_server_command
from source.events import base_event


# load the config file, create relevant objects
config = json.load(open('config.json'))
guild = discord.Object(config['server_id'])

# create bot instances
bot = commands.Bot(command_prefix='$', intents=discord.Intents.all(), help_command=None)
tree = bot.tree

# set up server slash commands
for cmd_class in base_server_command.__subclasses__():
    try:
        cmd = cmd_class(bot=bot, guild_id=guild.id)
    except TypeError as e:
        raise NotImplementedError(f'{cmd_class.__name__} failed to implement action method') from e

    tree.command(name=cmd.name, description=cmd.desc, guild=guild)(cmd.action)

# set up events
for event_class in base_event.__subclasses__():
    try:
        event = event_class(bot=bot, guild_id=guild.id)
    except TypeError as e:
        raise NotImplementedError(f'{cmd_class.__name__} failed to implement action method') from e

    setattr(bot, event.event, event.action)

# finally, prepare the bot.

# i think it's best to keep this here :)

bot.run(config['oauth_token'])
