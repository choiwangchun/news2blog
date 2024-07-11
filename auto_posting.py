import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import os

load_dotenv()

class TistoryPoster:
    def __init__(self):
        self.EMAIL = os.getenv('KAKAO_EMAIL')
        self.PASSWORD = os.getenv('KAKAO_PASSWORD')
        self.driver = None

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(options=options)

    def login(self):
        self.driver.get('https://www.tistory.com/')
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="kakaoHead"]/div/div[3]/div/a'))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/a[2]/span[2]'))).click()
        time.sleep(1)

        username = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="loginId--1"]')))
        username.send_keys(self.EMAIL)
        
        password = self.driver.find_element(By.XPATH, '//*[@id="password--2"]')
        password.send_keys(self.PASSWORD)
        time.sleep(1)
        self.driver.find_element(By.XPATH, '//*[@id="mainContent"]/div/div/form/div[4]/button[1]').click()

    def navigate_to_write_page(self):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="kakaoHead"]/div/div[3]/div/a[2]/img'))).click()
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="kakaoHead"]/div/div[3]/div/div/div/div[2]/div/div[3]/a[2]'))).click()
        time.sleep(0.5)

        try:
            WebDriverWait(self.driver, 2).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert.dismiss()
        except TimeoutException:
            pass

    def select_category(self):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="category-btn"]'))).click()
        time.sleep(0.5)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="category-item-1212602"]/span'))).click()
        time.sleep(0.5)

    def select_markdown(self):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="editor-mode-layer-btn-open"]'))).click()
        time.sleep(0.5)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="editor-mode-markdown-text"]'))).click()
        try:
            WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert.accept()
        except TimeoutException:
            pass

    def write_post(self, title, content, tags):
        title_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="post-title-inp"]')))
        title_input.send_keys(title)
        time.sleep(1)

        content_editor = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="markdown-editor-container"]/div[2]/div/div/div[6]/div[1]/div/div/div/div[5]/pre'))
        )

        actions = ActionChains(self.driver)
        actions.move_to_element(content_editor).click().send_keys(content).perform()

        tag_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tagText"]')))
        tag_input.click()
        tag_input.send_keys(tags)
        tag_input.send_keys(Keys.ENTER)

    def publish_post(self):
        try:
            # 발행 버튼 클릭
            publish_layer_btn = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="publish-layer-btn"]'))
            )
            publish_layer_btn.click()
            time.sleep(1)

            # 발행 확인 버튼 클릭
            publish_btn = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="publish-btn"]'))
            )
            publish_btn.click()
            print("1")
            # JavaScript를 사용하여 페이지 로딩 완료 확인
            WebDriverWait(self.driver, 60).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            print("포스트가 발행되었습니다. URL을 찾는 중...")
            # URL 가져오기
            for _ in range(10):  # 최대 10번 시도
                try:
                    # 현재 페이지의 HTML 가져오기
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')

                    # div.post_cont strong.tit_post a.link_cont 요소 찾기
                    post_link = soup.select_one('div.post_cont strong.tit_post a.link_cont')

                    if post_link and 'href' in post_link.attrs:
                        blog_url = post_link['href']
                        print(f"발행된 블로그 포스트 URL: {blog_url}")
                        return blog_url
                    else:
                        print(f"시도 {_ + 1}: URL을 찾지 못했습니다. 3초 후 다시 시도합니다.")
                        time.sleep(3)

                except Exception as e:
                    print(f"URL 가져오기 시도 {_ + 1} 실패: {e}")
                    time.sleep(3)

            print("URL 가져오기 실패")
            return None

        except (TimeoutException, WebDriverException) as e:
            print(f"WebDriver 오류 발생: {e}")
            return None
        except Exception as e:
            print(f"포스트 발행 중 오류 발생: {e}")
            return None
        

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def post_to_tistory(self, title, content, tags):
        try:
            self.setup_driver()
            self.login()
            self.navigate_to_write_page()
            self.select_category()
            self.select_markdown()
            self.write_post(title, content, tags)
            blog_url = self.publish_post()
            
            if blog_url:
                print("포스팅이 성공적으로 완료되었습니다.")
            else:
                print("포스팅은 완료되었지만 URL을 가져오는데 실패했습니다.")
            
            return blog_url
        except Exception as e:
            print(f"포스팅 과정에서 오류 발생: {e}")
            return None
        finally:
            # 드라이버를 여기서 종료하지 않습니다.
            pass

    