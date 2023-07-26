import discord
from discord.ext.commands import Bot
from abc import ABCMeta, abstractmethod
from source.tools.web_tools import check_member_status


class base_event(metaclass=ABCMeta):
    '''
    Base event class that all event listeners should inherit from.
    ### Attributes
      `event`: The event to listen to (see discord.py docs). Defaults to name of subclass.\n
      `bot`: The `commands.Bot` instance of the bot.\n
      `guild_id`: The ID of the server. Note that this is an `int`.\n
    ### Methods
      `action`: The callback coroutine for when the command is invoked. Must be overridden.
      
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        self.event: str = self.__class__.__name__
        self.bot: Bot = bot
        self.config: dict = config

    @abstractmethod
    async def action(self):
        '''
        Must be implemented in subclass.
        '''
        pass

class on_ready(base_event):
    async def action(self):
        await self.bot.tree.sync(guild=discord.Object(self.config['server_id']))
        print('Ready!')

class on_member_join(base_event):
    async def action(self, member: discord.Member):
        if check_member_status(member):
            member.add_roles