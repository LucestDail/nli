#!/usr/bin/env python3
"""
공공데이터포털 자동 수집기 (반자동 버전)
- 사용자가 로그인 후, 자동으로 검색/판단/다운로드
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json

# 환경 변수 로드
load_dotenv()

class DataPortalCollector:
    def __init__(self):
        self.download_dir = Path(os.getenv('RAW_DATA_DIR', './data/raw'))
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # API 정보 저장
        self.api_dir = self.download_dir / 'api_info'
        self.api_dir.mkdir(exist_ok=True)

        # 크롬 옵션 설정
        chrome_options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": str(self.download_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        # 자동화 감지 우회
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 드라이버 초기화
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"❌ Chrome 드라이버 초기화 실패: {e}")
            raise

        self.wait = WebDriverWait(self.driver, 10)
        self.driver.maximize_window()

    def wait_for_login(self):
        """사용자가 로그인할 때까지 대기"""
        print("\n" + "="*60)
        print("🌐 Chrome 브라우저가 열렸습니다.")
        print("📌 공공데이터포털에 로그인해주세요.")
        print("📌 로그인 후 30초 기다립니다...")
        print("="*60)

        self.driver.get("https://www.data.go.kr/")

        # 30초 대기 (사용자 로그인 시간)
        time.sleep(30)
        print("\n🚀 자동 수집을 시작합니다!\n")

    def search_dataset(self, keyword):
        """데이터셋 검색"""
        print(f"\n🔍 '{keyword}' 검색 중...")

        # 검색 페이지 이동
        search_url = f"https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword={keyword}"
        self.driver.get(search_url)
        time.sleep(2)

        try:
            # 검색 결과 확인
            results = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".result-list .result-item, .result_list li"))
            )

            if not results:
                print(f"   ⚠️  검색 결과 없음")
                return None

            # 첫 번째 결과의 상세 링크 찾기
            first_result = results[0]
            try:
                detail_link = first_result.find_element(By.CSS_SELECTOR, "a.title, .title a, a")
                dataset_url = detail_link.get_attribute("href")
                title = detail_link.text.strip()

                print(f"   ✓ 발견: {title}")
                return dataset_url

            except NoSuchElementException:
                print(f"   ⚠️  상세 링크를 찾을 수 없음")
                return None

        except TimeoutException:
            print(f"   ⚠️  검색 결과 로딩 실패")
            return None

    def analyze_data_type(self, dataset_url):
        """데이터 타입 판단 (Open API vs 파일데이터)"""
        self.driver.get(dataset_url)
        time.sleep(2)

        data_type = None

        try:
            # 페이지 소스에서 데이터 타입 확인
            page_source = self.driver.page_source

            # Open API 확인
            if 'OPEN API' in page_source or 'OpenAPI' in page_source or 'API' in page_source:
                # API 활용신청 버튼 확인
                try:
                    api_button = self.driver.find_element(By.XPATH,
                        "//button[contains(text(), '활용신청') or contains(text(), 'API')]")
                    data_type = 'API'
                except NoSuchElementException:
                    pass

            # 파일데이터 확인
            if '파일데이터' in page_source or 'CSV' in page_source or 'SHP' in page_source:
                try:
                    file_button = self.driver.find_element(By.XPATH,
                        "//a[contains(@onclick, 'download') or contains(text(), '다운로드')]")
                    if data_type == 'API':
                        data_type = 'BOTH'  # API와 파일 둘 다
                    else:
                        data_type = 'FILE'
                except NoSuchElementException:
                    if not data_type:
                        data_type = 'FILE'

            if not data_type:
                # 태그로 확인
                try:
                    tags = self.driver.find_elements(By.CSS_SELECTOR, ".tagset_file, .tagset_api, .data-type")
                    tag_text = ' '.join([tag.text for tag in tags])
                    if 'API' in tag_text:
                        data_type = 'API'
                    elif '파일' in tag_text:
                        data_type = 'FILE'
                except:
                    pass

            print(f"   📊 데이터 타입: {data_type or '불명'}")
            return data_type or 'UNKNOWN'

        except Exception as e:
            print(f"   ⚠️  타입 분석 실패: {e}")
            return 'UNKNOWN'

    def download_file(self, keyword):
        """파일데이터 다운로드"""
        try:
            # 다운로드 버튼 찾기 (여러 패턴 시도)
            download_patterns = [
                "//a[contains(@onclick, 'fileDataDown')]",
                "//a[contains(text(), '다운로드') and contains(@class, 'ico-down')]",
                "//button[contains(text(), '다운로드')]",
                "//a[@title='파일 다운로드']"
            ]

            download_btn = None
            for pattern in download_patterns:
                try:
                    download_btn = self.driver.find_element(By.XPATH, pattern)
                    break
                except NoSuchElementException:
                    continue

            if download_btn:
                download_btn.click()
                print(f"   ⬇️  다운로드 시작...")
                time.sleep(5)  # 다운로드 대기
                return True
            else:
                print(f"   ⚠️  다운로드 버튼을 찾을 수 없음")
                return False

        except Exception as e:
            print(f"   ❌ 다운로드 실패: {e}")
            return False

    def handle_api(self, keyword, dataset_url):
        """Open API 처리 - 정보 저장"""
        try:
            # API 키 추출 시도
            api_info = {
                'keyword': keyword,
                'url': dataset_url,
                'note': 'API 활용신청 필요 - 수동 처리 권장'
            }

            # API 정보 저장
            api_file = self.api_dir / f"{keyword.replace(' ', '_')}.json"
            with open(api_file, 'w', encoding='utf-8') as f:
                json.dump(api_info, f, ensure_ascii=False, indent=2)

            print(f"   📝 API 정보 저장: {api_file}")
            print(f"   💡 나중에 활용신청 필요")
            return True

        except Exception as e:
            print(f"   ⚠️  API 정보 저장 실패: {e}")
            return False

    def collect_dataset(self, keyword, exact_name=None):
        """데이터셋 수집 (검색 → 판단 → 다운로드)"""
        print(f"\n{'='*60}")
        print(f"📦 수집: {keyword}")
        print(f"{'='*60}")

        # 1. 검색
        dataset_url = self.search_dataset(keyword)
        if not dataset_url:
            return False

        # 2. 타입 판단
        data_type = self.analyze_data_type(dataset_url)

        # 3. 처리
        if data_type in ['FILE', 'BOTH', 'UNKNOWN']:
            success = self.download_file(keyword)
        elif data_type == 'API':
            success = self.handle_api(keyword, dataset_url)
        else:
            print(f"   ⚠️  처리 불가")
            success = False

        time.sleep(2)  # 다음 검색 전 대기
        return success

    def collect_priority_0(self):
        """우선순위 0 - 기준 레이어"""
        print("\n" + "🟥 우선순위 0 — 기준 레이어".center(60, "="))

        datasets = [
            "전국법정구역(읍면동)정보표준데이터",
            "국가데이터처_SGIS 행정구역 통계 및 경계",
            "주민등록인구통계",
        ]

        results = []
        for keyword in datasets:
            success = self.collect_dataset(keyword)
            results.append((keyword, success))

        return results

    def collect_priority_1(self):
        """우선순위 1 - MVP 핵심 지표"""
        print("\n" + "🟧 우선순위 1 — MVP 핵심 지표".center(60, "="))

        datasets = [
            # D1 의료·건강
            "전국약국표준데이터",
            "전국응급의료기관표준데이터",
            "전국자동심장충격기표준데이터",

            # D2 교육·보육
            "전국어린이집표준데이터",
            "전국초중등학교위치표준데이터",
            "전국도서관표준데이터",

            # D3 생활편의·상업
            "전국전통시장표준데이터",
            "소상공인시장진흥공단_상가(상권)정보",

            # D4 문화·여가·체육
            "전국도시공원정보표준데이터",
            "전국체육시설표준데이터",

            # D5 교통·이동
            "전국버스정류소표준데이터",
            "전국주차장정보표준데이터",

            # D6 안전
            "전국CCTV표준데이터",
            "전국어린이보호구역표준데이터",
            "전국교통사고다발지역표준데이터",

            # D7 환경·기후
            "전국무더위쉼터표준데이터",
            "전국전기차충전소표준데이터",

            # D8 복지·돌봄
            "전국사회복지시설표준데이터",
        ]

        results = []
        for keyword in datasets:
            success = self.collect_dataset(keyword)
            results.append((keyword, success))

        return results

    def print_summary(self, results):
        """결과 요약"""
        print("\n" + "="*60)
        print("📊 수집 결과 요약")
        print("="*60)

        success_count = sum(1 for _, success in results if success)
        total_count = len(results)

        print(f"✅ 성공: {success_count}/{total_count}")
        print(f"❌ 실패: {total_count - success_count}/{total_count}")

        print("\n실패 목록:")
        for keyword, success in results:
            if not success:
                print(f"  - {keyword}")

    def close(self):
        """브라우저 종료"""
        print("\n✅ 수집 완료! 10초 후 브라우저를 종료합니다...")
        time.sleep(10)
        self.driver.quit()


def main():
    collector = DataPortalCollector()

    try:
        # 1. 사용자 로그인 대기
        collector.wait_for_login()

        # 2. 우선순위 0 수집
        results_0 = collector.collect_priority_0()

        # 3. 우선순위 1 수집
        results_1 = collector.collect_priority_1()

        # 4. 결과 요약
        all_results = results_0 + results_1
        collector.print_summary(all_results)

    except KeyboardInterrupt:
        print("\n⚠️  사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.close()


if __name__ == "__main__":
    main()
