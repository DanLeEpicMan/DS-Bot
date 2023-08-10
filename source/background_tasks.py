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
        self.color_keys = {
            'Data Analyst': 0xd1ad0d,
            'Data Scientist': 0x2b5fb3
        }

    def parse_insights(self, insights: list[str]) -> list[dict]:
        '''
        Given an insight from LinkedIn, parse it into a fields list.
        '''
        fields = [
            {
                'name': 'Salary & Job Type' if '$' in insights[0] else 'Job Type', # include 'Salary' in title if the salary is given
                'value': insights[0].replace(' (from job description)', '') # remove the "from job desc" bit
            },
            {
                'name': 'Size & Industry',
                'value': insights[1]
            }
        ]
        for insight in insights[2:]: # first two elements are always the same
            if 'alum' in insight:
                fields.append({
                    'name': 'Alumni',
                    'value': insight
                })
            elif 'Skills' in insight:
                fields.append({
                    'name': 'Skills',
                    'value': insight[8:] # skips 'Skills: '
                })

        return fields

    @tasks.loop(hours=168)
    async def action(self):
        if self.channel is None:
            self.channel = await self.bot.fetch_channel(self.config['scraper_channel'])

        jobs = await self.bot.loop.run_in_executor(None, scrape)
        for job in jobs:
            await self.channel.send(embed=generate_embed({
                'author': {
                    'name': job.company,
                    'url': job.company_link,
                    'icon_url': job.company_img_link
                },
                'color': self.color_keys.get(job.query, 0x072c59),
                'title': job.title,
                'fields': [{
                    'name': 'Location',
                    'value': job.place
                }] + self.parse_insights(job.insights),
                'url': job.link,
                'timestamp': dt.fromisoformat(job.date)
            }))
            await asyncio.sleep(0.5)
