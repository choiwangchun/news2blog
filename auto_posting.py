import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import os
from datetime import datetime

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 이메일과 비밀번호 가져오기
EMAIL = os.getenv('KAKAO_EMAIL')
PASSWORD = os.getenv('KAKAO_PASSWORD')

# 현재 날짜와 시간으로 폴더 이름 생성
# folder_name = datetime.now().strftime("%Y%m%d_%H%M%S")
# folder_path = os.path.join(r"C:\Users\slek9\PycharmProjects\news2blog\Agent_result", folder_name)
folder_path = os.path.join(r"C:\Users\slek9\PycharmProjects\news2blog\Agent_result\20240710_211745")
def get_title_content_and_tags():
    with open(os.path.join(folder_path, 'blog_title.txt'), 'r', encoding='utf-8') as f:
        title = f.read().strip().replace('#', '')
    
    with open(os.path.join(folder_path, 'blog_content.txt'), 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(os.path.join(folder_path, 'related_links.txt'), 'r', encoding='utf-8') as f:
        links = f.readlines()
    
    related_links = "**관련출처:**\n" + ''.join([f"- {link.strip()}\n" for link in links])
    
    with open(os.path.join(folder_path, 'tags.txt'), 'r', encoding='utf-8') as f:
        tags = f.read()
    
    # 태그에서 불필요한 문자 제거
    tags = tags.replace('**태그:**', '').replace('#', '').replace(' ', '').strip()
    
    return title, content + "\n\n" + related_links, tags

# Selenium 설정
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

try:
    # 티스토리 접속
    driver.get('https://www.tistory.com/')

    # 계정 로그인 버튼 클릭
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="kakaoHead"]/div/div[3]/div/a'))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/a[2]/span[2]'))).click()
    time.sleep(1)

    # 로그인
    username = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="loginId--1"]')))
    username.send_keys(EMAIL)
    
    password = driver.find_element(By.XPATH, '//*[@id="password--2"]')
    password.send_keys(PASSWORD)
    time.sleep(1)
    driver.find_element(By.XPATH, '//*[@id="mainContent"]/div/div/form/div[4]/button[1]').click()

    # 글 작성 페이지 이동
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="kakaoHead"]/div/div[3]/div/a[2]/img'))).click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="kakaoHead"]/div/div[3]/div/div/div/div[2]/div/div[3]/a[2]'))).click()
    time.sleep(0.5)

    # 팝업창 처리
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print(f"Alert 메시지: {alert.text}")
        alert.dismiss()  # '취소' 버튼 클릭
        print("팝업창 취소 버튼을 클릭했습니다.")
    except TimeoutException:
        print("팝업창이 나타나지 않았습니다.")

    # 카테고리 선택
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="category-btn"]'))).click()
    time.sleep(0.5)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="category-item-1212602"]/span'))).click()
    time.sleep(0.5)

    # 마크다운 선택
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="editor-mode-layer-btn-open"]'))).click()
    time.sleep(0.5)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="editor-mode-markdown-text"]'))).click()
    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print(f"Alert 메시지: {alert.text}")
        alert.accept()
        print("팝업창 확인 버튼을 클릭했습니다.")
    except TimeoutException:
        print("팝업창이 나타나지 않았습니다.")
    
    # 제목, 내용, 태그 가져오기
    title, content, tags = get_title_content_and_tags()

    # 제목 입력
    title_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="post-title-inp"]')))
    title_input.send_keys(title)
    time.sleep(1)

    # 내용 입력
    content_editor = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="markdown-editor-container"]/div[2]/div/div/div[6]/div[1]/div/div/div/div[5]/pre'))
    )

    actions = ActionChains(driver)
    actions.move_to_element(content_editor).click().send_keys(content).perform()

    print("내용이 성공적으로 입력되었습니다.")

    # 태그 입력
    tag_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tagText"]')))
    tag_input.click()
    tag_input.send_keys(tags)
    tag_input.send_keys(Keys.ENTER)

    print("태그가 성공적으로 입력되었습니다.")

    # 완료 버튼 클릭
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="publish-layer-btn"]'))).click()
    time.sleep(0.5)

    # 발행 버튼 클릭
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="publish-btn"]'))).click()
    time.sleep(0.5)

    print("포스팅이 성공적으로 완료되었습니다.")

except Exception as e:
    print(f"오류 발생: {e}")

finally:
    # 브라우저 종료
    driver.quit()