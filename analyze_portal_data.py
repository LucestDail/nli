#!/usr/bin/env python3
"""
공공데이터포털 CSV 분석 - 우선순위 데이터 찾기
"""

import pandas as pd

# 우선순위 0, 1 데이터 목록
PRIORITY_DATASETS = [
    # 우선순위 0
    "전국법정구역(읍면동)정보표준데이터",
    "국가데이터처_SGIS 행정구역 통계 및 경계",
    "주민등록인구통계",

    # 우선순위 1
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

# CSV 읽기
df = pd.read_csv("공공데이터활용지원센터_공공데이터포털 목록개방현황_20260630.csv", encoding='utf-8')

print(f"✅ CSV 로드 완료: {len(df)} 행")
print(f"컬럼: {list(df.columns)}\n")

# 각 데이터셋 검색
found_data = []

for keyword in PRIORITY_DATASETS:
    # 목록명에서 검색
    matches = df[df['목록명'].str.contains(keyword, case=False, na=False)]

    if len(matches) > 0:
        for idx, row in matches.iterrows():
            info = {
                '검색어': keyword,
                '목록명': row['목록명'],
                '목록유형': row['목록유형'],
                '제공형태': row.get('제공형태', ''),
                '파일데이터명': row.get('파일데이터명', ''),
                'API유형': row.get('API 유형', ''),
                'URL': row.get('목록 URL', ''),
                '표준데이터여부': row.get('표준데이터여부', ''),
            }
            found_data.append(info)

            print(f"{'='*60}")
            print(f"🔍 {keyword}")
            print(f"   목록명: {info['목록명']}")
            print(f"   목록유형: {info['목록유형']}")
            print(f"   제공형태: {info['제공형태']}")
            print(f"   URL: {info['URL']}")
            print()
    else:
        print(f"⚠️  '{keyword}' - 검색 결과 없음\n")

print(f"\n📊 총 {len(found_data)}개 발견")

# 결과를 JSON으로 저장
import json
with open('data/raw/found_datasets.json', 'w', encoding='utf-8') as f:
    json.dump(found_data, f, ensure_ascii=False, indent=2)

print(f"✅ 결과 저장: data/raw/found_datasets.json")
