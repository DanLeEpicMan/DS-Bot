import json
import os
from time import sleep
from linkedin_jobs_scraper import LinkedinScraper as Scraper
from linkedin_jobs_scraper.events import Events, EventData
from linkedin_jobs_scraper.query import Query, QueryFilters, QueryOptions
from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, TypeFilters, ExperienceLevelFilters

with open(r'secrets/scraper_config.json') as file:
    SCRAPER_CONFIG = json.load(file)

DEFAULT_QUERY = [
    Query(
        query=query['search'],
        options=QueryOptions(
            locations=query['locations'],
            skip_promoted_jobs=query['skip_promoted'],
            page_offset=query['pages_to_skip'],
            limit=query['amount_to_scrape'],
            apply_link=query['get_apply_link'],
            filters=QueryFilters(
                relevance=getattr(RelevanceFilters, query['relevance']),
                time=getattr(TimeFilters, query['time']),
                type=[getattr(TypeFilters, item) for item in query['type']],
                experience=[getattr(ExperienceLevelFilters, item) for item in query['experience']]
            )
        )
    )
    for query in SCRAPER_CONFIG['queries']
]

class _StatusTracker:
    '''
    To track the number of completed queries
    '''
    def __init__(self) -> None:
        self.queries_finished = 0
        
    def done(self):
        self.queries_finished += 1

SCRAPER = Scraper(
    chrome_executable_path=SCRAPER_CONFIG['chromedriver'], 
    max_workers=SCRAPER_CONFIG['concurrent_chrome_instances'], 
    slow_mo=SCRAPER_CONFIG['http_slow_down'],  # Slow down (in seconds)
    page_load_timeout=SCRAPER_CONFIG['page_load_timeout']  
)

def scrape(query: Query | list[Query] = DEFAULT_QUERY) -> list[EventData]:
    '''
    Returns a list of EventData scraped from LinkedIn using the given query (or list of queries).

    Note that this is a synchronous function, since the scraper package is built with `requests`.
    It's advisable to run this in a background thread.

    If no query is provided, then the default query found in `secrets/scraper_config.json` is used.
    '''
    if isinstance(query, Query):
        query = [query]
    jobs = []
    status = _StatusTracker()

    def on_data(item: EventData):
        print('[ON DATA]', item.title)
        jobs.append(item)

    def on_end():
        print('[END QUERY]', query[status.queries_finished].query)
        status.done()

    SCRAPER.on(Events.DATA, on_data)
    SCRAPER.on(Events.END, on_end)
    SCRAPER.run(queries=query)

    while status.queries_finished != len(query):
        sleep(SCRAPER_CONFIG['sleep_duration'])
    
    print('[END SCRAPING]')
    return jobs