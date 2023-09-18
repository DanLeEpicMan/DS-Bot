import discord
from discord import ui, ButtonStyle, SelectOption
from discord.ext.commands import Bot
from source.tools.ui_helper import generate_embed
from abc import ABCMeta, abstractmethod
from source.tools.web_tools import check_member_status


class BaseView(ui.View):
    '''
    Sets the view to be persistent.
    '''
    def __init__(self, *, timeout: float | None = None):
        super().__init__(timeout=timeout)

class BasePersistentUI(metaclass=ABCMeta):
    '''
    Base class that all persistent UI buttons should inherit from.\n
    Persistent UI refers to `Buttons` that must always be active.\n
    While related, this is **not** a background task, since this
    needs to be invoked by a user. 
    ### Attributes (No setup required)
      `bot`: The `commands.Bot` instance of the bot.\n
      `config`: The `json` config file containg relevant server information.
    ### Setup Required
      `message`: The ID of the message that the UI will attach itself to.\n
      `view`: A `BaseView` object containing all UI objects.
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
        Must be overridden and return a subclass of `BaseView`
        '''
        pass

class Verify(BasePersistentUI):
    '''
    The verify button users can press to receive the member role.
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        super().__init__(bot=bot, config=config)
        self.member_role = discord.Object(config['member_role_id'])

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
            async def verify(view_self, interaction: discord.Interaction, button: ui.Button):
                await interaction.response.defer(ephemeral=True, thinking=True)
                member = interaction.user
                result = check_member_status(member)
                if result:
                    await member.add_roles(self.member_role)
                    await interaction.followup.send('Success!', ephemeral=True)
                else:
                    await interaction.followup.send("It doesn't seem like you're a member of Data Science UCSB. Please contact a board member if this is an error.", ephemeral=True)

        return VerifyView

class ClassRoleMenu(BasePersistentUI):
    def __init__(self, *, bot: Bot, config: dict) -> None:
        super().__init__(bot=bot, config=config)
        self.roles = {
            name: discord.Object(role_id)
            for name, role_id in self.config['roles_config']['class_roles'].items()
        }

    @property
    def message(self) -> int:
        return self.config['roles_config']['role_message']
    
    @property
    def view(self) -> BaseView:
        class RoleMenu(BaseView):
            @ui.select(
                options=[
                    SelectOption(label=name)
                    for name in self.roles
                ],
                placeholder='Choose your current class year!',
                custom_id='role-menu'
            )
            async def select_role(view_self, interaction: discord.Interaction, menu: discord.ui.Select):
                role = self.roles[menu.values[0]]
                await interaction.user.remove_roles(*self.roles.values())
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f'Successfully gave you {menu.values[0]}', ephemeral=True)

        return RoleMenu
