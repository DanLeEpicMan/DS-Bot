import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import json


config = json.load(open('config.json'))

bot = commands.Bot(command_prefix='$', intents=discord.Intents.all())
tree = bot.tree
guild = discord.Object(config['server_id'])

@tree.command(name='hey', description='Responds with Ho!', guild=guild)
async def func(interaction: discord.Interaction):
    await interaction.response.send_message('Ho!', ephemeral=True)


@bot.event
async def on_ready():
    await tree.sync(guild=guild)
    print('Ready!')



bot.run(config['oauth_token'])
