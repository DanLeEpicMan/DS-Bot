from abc import ABCMeta, abstractmethod
import discord
from discord.ext.commands import Bot
from discord import ui
from discord.interactions import Interaction
from source.tools.ui_helper import generate_embed, make_fail_embed


class BaseContextMenu(metaclass=ABCMeta):
    '''
    The base class that all context menus are expected to inherit from.\n
    Context menus are buttons that appear in the interaction menu
    when right clicking a message or user.

    If you wish to add parameter descriptions (or change how they're named in Discord), please use the `describe`
    or `rename` decorators, respectively.
    ## Attributes
    ### No Setup Required
      `name`: The name of the menu. Defaults to the name of the subclass.\n
      `bot`: The `commands.Bot` instance of the bot.\n
      `config`: The `json` config file containg relevant server information.
    ### Setup Required
      `action`: The callback coroutine for when the command is invoked. Must be overridden.
      It's important for the `message_or_member` parameter to be properly typed.
    '''
    def __init__(self, *, bot: Bot, config: dict) -> None:
        self.bot = bot
        self.config = config
        self.name = getattr(self, 'name', self.__class__.__name__)

    @abstractmethod
    async def action(self, interaction: discord.Interaction, message_or_member: discord.Message | discord.Member):
        '''
        Must be implemented in subclass.
        '''
        pass

class message_edit(BaseContextMenu):
    name = 'edit'

    async def action(self, interaction: discord.Interaction, message: discord.Message,) -> None:
        # the following two sanity checks simply discern if the interaction can proceed
        # input_sanity_checks is meant to check the message and embed input
        if not message.author.id == self.bot.user.id and message.webhook_id is None: 
            return await interaction.response.send_message('Please provide a message sent by the bot.', ephemeral=True)
        
        hook = None
        if message.webhook_id:
            for webhook in await message.channel.webhooks():
                if webhook.name == 'DS-CustomMessages':
                    hook = webhook
                    break
            else:
                return await interaction.response.send_message("Can't edit this message.", ephemeral=True)
        
        class EditModal(ui.Modal, title='Edit Message'):
            '''
            The modal is included explicitly instead of using a helper method due to
            `on_submit` needing to be defined here anyways.

            Until I can think of a good implementation of a helper method,
            this will be created here.
            '''
            content = ui.TextInput(label='Message Content', placeholder="Content of the message.", style=discord.TextStyle.long, required=False)
            embed_title = ui.TextInput(label='Embed Title', placeholder="Title of the embed.", required=False) # 'title' is already taken :(
            description = ui.TextInput(label='Embed Description', placeholder="Description of the embed.", style=discord.TextStyle.long, required=False)
            color = ui.TextInput(label='Embed Color', placeholder="The hexcode to use for the embed's color.", required=False)
            urls = ui.TextInput(label='Embed URLs', placeholder="embed_url\nimage_url\nUse `none` to skip embed_url", style=discord.TextStyle.long, required=False)

            async def on_submit(modal_self, interaction: Interaction) -> None: # can't use self :(
                content, title, description, color, urls = modal_self.content.value, modal_self.embed_title.value, modal_self.description.value, modal_self.color.value, modal_self.urls.value
                if not await self.input_sanity_checks(interaction=interaction, message=message, content=content, title=title, description=description, color=color, urls=urls, params=locals()):
                    # it would be so nice to just pass **locals(), but i guess python doesn't want that for me
                    return
                
                url, image = None, None
                urls = urls.split()
                for i in range(len(urls)):
                    # first item is always url, second is always image
                    item = urls[i]
                    if i==0:
                        url = None if item.lower() == 'none' else item
                    elif i==1:
                        image = None if item.lower() == 'none' else item

                embed = None
                if message.embeds:
                    embed = message.embeds[0].copy()
                    embed.title = title or embed.title
                    embed.description = description or embed.description
                    embed.color = int(color, base=16) if color else embed.color
                    embed.url = url or embed.url
                    if image:
                        embed.set_image(url=image)
                elif title and description:
                    embed = generate_embed({
                        'title': title,
                        'description': description,
                        'image': image,
                        'color': int(color, base=16) if color else None,
                        'url': url
                    })

                if hook is not None:
                    # you can't edit the webhook message directly without being thrown a forbidden error
                    await hook.edit_message(
                        message.id, 
                        content=content or message.content,
                        embed=embed
                    )
                else:
                    await message.edit(
                        content=content or message.content,
                        embed=embed
                    )
                await interaction.response.send_message('Success!', ephemeral=True)


        await interaction.response.send_modal(EditModal())
    
    async def input_sanity_checks(self, *, interaction: discord.Interaction, message: discord.Message, params: dict, content: str, title: str, description: str, color: str, urls: str) -> bool: 
        # check if the user inputted something
        if not (content or title or description or color or urls):
            await interaction.response.send_message(embed=make_fail_embed(
                title='ERROR', 
                msg='Please input something.',
                args=params
            ), ephemeral=True)
            return False
        
        # test the validity of the color
        if color:
            try:
                int(color, base=16)
            except ValueError:
                await interaction.response.send_message(embed=make_fail_embed(
                    title='ERROR', 
                    msg=f'{color} is an invalid color.',
                    args=params
                ), ephemeral=True)
                return False
        
        # if no embed exists but the user tries to add one improperly
        if not message.embeds and bool(title) != bool(description): 
            await interaction.response.send_message(embed=make_fail_embed(
                title='ERROR', 
                msg='Failed add an embed due to missing `title` or `description`.',
                args=params
            ), ephemeral=True)
            return False
        
        # if no embed exists and the user tries to add color/urls without title AND desc
        if not (message.embeds or title or description) and (color or urls):
            await interaction.response.send_message(embed=make_fail_embed(
                title='ERROR', 
                msg="Can't change color or set URLs without title and description.",
                args=params
            ), ephemeral=True)
            return False

        return True
