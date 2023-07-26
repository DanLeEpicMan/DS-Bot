import discord
from discord import ui, ButtonStyle
from discord.ext.commands import Bot
from source.tools.ui_helper import generate_embed
from abc import ABCMeta, abstractmethod


class BaseView(ui.View):
    '''
    Sets the view to be persistent.
    '''
    def __init__(self, *, timeout: float | None = None):
        super().__init__(timeout=timeout)

class BasePersistentUI(metaclass=ABCMeta):
    '''
    Base class that all persistent UI buttons should inherit from.
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        self.bot = bot
        self.config = config

    @property
    @abstractmethod
    def message(self) -> int:
        '''
        Must be overridden and return an int of a message ID.
        '''
        pass
    
    @property
    @abstractmethod
    def view(self) -> BaseView:
        '''
        Must be overridden and return a subclass of `ui.View`
        '''
        pass

class Verify(BasePersistentUI):
    @property
    def message(self) -> int:
        return self.config['verify_message']
    
    @property
    def view(self) -> BaseView:
        class VerifyView(BaseView):
            @ui.button(
                label='Verify', 
                style=ButtonStyle.blurple,
                custom_id='verify-button'
            )
            async def verify(self, interaction: discord.Interaction, button: ui.Button):
                await interaction.response.send_message('Pressed!', ephemeral=True)


        return VerifyView
