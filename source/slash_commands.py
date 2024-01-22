from abc import ABCMeta, abstractmethod
import discord
from discord import ui
from discord.app_commands import describe, rename
from discord.ext.commands import Bot
from discord.interactions import Interaction
from source.tools.ui_helper import generate_embed, make_fail_embed
from source.tools.shared_features import SupportModal, HelpInfo


class BaseCommand(metaclass=ABCMeta):
    '''
    The base class that all server commands are expected to inherit from.\n
    If you wish to add a description or rename a command, please use the `describe`
    or `rename` decorators, respectively.
    ## Attributes
    ### Configurable
      `name`: The name of the command. Defaults to what's given by `help_info`.\n
      `desc`: The description of the command. Defaults to what's given by `help_info`.\n
    ### Unconfigurable
      `bot`: The `commands.Bot` instance of the bot.\n
      `config`: The `json` config file containg relevant server information.
    ## Methods
    ### Setup Optional
      `@classmethod help_info`: Returns a `HelpInfo` object detailing the settings of the command.
      See `HelpInfo` docstring for customizable attributes.
    ### Setup Required
      `action`: The callback coroutine for when the command is invoked. Must be overridden.
    '''
    _is_registered = False

    def __init__(self, *, bot: Bot, config: dict) -> None:
        hlp = self.help_info()
        self.name: str = getattr(self, 'name', hlp.name)
        self.desc: str = getattr(self, 'desc', hlp.desc)
        self.bot: Bot = bot
        self.config: dict = config

    @abstractmethod
    async def action(self, interaction: discord.Interaction) -> None:
        '''
        Must be implemented in subclass.
        '''
        pass

    @classmethod
    def help_info(cls) -> HelpInfo:
        '''
        Return a default HelpInfo object with the following attribute:
          1. `name`: The name of the class
          2. `desc`: The docstring of the class
          3. `group`: None
          4. `mod_only`: False
        '''
        return HelpInfo(name=cls.__name__, desc=cls.__doc__)

class BaseGroup(metaclass=ABCMeta):
    '''
    The base class that all groups are expected to inherit from.\n
    A group is a collection of related commands. Here's an example for
    a group called `timer` with `start` and `end` commands.
    ```
    /timer start
    /timer end
    ```
    Subgroups are not supported. I'll redesign this class if I ever need them.

    ## Attributes
    ### No Setup Required
      `name`: The name of the group. Defaults to the name of the subclass.\n
      `desc`: The description of the group. Defaults to the docstring of the subclass.
    ### Setup Required
      `commands`: The commands belonging to this group.
    '''
    def __init__(self) -> None:
        self.name: str = getattr(self, 'name', self.__class__.__name__)
        self.desc: str = getattr(self, 'desc', self.__class__.__doc__)

    @property
    @abstractmethod
    def commands(self) -> list[type[BaseCommand]]:
        '''
        Must be implemented in subclass
        '''
        pass
    
class ping(BaseCommand):
    '''
    Returns the latency of the bot in miliseconds.
    '''
    async def action(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'{round(self.bot.latency, 2) * 1000} ms', ephemeral=True)

    @classmethod
    def help_info(cls) -> HelpInfo:
        return HelpInfo(name='ping', desc='Returns the latency of the bot in miliseconds.\n')
    
class message_send(BaseCommand):
    '''
    Note the closely related `message_edit` in context_menu.py.\n 
    It was easier to design the `edit` portion as a context menu 
    command due to its place in Discord, and due to Discord limitations. 
    '''
    @describe(
        content="The content of the message. Required if title and desc aren't given.",
        title="Title of the embed. Required if content isn't given.",
        description="Description of the embed. Required if content isn't given.",
        color="The hexcode to use for the embed's color.",
        url="The URL the embed should link to.",
        image="URL to an image that the embed should use.",
        mimic="The person to mimic. Defaults to the bot."
    )
    async def action(self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel,
        content: str = None, 
        title: str = None, 
        description: str = None,
        color: str = '072c59',
        url: str = None,
        image: str = None,
        mimic: discord.Member = None
    ) -> None:
        
        if not await self.input_sanity_checks(interaction=interaction, content=content, title=title, description=description, color=color, params=locals()):
            return
        
        embed = generate_embed({
            'title': title,
            'description': description,
            'image': image,
            'color': int(color, base=16),
            'url': url
        }) if title and description else None

        if mimic: # use a webhook to send
            webhook = await self.get_webhook(channel)
            await webhook.send(
                username=mimic.display_name,
                avatar_url=mimic.display_avatar,
                content=content,
                embed=embed
            )
        else:
            await channel.send(content=content, embed=embed)

        await interaction.response.send_message('Success!', ephemeral=True)
    
    async def get_webhook(self, channel: discord.TextChannel) -> discord.Webhook:
        for webhook in await channel.webhooks():
            if webhook.name == 'DS-CustomMessages':
                return webhook
        return await channel.create_webhook(name='DS-CustomMessages', reason="For the DS-UCSB bot. Don't touch!")
    
    async def input_sanity_checks(self, 
        *,
        interaction: discord.Interaction,
        content: str, 
        title: str, 
        description: str,
        color: str,
        params: dict,
    ) -> discord.Embed | None:
        '''
        Perform sanity checks on given input.
        '''
        # user failed to provide content OR title and desc
        if not content and (not title or not description):
            await interaction.response.send_message(embed=make_fail_embed(
                title='ERROR', 
                msg='You must provide either `content` or `title` AND `desc`.',
                args=params
            ), ephemeral=True)
            return False
        
        # test validity of the color
        try:
            int(color, base=16)
        except ValueError:
            await interaction.response.send_message(embed=make_fail_embed(
                title='ERROR', 
                msg=f'{color} is an invalid color.',
                args=params
            ), ephemeral=True)
            return False
        
        # if one is given but other is missing
        if bool(title) != bool(description):
            await interaction.response.send_message(embed=make_fail_embed(
                title='ERROR', 
                msg='Failed to send embed since either `title` or `description` was missing.',
                args=params
            ), ephemeral=True)
            return False
        
        return True
    
    @classmethod
    def help_info(cls) -> HelpInfo:
        return HelpInfo(name='send', desc='Send a message through the bot.\n', mod_only=True)

class checkboard(BaseCommand):

    #checks if user is a board member

    def __init__(self, *, bot: Bot, config: dict) -> None:
        super().__init__(bot=bot, config=config)
        
    async def action(self, interaction: Interaction) -> None:
        
        if interaction.user.get_role(1132838403352830013) == None:
            await interaction.response.send_message("You are not a Board member.", ephemeral = True)
        else:
            await interaction.response.send_message("You are a Board member!", ephemeral = True)

    @classmethod
    def help_info(cls) -> HelpInfo:
        return HelpInfo(name='check', desc= 'Checks if user is on the Data Science UCSB Board.\n')

class helptest(BaseCommand):
    '''
    Returns list of slash commands.
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        super().__init__(bot=bot, config=config)
        
    async def action(self, interaction: Interaction) -> None:
        cmds = BaseCommand.__subclasses__()
        cmds.sort(key=lambda x: x.help_info().name)

        allCommandsTxt = "",
        for cmd in cmds:
            getCmd = cmd.help_info()
            # checks if the command is mod_only and skip it (unless interaction.user is a mod!)
            if getCmd.mod_only == False:
                allCommandsTxt += getCmd.display()
            elif not (interaction.user.get_role(1132838403352830013) == None):
                allCommandsTxt += getCmd.display()
        
        cmdstr = ''.join(map(str,allCommandsTxt))
        # joins tuple to form one string

        await interaction.response.send_message(cmdstr, ephemeral = True)

    @classmethod
    def help_info(cls) -> HelpInfo:
        return HelpInfo(name='help', desc= 'Returns list of slash commands.\n')
