import discord
import asyncio
import aiohttp
import json
from datetime import datetime as dt
from time import sleep
import gspread
from linkedin_jobs_scraper import LinkedinScraper as Scraper
from linkedin_jobs_scraper.events import Events, EventData
from linkedin_jobs_scraper.query import Query, QueryFilters, QueryOptions
from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, TypeFilters, ExperienceLevelFilters

# ---------------------------------------
#             Member Status
# ---------------------------------------
class _CacheClient(gspread.Client):
    '''
    Adds additional parameters and methods to `Client` to allow for easy caching.
    '''
    def __init__(self, auth, session=None):
        super().__init__(auth, session)
        self.last_updated = dt.now()
        self._users = set(self.open_by_key(SHEETS_CONFIG['sheet_id']).sheet1.col_values(SHEETS_CONFIG['user_column']))

    @property
    def users(self) -> set[str]:
        now = dt.now()
        time_difference = now - self.last_updated
        if time_difference.total_seconds() >= 3600: # update every hour
            self._users = set(self.open_by_key(SHEETS_CONFIG['sheet_id']).sheet1.col_values(SHEETS_CONFIG['user_column']))
            self.last_updated = now
        return self._users

with open('secrets/sheets_config.json') as file:
    SHEETS_CONFIG = json.load(file)
GC: _CacheClient = gspread.service_account(filename='secrets/sheets_credentials.json', scopes=SHEETS_CONFIG['scopes'], client_factory=_CacheClient)

def check_member_status(member: discord.Member) -> bool:
    query = member.name if member.discriminator == '0' else f'{member.name}#{member.discriminator}' # to allow for legacy users
    return query in GC.users
    
# ---------------------------------------
#               Scraping
# ---------------------------------------

DEFAULT_QUERY = Query(
    query='Data Analyst',
    options=QueryOptions(
        locations=['California'],
        skip_promoted_jobs=True,  # Skip promoted jobs. Default to False.
        page_offset=2,  # How many pages to skip
        limit=2, # number of jobs to scrape
        filters=QueryFilters(              
            relevance=RelevanceFilters.RECENT,
            time=TimeFilters.MONTH,
            type=[TypeFilters.FULL_TIME, TypeFilters.INTERNSHIP],
            experience=[ExperienceLevelFilters.INTERNSHIP, ExperienceLevelFilters.ENTRY_LEVEL]
        )
    )
)

def scrape(*, query: Query | list[Query] = DEFAULT_QUERY) -> list[EventData]:
    '''
    Returns a list of EventData scraped from LinkedIn using the given query (or list of queries).

    Note that this is a synchronous function, since the scraper package is built with `requests`.
    It's advisable to run this in a background thread.

    If no query is provided, then the following default query is used
    ```
    search = 'Data Analyst'
    locations = 'California'
    skip_promoted = True
    start_page = 2
    jobs_to_collect = 2
    filters = {
        Sort By = 'MOST RECENT'
        Date Posted = 'PAST MONTH'
        Experience Level = 'INTERNSHIP', 'ENTRY LEVEL'
        Job Type = 'INTERNSHIP', 'FULL TIME'
    }
    ```
    '''
    # set up some variables
    jobs = []
    scraper = Scraper(
        chrome_executable_path=r'driver/chromedriver', 
        max_workers=1, 
        slow_mo=30,  # Slow down (in seconds)
        page_load_timeout=40  
    )
    # create a 'StatusTracker', whose sole purpose is to hold a boolean
    # and modify said boolean from False to True
    class StatusTracker:
        finished = False
        def done(self):
            self.finished = True

    # set up relevant events
    status = StatusTracker()

    def on_data(item: EventData):
        print('[ON DATA]', item.title)
        jobs.append(item)

    def on_end():
        print('[END SCRAPING]')
        status.done()

    scraper.on(Events.DATA, on_data)
    scraper.on(Events.END, on_end)

    scraper.run(queries=query)

    while not status.finished:
        sleep(10)
    
    return jobs
