import discord
import asyncio
from discord.ext import tasks, commands
from abc import ABCMeta, abstractmethod
from datetime import datetime as dt, time
from source.tools.web_tools import scrape, EventData
from source.tools.ui_helper import generate_embed

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

    @tasks.loop(hours=24)
    async def action(self):
        raise NotImplementedError(f'{self.__class__.__name__} failed to implement action.')
    
class Scraper(BaseBackgroundTask):
    def __init__(self, *, bot: commands.Bot, config: dict) -> None:
        super().__init__(bot=bot, config=config)
        self.channel = None

    @tasks.loop(hours=168)
    async def action(self):
        if self.channel is None:
            self.channel = await self.bot.fetch_channel(self.config['scraper_channel'])

        jobs = await self.bot.loop.run_in_executor(None, scrape)
        for job in jobs:
            generate_embed
            embed = {
                'title': job.title,
                'description': job.description if len(job.description) < 256 else job.description[:253] + "...",
                'url': job.link,
                'footer': {
                    'text': job.company,
                    'icon_url': job.company_img_link
                },
                'color': 0x2b5fb3
            }
            await self.channel.send(embed=generate_embed(embed))
