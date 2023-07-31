import discord
from discord.ext.commands import Bot
from abc import ABCMeta, abstractmethod


class BaseCommand(metaclass=ABCMeta):
    '''
    The base class that all server commands are expected to inherit from. 
    ### Attributes
      `name`: The name of the command. Defaults to the name of the subclass.\n
      `desc`: The description of the command. Defaults to the docstring of the subclass.\n
      `bot`: The `commands.Bot` instance of the bot.\n
      `config`: The `json` config file containg relevant server information.
    ### Methods
      `action`: The callback coroutine for when the command is invoked. Must be overridden.
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        self.name: str = self.__class__.__name__
        self.desc: str = self.__class__.__doc__
        self.bot: Bot = bot
        self.config: dict = config

    @abstractmethod
    async def action(self, interaction: discord.Interaction) -> None:
        '''
        Must be implemented in subclass.
        '''
        pass

class ping(BaseCommand):
    '''
    Returns the latency of the bot in miliseconds.
    '''
    async def action(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'{round(self.bot.latency, 2) * 1000} ms', ephemeral=True)
