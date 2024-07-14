# test.py

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("https://wroldnews-ainews.tistory.com/entry/AI-%EA%B8%88%EB%A6%AC-%EC%9D%B8%ED%95%98-%EC%97%94%ED%99%94-%EC%95%BD%EC%84%B8-2024%EB%85%84-%EA%B8%80%EB%A1%9C%EB%B2%8C-%ED%88%AC%EC%9E%90-%EC%A0%84%EB%9E%B5-%EB%B6%84%EC%84%9D")
    else:
        print(f"Channel with ID {CHANNEL_ID} not found.")

bot.run(TOKEN)
