import discord
from discord.ext import tasks, commands
from abc import ABCMeta, abstractmethod
from datetime import datetime as dt, time


class BaseBackgroundTask(metaclass=ABCMeta):
    '''
    Base class that all background tasks should inherit from.\n
    A background task is a script executed at regular intervals,
    as opposed to needing to be invoked by a user.
    ### Class Attributes (no setup required)
      `bot`: The `commands.Bot` instance of the bot.\n
      `config`: The `json` config file containg relevant server information.
    ### Setup Required
      `action`: The coroutine running in the background. See the docs for `discord.ext.tasks`.
    Note that `action` behaves exactly like in the `Cog` examples in the `discord.py` docs.
    '''
    def __init__(self, *, bot: commands.Bot, config: dict) -> None:
        self.bot = bot
        self.config = config

    @tasks.loop()
    async def action(self):
        raise NotImplementedError(f'{self.__class__.__name__} failed to implement action.')

class test(BaseBackgroundTask):
    @tasks.loop(seconds=10)
    async def action(self):
        print('test')
