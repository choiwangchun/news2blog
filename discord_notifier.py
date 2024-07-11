import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

class TistoryDiscordBot:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        self.channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))
        
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        @self.bot.event
        async def on_ready():
            print(f'{self.bot.user} has connected to Discord!')
    
    async def send_notification(self, blog_url):
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            await channel.send(f"새 글이 포스팅되었습니다: {blog_url}")
        else:
            print(f"Channel with ID {self.channel_id} not found.")
    
    async def start(self):
        await self.bot.start(self.token)
    
    async def close(self):
        await self.bot.close()