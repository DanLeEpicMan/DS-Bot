import discord
from discord import ui, ButtonStyle, SelectOption
from discord.ui import View
from discord.ext.commands import Bot
from source.tools.ui_helper import generate_embed
from abc import ABCMeta, abstractmethod
from source.tools.web_tools import check_member_status
from source.shared_features import SupportModal


class BasePersistentUI(metaclass=ABCMeta):
    '''
    Base class that all persistent UI buttons should inherit from.\n
    Persistent UI refers to `Buttons` that must always be active.\n
    While related, this is **not** a background task, since this
    needs to be invoked by a user. 

    **Note**: The UI must already exist in Discord in order for
    the library to attach a listener. See the comment under the
    `message` attribute.

    ## Attributes
    ### No Setup Required
      `bot`: The `commands.Bot` instance of the bot.\n
      `config`: The `json` config file containg relevant server information.
    ### Setup Required
      `message`: The ID of the message that the UI will attach itself to.
      **This must be an existing message with the UI already attached.**
      Use an ad hoc script with empty callbacks to achieve this.\n
      `view`: A `BaseView` object containing all UI objects. 
      **Note that every component MUST have a custom id.**
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
    def view(self) -> type[View]:
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
        self.member_role = discord.Object(config['verify_config']['role'])

    @property
    def message(self) -> int:
        return self.config['verify_config']['message_id']
    
    @property
    def view(self) -> type[View]:
        class VerifyView(View):
            @ui.button(
                label='Verify', 
                style=ButtonStyle.blurple,
                custom_id=f'verify-button-{self.config["server_id"]}'
            )
            async def verify(view_self, interaction: discord.Interaction, button: ui.Button):
                await interaction.response.defer(ephemeral=True, thinking=True)
                member = interaction.user
                result = check_member_status(member)
                if result:
                    await member.add_roles(self.member_role)
                    await interaction.followup.send('Success!', ephemeral=True)
                else:
                    await interaction.followup.send("It doesn't seem like you're a member of Data Science UCSB. If you believe this is an error, open a support ticket.", ephemeral=True)

        return VerifyView

class ClassRoleMenu(BasePersistentUI):
    '''
    The menu to select class roles (Freshman, Sophomore, ...).
    As much as I want to use the `RoleMenu` class, I must use a default `SelectMenu`, 
    since `RoleMenu` displays every role in the server and can't be changed.
    
    To update existing roles, modify the 'class_roles_config' portion in the config file.
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        super().__init__(bot=bot, config=config)
        self.roles = {
            name: discord.Object(role_id)
            for name, role_id in self.config['class_roles_config']['roles'].items()
        }

    @property
    def message(self) -> int:
        return self.config['class_roles_config']['message_id']
    
    @property
    def view(self) -> type[View]:
        class RoleMenu(View):
            @ui.select(
                options=[
                    SelectOption(label=name)
                    for name in self.roles
                ],
                placeholder='Choose your current class year!',
                custom_id=f'role-menu-{self.config["server_id"]}'
            )
            async def select_role(view_self, interaction: discord.Interaction, menu: discord.ui.Select):
                await interaction.response.defer(ephemeral=True, thinking=True) # sometimes it takes a while to remove roles
                role = self.roles[menu.values[0]]
                await interaction.user.remove_roles(*self.roles.values())
                await interaction.user.add_roles(role)
                await interaction.followup.send(f'Successfully gave you {menu.values[0]}', ephemeral=True)

        return RoleMenu

class AnnouncementButton(BasePersistentUI):
    '''
    A button giving a self-assignable role for announcements.
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        super().__init__(bot=bot, config=config)
        self.role = discord.Object(self.config['announcement_role_config']['role'])

    @property
    def message(self) -> int:
        return self.config['announcement_role_config']['message_id']
    
    @property
    def view(self) -> type[View]:
        class AnnounceView(View):
            @ui.button(
                label='Opt In/Out',
                style=ButtonStyle.red,
                custom_id=f'announcement-button-{self.config["server_id"]}'
            )
            async def give_announce_role(view_self, interaction: discord.Interaction, button: ui.Button):
                member = interaction.user
                if member.get_role(self.role.id):
                    await member.remove_roles(self.role)
                    await interaction.response.send_message('Successfully opted out of announcements.', ephemeral=True)
                else:
                    await member.add_roles(self.role)
                    await interaction.response.send_message('Successfully opted into announcements.', ephemeral=True)

        return AnnounceView

class HelpButton(BasePersistentUI):
    '''
    A button prompting a support ticket.
    '''
    @property
    def message(self) -> int:
        return self.config['help_config']['message_id']
    
    @property
    def view(self) -> type[View]:
        class HelpView(View):
            @ui.button(
                label='Help',
                style=ButtonStyle.green,
                custom_id=f'support-button-{self.config["server_id"]}'
            )
            async def help_button(view_self, interaction: discord.Interaction, button):
                channel = self.bot.get_channel(self.config['help_config']['channel'])
                await interaction.response.send_modal(SupportModal(channel=channel))

        return HelpView