'''
Due to hosting limitations, the scraper must be ran as a manual script.
'''
import discord
import asyncio
import json
import re
from discord.ext import commands
from scraper_tools.web import scrape, EventData, SCRAPER_CONFIG
from source.tools.ui_helper import generate_embed

with open('secrets/real_config.json') as file:
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

    The logic here isn't pretty. I won't try to defend it; this is just an amalgamation of multiple months of code.
    '''
    fields = []

    # first parse salary and job type
    salary_and_job = insights[0].split(' · ', 1)
    for item in salary_and_job: # sometimes there is no identifiable delimiter, so a for-loop is necessary
        if '$' in item:
            # the purpose of check_list is to handle something like 
            # $82,600/yr - $153,100/yr (from job description) On-site Full-time Entry level
            # i.e. improper delimiter.
            # first, split (from job description). if the list isn't a singleton, then we're in the above case.
            check_list = item.split('(from job description)') 
            if len(check_list) > 1:
                fields.append({
                    'name': 'Salary',
                    'value': check_list[0].strip()
                })
                fields.append({
                    'name': 'Job Type',
                    'value': check_list[1].strip()
                })
                break

            fields.append({
                'name': 'Salary',
                'value': item.replace(' (from job description)', '') # remove the "from job desc" bit
            })
        else:
            fields.append({
                'name': 'Job Type',
                'value': item
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
        try:
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
        except Exception as e:
            print(job.insights, e, sep='\n')

# prepare the bot
bot = commands.Bot(command_prefix='$', intents=discord.Intents.all(), help_command=None)

@bot.event
async def on_ready():
    channel = await bot.fetch_channel(channel_id)
    jobs = await bot.loop.run_in_executor(None, scrape)
    await send_messages(channel, jobs)
    await bot.close()

with open('secrets/bot_key.json') as file:
    key = json.load(file)['key']

bot.run(key)
