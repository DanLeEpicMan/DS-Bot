'''
Due to hosting limitations, the scraper must be ran as a manual script.
'''
import discord
import asyncio
import json
import re
import os
from discord.ext import commands
from scraper_tools.web import scrape, EventData, SCRAPER_CONFIG
from source.tools.ui_helper import generate_embed

with open('secrets/config.json') as file:
    channel_id = json.load(file)['scraper_channel']

# set up colors for each query
color_keys = {
    query['search']: int(query['embed_color'], base=16)
    for query in SCRAPER_CONFIG['queries']
}
default_color = int(SCRAPER_CONFIG['default_embed_color'], base=16)

# define relevant functions
def parse_insights(insights: list[str]) -> list[dict]:
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

async def send_messages(channel: discord.TextChannel, jobs: list[EventData], /):
    for job in jobs:
        embed = generate_embed({
            'author': {
                'name': job.company,
                'url': job.company_link,
                'icon_url': job.company_img_link
            },
            'color': color_keys.get(job.query, default_color),
            'title': ' '.join(re.sub(r'\([^)]*\)|[\-\|\/\\](.*)', '', job.title).split()), # regex removes everything between parentheses, and everything after -|/\
            'fields': [{
                'name': 'Location',
                'value': job.place
            }] + parse_insights(job.insights),
            'url': job.link
        })

        view = None
        if job.apply_link: # if it's not empty
            view = discord.ui.View(timeout=None).add_item(discord.ui.Button(label='Apply', url=job.apply_link))

        await channel.send(embed=embed, view=view)
        await asyncio.sleep(0.5)

# prepare the bot
bot = commands.Bot(command_prefix='$', intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_ready():
    channel = await bot.fetch_channel(channel_id)
    jobs = await bot.loop.run_in_executor(None, scrape)
    await send_messages(channel, jobs)
    await bot.close()

bot.run(os.environ['DS_OAUTH_KEY'], log_handler=None)
