import schedule
import time
import csv
import re
import pandas as pd
import discord
from discord.ext import commands
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from langchain import LLMChain, PromptTemplate
from langchain.llms import OpenAI
from dotenv import load_dotenv
import os
from ai_workflow import create_workflow, run_workflow
load_dotenv()


class NewsBot:
    def __init__(self):
        self.driver = None 
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.ai_workflow = create_workflow(self.api_key)
        self.csv_directory = r"C:\Users\slek9\PycharmProjects\news2blog\parsing_news"
        self.agent_result_directory = r"C:\Users\slek9\PycharmProjects\news2blog\Agent_result"
        self.news_directory = self.csv_directory

        # Discord 봇 설정
        self.discord_token = os.getenv('DISCORD_BOT_TOKEN')
        self.discord_channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))
        intents = discord.Intents.default()
        intents.message_content = True
        self.discord_bot = commands.Bot(command_prefix='!', intents=intents)

        # Agent_result 디렉토리가 없으면 생성
        if not os.path.exists(self.agent_result_directory):
            os.makedirs(self.agent_result_directory)

        
    async def send_discord_notification(self, message):
        await self.discord_bot.wait_until_ready()
        channel = self.discord_bot.get_channel(self.discord_channel_id)
        if channel:
            await channel.send(message)
        else:
            print(f"Error: Could not find Discord channel with ID {self.discord_channel_id}")   

    def setup_selenium(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
        self.driver = webdriver.Chrome(options=options)
        

    def crawl_investing_com(self, time_period):
        url = "https://www.investing.com/news/latest-news"
        self.driver.get(url)
        
        raw_data = []
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-test='article-title-link']"))
            )
            articles = self.driver.find_elements(By.CSS_SELECTOR, "a[data-test='article-title-link']")
            print(f"Found {len(articles)} articles")
            
            for article in articles[:20]:  # 최근 20개 기사만 수집
                title = article.text
                link = article.get_attribute("href")
                raw_data.append({"title": title, "link": link})
        
        except Exception as e:
            print(f"Error during crawling: {e}")
        
        print(f"Crawled {len(raw_data)} articles")
        return raw_data
    

    def clean_content(self, content):
        # HTML 파싱
        soup = BeautifulSoup(content, 'html.parser')
        
        # 광고 및 구독 유도 콘텐츠 제거
        for div in soup.find_all('div', {'data-test': 'contextual-subscription-hook'}):
            div.decompose()
        
        # 나머지 텍스트 추출
        cleaned_text = soup.get_text(separator='\n', strip=True)
        
        # 불필요한 줄바꿈 제거 및 여러 줄바꿈을 하나로 통일
        cleaned_text = re.sub(r'\n+', '\n', cleaned_text)

        # 광고 텍스트 제거
        ad_text = "3rd party Ad. Not an offer or recommendation by Investing.com. See disclosure here or remove ads."
        cleaned_text = cleaned_text.replace(ad_text, "")
        
        # 연속된 빈 줄 제거
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        
        return cleaned_text.strip()


    def read_latest_csv(self):
        csv_files = [f for f in os.listdir(self.csv_directory) if f.endswith('.csv')]
        if not csv_files:
            raise FileNotFoundError("No CSV files found in the directory.")
        
        latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(self.csv_directory, x)))
        file_path = os.path.join(self.csv_directory, latest_file)
        
        df = pd.read_csv(file_path)
        return df


    def parse_news_data(self, raw_data):
        parsed_data = []
        for article in raw_data:
            self.driver.get(article['link'])
            time.sleep(3)
            try:
                title = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "articleTitle"))
                ).text
                
                content_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@id='article']/div"))
                )
                
                # BeautifulSoup을 사용하여 HTML 파싱
                soup = BeautifulSoup(content_element.get_attribute('innerHTML'), 'html.parser')
                
                # 마지막 <p> 태그까지의 내용만 추출
                content = ''
                for element in soup.find_all(['p', 'h2']):  # 제목(h2)과 단락(p)만 추출
                    content += element.get_text() + '\n'
                    if element.name == 'p' and not element.find_next_sibling('p'):
                        break  # 마지막 <p> 태그에 도달하면 루프 종료
                
                # 콘텐츠 정리
                cleaned_content = self.clean_content(content)
                
                parsed_data.append({"title": title, "content": cleaned_content})
            except Exception as e:
                print(f"Failed to parse article: {article['title']}. Error: {e}")
        return parsed_data


    def save_to_csv(self, data, directory=None, filename=None):
        if directory is None:
            directory = r"C:\Users\slek9\PycharmProjects\news2blog\parsing_news"
        
        if filename is None:
            filename = f"news_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # 디렉토리가 존재하지 않으면 생성
        os.makedirs(directory, exist_ok=True)
        
        full_path = os.path.join(directory, filename)
        
        with open(full_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["title", "content"])
            writer.writeheader()
            for article in data:
                writer.writerow(article)
        
        print(f"Data saved to {full_path}")


    async def run_cycle(self, time_period):
        try:
            df = self.read_latest_csv()
            input_data = "\n\n".join([f"제목: {row['title']}\n내용: {row['content']}" for _, row in df.iterrows()])
            
            result = run_workflow(self.ai_workflow, input_data)
            
            self.save_agent_results(result)
            
            print(f"Workflow result: {result}")  # 디버깅을 위한 출력 추가
            
            if 'blog_writer' in result and 'seo_evaluator' in result:
                blog_post = result['blog_writer']['output']
                seo_result = result['seo_evaluator']['output']
                
                print(f"SEO result: {seo_result}")  # 디버깅을 위한 출력 추가
                
                try:
                    seo_score = int(seo_result.split()[0])
                except (ValueError, IndexError):
                    print(f"Failed to parse SEO score from: {seo_result}")
                    seo_score = 0
                
                self.post_to_blog(blog_post)
                self.save_result(blog_post, seo_score)
                await self.send_discord_notification(f"새 블로그 포스트가 작성되었습니다. SEO 점수: {seo_score}")
            else:
                print("블로그 작성 또는 SEO 평가 결과가 없습니다.")
                print(f"Available keys in result: {result.keys()}")
        
        except Exception as e:
            print(f"Error in run_cycle: {e}")
            import traceback
            traceback.print_exc()  # 상세한 에러 정보 출력
            await self.send_discord_notification(f"Error occurred: {e}")


    def save_agent_results(self, result):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for agent, data in result.items():
            if agent != 'input':  # 입력 데이터는 제외
                file_name = f"{agent}_result_{timestamp}.csv"
                file_path = os.path.join(self.agent_result_directory, file_name)
                
                # 데이터를 DataFrame으로 변환
                if isinstance(data['output'], dict):
                    df = pd.DataFrame([data['output']])
                else:
                    df = pd.DataFrame({'output': [data['output']]})
                
                df.to_csv(file_path, index=False)
                print(f"Saved {agent} result to {file_path}")


    def post_to_blog(self, blog_post):
        # 실제 블로그 포스팅 로직 구현
        print("블로그에 포스팅:", blog_post[:100] + "...")
    

async def main():
    import logging
    logging.basicConfig(level=logging.INFO)

    bot = NewsBot()
    
    @bot.discord_bot.event
    async def on_ready():
        print(f'{bot.discord_bot.user} has connected to Discord!')
    
    async def run_schedule():
        while True:
            now = datetime.now()
            if now.hour == 9 and now.minute == 0:
                await bot.run_cycle("night_to_morning")
            elif now.hour == 13 and now.minute == 0:
                await bot.run_cycle("morning_to_noon")
            elif now.hour == 23 and now.minute == 8:
                await bot.run_cycle("noon_to_evening")
            await asyncio.sleep(60)  # 1분마다 체크
    
    # 두 개의 태스크를 동시에 실행
    await asyncio.gather(
        bot.discord_bot.start(bot.discord_token),
        run_schedule()
    )

if __name__ == "__main__":
    asyncio.run(main())