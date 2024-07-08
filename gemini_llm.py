from dotenv import load_dotenv, find_dotenv
import os

# .env 파일의 경로를 찾고 로드
dotenv_path = find_dotenv()
if not dotenv_path:
    print("No .env file found.")
else:
    load_dotenv(dotenv_path)

print("Environment variables:")
print(f"DISCORD_BOT_TOKEN: {os.getenv('DISCORD_BOT_TOKEN')}")
print(f"DISCORD_CHANNEL_ID: {os.getenv('DISCORD_CHANNEL_ID')}")
print(f"GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY')}")