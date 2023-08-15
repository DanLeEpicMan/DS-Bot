import discord
import asyncio
import json
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
        with open('secrets/scraper_config.json') as file:
            SCRAPER_CONFIG = json.load(file)

        self.color_keys = {
            query['search']: int(query['embed_color'], base=16)
            for query in SCRAPER_CONFIG['queries']
        }
        self.default_color = int(SCRAPER_CONFIG['default_embed_color'], base=16)

    def parse_insights(self, insights: list[str]) -> list[dict]:
        '''
        Given an insight from LinkedIn, parse it into a fields list.
        '''
        fields = []

        # first parse salary and job type
        if '$' in insights[0]: # if the salary is given
            salary_and_job = insights[0].split(' · ', 1)
            fields.append({
                'name': 'Salary',
                'value': salary_and_job[0].replace(' (from job description)', '') # remove the "from job desc" bit
            })
            fields.append({
                'name': 'Job Type',
                'value': salary_and_job[1]
            })
        else:
            fields.append({
                'name': 'Job Type',
                'value': insights[0]
            })

        # next, parse size and industry
        size_and_industry = insights[1].split(' · ', 1) # this can be of varying sizes, so a for-loop is necessary
        for item in size_and_industry:
            if 'employee' in item:
                fields.append({
                    'name': 'Size',
                    'value': item
                })
            else:
                fields.append({
                    'name': 'Industry',
                    'value': item
                })

        # finally, parse remaining information that might not always be present
        for insight in insights[2:]:
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
            fields = [
                {
                    'name': 'Location',
                    'value': job.place
                }
            ] + self.parse_insights(job.insights)
            await self.channel.send(embed=generate_embed({
                'author': {
                    'name': job.company,
                    'url': job.company_link,
                    'icon_url': job.company_img_link
                },
                'color': self.color_keys.get(job.query, self.default_color),
                'title': job.title,
                'fields': fields,
                'url': job.link,
                'timestamp': dt.fromisoformat(job.date)
            }))
            await asyncio.sleep(0.5)
