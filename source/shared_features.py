'''
The purpose of this module is to be a container for commands that pull from the same code.
'''
import discord
from discord import ui
from discord.utils import MISSING
from source.tools.ui_helper import generate_embed


class SupportModal(ui.Modal, title='Help Form'):
    '''
    Support Modal used by the help button and help command.
    '''
    brief = ui.TextInput(label='Title', placeholder='Briefly title your problem.', max_length=50)
    explain = ui.TextInput(label='Explanation', placeholder='Explain your problem in full. Please give as many details as possible.', style=discord.TextStyle.long)
    contact = ui.TextInput(label='Contact', placeholder='How should we reach out to you?', required=False)

    def __init__(self, *, title: str = MISSING, timeout: float | None = None, custom_id: str = MISSING, channel: discord.TextChannel) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        brief, explain, contact = self.brief.value, self.explain.value, self.contact.value

        await self.channel.send(embed=generate_embed({
                'author': {
                    'name': interaction.user.display_name,
                    'icon_url': interaction.user.display_avatar
                },
                'color': 0x0ec940,
                'title': brief,
                'description': explain,
                'fields': [{
                    'name': 'Contact Info',
                    'value': contact
                }] if contact else None
            }))

        await interaction.response.send_message('Successfully opened a support ticket. Expect a response from a board member soon.', ephemeral=True)