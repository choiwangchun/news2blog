import schedule
import time
import csv
import re
import os
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from ai_workflow_test import create_workflow_test, run_workflow_test
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

load_dotenv()

class NewsBot:
    def __init__(self):
        self.driver = None 
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.csv_directory = r"C:\Users\slek9\PycharmProjects\news2blog\parsing_news"
        self.agent_result_directory = r"C:\Users\slek9\PycharmProjects\news2blog\Agent_result"
        self.ai_workflow = create_workflow_test(self.api_key, self.csv_directory)
        self.news_directory = self.csv_directory
        self.current_result_directory = None

        if not os.path.exists(self.agent_result_directory):
            os.makedirs(self.agent_result_directory)

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
            
            for article in articles[:10]:  # 최근 10개 기사만 수집
                title = article.text
                link = article.get_attribute("href")
                raw_data.append({"title": title, "link": link})
        
        except Exception as e:
            print(f"Error during crawling: {e}")
        
        print(f"Crawled {len(raw_data)} articles")
        return raw_data

    def clean_content(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        
        for div in soup.find_all('div', {'data-test': 'contextual-subscription-hook'}):
            div.decompose()
        
        cleaned_text = soup.get_text(separator='\n', strip=True)
        cleaned_text = re.sub(r'\n+', '\n', cleaned_text)

        ad_text = "3rd party Ad. Not an offer or recommendation by Investing.com. See disclosure here or remove ads."
        cleaned_text = cleaned_text.replace(ad_text, "")
        
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        
        return cleaned_text.strip()

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
                
                soup = BeautifulSoup(content_element.get_attribute('innerHTML'), 'html.parser')
                
                content = ''
                for element in soup.find_all(['p', 'h2']):
                    content += element.get_text() + '\n'
                    if element.name == 'p' and not element.find_next_sibling('p'):
                        break
                
                cleaned_content = self.clean_content(content)
                
                parsed_data.append({
                    "title": title, 
                    "content": cleaned_content, 
                    "link": article['link']
                })
            except Exception as e:
                print(f"Failed to parse article: {article['title']}. Error: {e}")
        return parsed_data

    def save_to_csv(self, data, directory=None, filename=None):
        if directory is None:
            directory = self.csv_directory
        
        if filename is None:
            filename = f"news_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        os.makedirs(directory, exist_ok=True)
        
        full_path = os.path.join(directory, filename)
        
        with open(full_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["title", "content", "link"])
            writer.writeheader()
            for article in data:
                writer.writerow(article)

        print(f"Data saved to {full_path}")


    def get_related_links(self, title, content):
        latest_csv = self.get_latest_csv(self.csv_directory)
        related_links = []
        
        with open(latest_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if (title.lower() in row['title'].lower()) or any(word in row['content'].lower() for word in content.lower().split()[:10]):
                    related_links.append(row['link'])
                    if len(related_links) == 3:
                        break
        
        return related_links


    def get_latest_csv(self, directory):
        csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
        if not csv_files:
            raise FileNotFoundError("No CSV files found in the directory.")
        
        latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(directory, x)))
        return os.path.join(directory, latest_file)

    def read_csv_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


    def create_new_result_directory(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_directory = os.path.join(self.agent_result_directory, timestamp)
        os.makedirs(new_directory, exist_ok=True)
        self.current_result_directory = new_directory
        print(f"Created new result directory: {new_directory}")


    def run_cycle(self, time_period):
        try:
            self.create_new_result_directory()
            self.setup_selenium()
            raw_data = self.crawl_investing_com(time_period)
            parsed_data = self.parse_news_data(raw_data)
            self.save_to_csv(parsed_data)
            
            latest_csv = self.get_latest_csv(self.csv_directory)
            input_data = self.read_csv_file(latest_csv)

            result = run_workflow_test(self.ai_workflow, input_data, self.current_result_directory)
            
            print(f"Workflow result: {result}")
            print(f"Result keys: {result.keys()}")

            self.save_agent_results(result)
            
            blog_post = result.get('blog_content', '')  # 'blog_content' 키가 없으면 빈 문자열 반환
            seo_score = result.get('SEO_score', 0)
            
            self.post_to_blog(blog_post)
            self.save_result(blog_post, seo_score)
            print(f"새 블로그 포스트가 작성되었습니다. SEO 점수: {seo_score}")
        
        except Exception as e:
            print(f"Error in run_cycle: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()

    def save_agent_results(self, result):
        for agent, data in result.items():
            if agent != 'input':
                file_name = f"{agent}_result.csv"
                file_path = os.path.join(self.current_result_directory, file_name)
                
                if isinstance(data, dict):
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=data.keys())
                        writer.writeheader()
                        writer.writerow(data)
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(str(data))
                
                print(f"Saved {agent} result to {file_path}")

    def post_to_blog(self, blog_post):
        print("블로그에 포스팅:")
        print(blog_post[:500] + "..." if len(blog_post) > 500 else blog_post)

    def save_result(self, blog_post, seo_score):
        file_name = "blog_post.txt"
        file_path = os.path.join(self.current_result_directory, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"SEO Score: {seo_score}\n\n")
            f.write(blog_post)
        
        print(f"Saved blog post to {file_path}")

def main():
    bot = NewsBot()
    
    def run_schedule():
        while True:
            now = datetime.now()
            if now.hour == 14 and now.minute == 4:
                bot.run_cycle("night_to_morning")
            elif now.hour == 21 and now.minute == 17:
                bot.run_cycle("morning_to_noon")
            elif now.hour == 23 and now.minute == 31:
                bot.run_cycle("noon_to_evening")
            time.sleep(60)  # 1분마다 체크

    try:
        run_schedule()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()