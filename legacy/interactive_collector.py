#!/usr/bin/env python3
"""
대화형 수집기 - Claude가 각 단계마다 페이지를 보고 판단
"""
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from pathlib import Path

# Chrome 설정
download_dir = Path('./data/raw').absolute()
download_dir.mkdir(parents=True, exist_ok=True)

chrome_options = webdriver.ChromeOptions()
prefs = {"download.default_directory": str(download_dir)}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()

# 명령행 인자로 받은 작업 수행
command = sys.argv[1] if len(sys.argv) > 1 else "start"

if command == "start":
    driver.get("https://www.data.go.kr/")
    print("READY")

elif command == "search":
    keyword = sys.argv[2]
    driver.get(f"https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword={keyword}")
    time.sleep(2)
    print(driver.page_source)

elif command == "click_first":
    # 첫 번째 검색 결과 클릭
    results = driver.find_elements(By.CSS_SELECTOR, ".result-list .result-item a, .result_list li a")
    if results:
        url = results[0].get_attribute("href")
        driver.get(url)
        time.sleep(2)
        print(driver.page_source)

elif command == "get_html":
    print(driver.page_source)

elif command == "click":
    xpath = sys.argv[2]
    element = driver.find_element(By.XPATH, xpath)
    element.click()
    time.sleep(3)
    print("CLICKED")

elif command == "quit":
    driver.quit()
    print("QUIT")
