import discord
from discord.ext.commands import Bot
from abc import ABCMeta, abstractmethod
from source.tools.web_tools import check_member_status


class BaseEvent(metaclass=ABCMeta):
    '''
    Base event class that all event listeners should inherit from.
    ### Attributes (No setup required)
      `event`: The event to listen to (see discord.py docs). Defaults to name of subclass.\n
      `bot`: The `commands.Bot` instance of the bot.\n
      `config`: The `json` config file containg relevant server information.
    ### Setup Required
      `action`: The callback coroutine for when the command is invoked. Must be overridden.
      
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        self.event = getattr(self, 'event', self.__class__.__name__)
        self.bot = bot
        self.config = config

    @abstractmethod
    async def action(self):
        '''
        Must be implemented in subclass.
        '''
        pass
    
class on_member_join(BaseEvent):
    '''
    Check if a new user is a member of DS UCSB.
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        super().__init__(bot=bot, config=config)
        self.member_role = discord.Object(config['verify_config']['role'])
    
    async def action(self, member: discord.Member):
        if check_member_status(member):
            await member.add_roles(self.member_role)
        else:
            await member.send("You're not a member!")