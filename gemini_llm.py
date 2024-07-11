import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from auto_posting import TistoryPoster
import asyncio

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

poster = TistoryPoster()
    
title = "테스트 제목"
content = "# 테스트 내용\n\n이것은 테스트 포스트입니다."
tags = "테스트, 예시"

blog_url = poster.post_to_tistory(title, content, tags)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(blog_url)
        print("Message sent. Shutting down the bot.")
        await bot.close()
    else:
        print(f"Channel with ID {CHANNEL_ID} not found.")
        await bot.close()

async def main():
    try:
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        await bot.close()
    finally:
        print("Bot has been shut down.")

asyncio.run(main())