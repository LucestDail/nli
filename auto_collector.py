#!/usr/bin/env python3
"""
공공데이터포털 완전 자동 수집기
- Chrome 띄우기 → 사용자 로그인 대기 → HTML 분석 → 자동 다운로드/처리
"""

import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

load_dotenv()

# 우선순위 데이터 목록
PRIORITY_0 = [
    "전국법정구역(읍면동)정보표준데이터",
    "국가데이터처_SGIS 행정구역 통계 및 경계",
    "주민등록인구통계",
]

PRIORITY_1 = [
    "전국약국표준데이터",
    "전국응급의료기관표준데이터",
    "전국자동심장충격기표준데이터",
    "전국어린이집표준데이터",
    "전국초중등학교위치표준데이터",
    "전국도서관표준데이터",
    "전국전통시장표준데이터",
    "소상공인시장진흥공단_상가(상권)정보",
    "전국도시공원정보표준데이터",
    "전국체육시설표준데이터",
    "전국버스정류소표준데이터",
    "전국주차장정보표준데이터",
    "전국CCTV표준데이터",
    "전국어린이보호구역표준데이터",
    "전국교통사고다발지역표준데이터",
    "전국무더위쉼터표준데이터",
    "전국전기차충전소표준데이터",
    "전국사회복지시설표준데이터",
]

class AutoCollector:
    def __init__(self):
        self.download_dir = Path('./data/raw')
        self.api_dir = Path('./data/raw/api_info')
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.api_dir.mkdir(parents=True, exist_ok=True)

        # Chrome 옵션
        chrome_options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": str(self.download_dir.absolute()),
            "download.prompt_for_download": False,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.maximize_window()

        self.results = []

    def wait_for_login(self):
        """공공데이터포털 열고 로그인 대기"""
        print("\n" + "="*70)
        print("🌐 공공데이터포털을 엽니다.")
        print("📌 30초 안에 로그인해주세요...")
        print("="*70 + "\n")

        self.driver.get("https://www.data.go.kr/")

        # 30초 대기
        time.sleep(30)

        print("\n🚀 데이터 수집을 시작합니다!\n")

    def analyze_page(self):
        """현재 페이지 분석 - 파일데이터 vs Open API"""
        try:
            page_html = self.driver.page_source

            data_type = None
            download_info = {}

            # 1. 파일데이터 확인
            if '파일데이터' in page_html or 'CSV' in page_html or '다운로드' in page_html:
                # 다운로드 버튼 찾기
                try:
                    # 여러 패턴 시도
                    download_selectors = [
                        "//a[contains(@onclick, 'fileDataDown')]",
                        "//a[contains(text(), '다운로드')]",
                        "//button[contains(text(), '다운로드')]",
                        "//a[@title='파일 다운로드']",
                    ]

                    for selector in download_selectors:
                        try:
                            btn = self.driver.find_element(By.XPATH, selector)
                            data_type = 'FILE'
                            download_info['button_found'] = True
                            break
                        except:
                            continue

                    if not data_type:
                        data_type = 'FILE_NO_BUTTON'

                except Exception as e:
                    data_type = 'FILE_ERROR'

            # 2. Open API 확인
            if 'OPEN API' in page_html or 'OpenAPI' in page_html or '활용신청' in page_html:
                if data_type == 'FILE':
                    data_type = 'BOTH'
                else:
                    data_type = 'API'

                # API 정보 추출
                try:
                    api_elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), '활용신청')]")
                    if api_elements:
                        download_info['api_button_found'] = True
                except:
                    pass

            return data_type, download_info

        except Exception as e:
            print(f"   ⚠️  페이지 분석 실패: {e}")
            return 'UNKNOWN', {}

    def download_file(self, keyword):
        """파일 다운로드 시도"""
        try:
            download_selectors = [
                "//a[contains(@onclick, 'fileDataDown')]",
                "//a[contains(text(), '다운로드') and contains(@class, 'ico-down')]",
                "//button[contains(text(), '다운로드')]",
            ]

            for selector in download_selectors:
                try:
                    btn = self.driver.find_element(By.XPATH, selector)
                    btn.click()
                    print(f"   ⬇️  다운로드 시작...")
                    time.sleep(5)
                    return True
                except:
                    continue

            print(f"   ⚠️  다운로드 버튼을 찾을 수 없음")
            return False

        except Exception as e:
            print(f"   ❌ 다운로드 실패: {e}")
            return False

    def save_api_info(self, keyword, url):
        """API 정보 저장"""
        try:
            # 페이지에서 API 관련 정보 추출
            page_html = self.driver.page_source

            api_info = {
                'keyword': keyword,
                'url': url,
                'type': 'Open API',
                'note': '활용신청 필요 - 승인 후 API 키 발급됨',
                'collected_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # API endpoint 찾기 시도
            try:
                # 테이블에서 endpoint 정보 찾기
                tables = self.driver.find_elements(By.TAG_NAME, 'table')
                for table in tables:
                    if 'endpoint' in table.text.lower() or '요청주소' in table.text:
                        api_info['endpoint_info'] = table.text[:500]
                        break
            except:
                pass

            # 저장
            filename = self.api_dir / f"{keyword.replace(' ', '_')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(api_info, f, ensure_ascii=False, indent=2)

            print(f"   📝 API 정보 저장: {filename.name}")
            return True

        except Exception as e:
            print(f"   ⚠️  API 정보 저장 실패: {e}")
            return False

    def process_dataset(self, keyword):
        """데이터셋 처리"""
        print(f"\n{'='*70}")
        print(f"📦 처리중: {keyword}")
        print(f"{'='*70}")

        # 검색
        search_url = f"https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword={keyword}"
        self.driver.get(search_url)
        time.sleep(2)

        try:
            # 첫 번째 결과 클릭
            results = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".result-list .result-item, .result_list li"))
            )

            if not results:
                print(f"   ⚠️  검색 결과 없음")
                self.results.append({'keyword': keyword, 'status': 'not_found'})
                return False

            first_result = results[0]
            title_elem = first_result.find_element(By.CSS_SELECTOR, "a.title, .title a, a")
            title = title_elem.text.strip()
            dataset_url = title_elem.get_attribute("href")

            print(f"   ✓ 발견: {title}")

            # 상세페이지로 이동
            self.driver.get(dataset_url)
            time.sleep(2)

            # 페이지 분석
            data_type, info = self.analyze_page()
            print(f"   📊 데이터 타입: {data_type}")

            # 처리
            success = False
            if data_type in ['FILE', 'BOTH']:
                success = self.download_file(keyword)

            if data_type in ['API', 'BOTH']:
                api_success = self.save_api_info(keyword, dataset_url)
                success = success or api_success

            result = {
                'keyword': keyword,
                'title': title,
                'url': dataset_url,
                'data_type': data_type,
                'status': 'success' if success else 'partial',
                'info': info
            }
            self.results.append(result)

            return success

        except Exception as e:
            print(f"   ❌ 처리 실패: {e}")
            self.results.append({'keyword': keyword, 'status': 'error', 'error': str(e)})
            return False

    def run(self):
        """전체 수집 실행"""
        try:
            # 로그인 대기
            self.wait_for_login()

            # 우선순위 0
            print("\n" + "🟥 우선순위 0 — 기준 레이어".center(70, "="))
            for keyword in PRIORITY_0:
                self.process_dataset(keyword)
                time.sleep(2)

            # 우선순위 1
            print("\n" + "🟧 우선순위 1 — MVP 핵심 지표".center(70, "="))
            for keyword in PRIORITY_1:
                self.process_dataset(keyword)
                time.sleep(2)

            # 결과 저장
            result_file = self.download_dir / 'collection_results.json'
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            # 요약 출력
            print("\n" + "="*70)
            print("📊 수집 결과 요약")
            print("="*70)

            success = sum(1 for r in self.results if r.get('status') == 'success')
            partial = sum(1 for r in self.results if r.get('status') == 'partial')
            failed = sum(1 for r in self.results if r.get('status') in ['error', 'not_found'])

            print(f"✅ 성공: {success}")
            print(f"⚠️  부분 성공: {partial}")
            print(f"❌ 실패: {failed}")
            print(f"\n📁 결과 저장: {result_file}")

        except KeyboardInterrupt:
            print("\n⚠️  사용자가 중단했습니다.")
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\n✅ 10초 후 브라우저를 종료합니다...")
            time.sleep(10)
            self.driver.quit()


if __name__ == "__main__":
    collector = AutoCollector()
    collector.run()
