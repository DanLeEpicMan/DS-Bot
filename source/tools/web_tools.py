import discord
import gspread
import json
from datetime import datetime as dt


# everything related to checking member status
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
        if time_difference.seconds >= 3600: # update every hour
            self._users = set(self.open_by_key(SHEETS_CONFIG['sheet_id']).sheet1.col_values(SHEETS_CONFIG['user_column']))
            self.last_updated = now
        return self._users

SHEETS_CONFIG = json.load(open('secrets/sheets_config.json'))
GC: _CacheClient = gspread.service_account(filename='secrets/sheets_credentials.json', scopes=SHEETS_CONFIG['scopes'], client_factory=_CacheClient)

def check_member_status(member: discord.Member) -> bool:
    query = member.name if member.discriminator == '0' else f'{member.name}#{member.discriminator}' # to allow for legacy users
    return query in GC.users
    
