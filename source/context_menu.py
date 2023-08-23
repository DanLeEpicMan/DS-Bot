import discord

class message_edit(BaseCommand):
    def __init__(self, *, bot: Bot, config: dict) -> None:
        super().__init__(bot=bot, config=config)
        self.name = 'edit'
        self.desc = "Edits an existing message sent by the bot. Doesn't change values that aren't given."

    @describe(
        channel="The channel the message is in. This must be given due to Discord limitation.",
        message_id="The ID of the message.",
        content="The content of the message.",
        title="Title of the embed.",
        description="Description of the embed.",
        color="The hexcode to use for the embed's color.",
        url="The URL the embed should link to.",
        image="URL to an image that the embed should use.",
    )
    async def action(self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel,
        message_id: int, 
        content: str = None, 
        title: str = None, 
        description: str = None, 
        color: str = None, 
        url: str = None, 
        image: str = None, 
    ) -> None:
        # the sanity checks are so simple, so i didn't bundle them into one method
        params = locals()
        message = await self.sanity_checks(channel=channel, message_id=message_id, title=title, description=description, color=color, params=params)
        if isinstance(message, discord.Embed):
            return await interaction.response.send_message(embed=message, ephemeral=True)
        
        if message.embeds:
            embed = message.embeds[0]
            embed.title = title or embed.title
            embed.description = description or embed.description
            embed.color = int(color, base=16) if color else embed.color
            embed.url = url or embed.url
            if image:
                embed.set_image(url=image)

        else:
            embed = generate_embed({
                'title': title,
                'description': description,
                'image': image,
                'color': color,
                'url': url
            })

        await message.edit(
            content=content,
            embed=embed
        )
        await interaction.response.send_message('Success!', ephemeral=True)
    
    async def sanity_checks(self, channel: discord.TextChannel, message_id: discord.Message, title: str, description: str, color: int, params: dict) -> discord.Embed | discord.Message:
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return make_fail_embed(
                title='ERROR',
                msg="Message wasn't found in provided channel.",
                color=0xdb1a1a,
                args=params
            )
        
        if not message.author.bot:
            return make_fail_embed(
                title='ERROR',
                msg='Provide a valid message.',
                color=0xdb1a1a,
                args=params
            )
        
        try:
            color = int(color, base=16)
        except ValueError:
            return make_fail_embed(
                title='ERROR', 
                msg=f'{color} is an invalid color.',
                color=0xdb1a1a,
                args=params
            )
        
        if not message.embeds and bool(title) != bool(description): # if no embed exists but the user tries to add one improperly
            return make_fail_embed(
                title='Warning', 
                msg='Failed add an embed due to missing `title` or `description`.',
                color=0xeed202,
                args=params
            )

        return message