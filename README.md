# 동네살기지수 (NLI · Neighborhood Livability Index)

공공데이터 표준데이터를 **읍면동(행정동) 단위**로 융합해, "어디가 살기 좋은 동네인가"를 9개 도메인으로 정량화한 지수 + 정적 웹 대시보드.

- **분석 단위**: 전국 행정동 3,559개 (SGIS 2025 2분기 경계)
- **총인구 정합**: 51.8M
- **스택**: 순수 Python (pandas · DuckDB spatial · mapshaper) 데이터/지오 파이프라인 → 자체완결 단일 `index.html` (Leaflet SPA)
- **빌드 프레임워크 없음**: 검증은 "스크립트 실행 + 실측 수치·상식 확인" (`verify_pipeline.py`)

---

## 9개 도메인 · 32개 지표

| 도메인 | 지표 |
|---|---|
| D1 의료·건강 | 약국 · 의료기관 · 응급의료 |
| D2 교육·보육 | 초중등학교 · **학원**(상가 세분) · 어린이집 · 도서관 |
| D3 생활편의·상업 | **생활편의 상가**(음식·소매·수리·숙박) · 대규모점포 · 주유소 · 무료와이파이 |
| D4 문화·여가·체육 | 도시공원 · **여가 상가**(예술·스포츠) · 체육시설 · 박물관·미술관 · 공연장 · 영화관 |
| D5 교통·이동 | 버스정류소 · 지하철역 · 주차장 · 자전거(보관소·대여소) |
| D6 안전 | CCTV · 어린이보호구역 · 안전비상벨 · 민방위대피 |
| D7 환경·기후 | 전기차충전소 · 무더위쉼터 · 보호수 |
| D8 복지·돌봄 | 사회복지시설(VWorld 지오코딩 88% 커버) · 경로당·마을회관 |
| D9 반려·동물 | 동물병원 |

*지역특성 축*: 인구밀도 · 인구 · 고령/유소년비중 · 아파트비율 · **노후주택비율**(1999년 이전) · **아파트 실거래 평당가**.

## 방법론 (스코어링)

지표별 **[밀도(인구 1만명당) 백분위 + 근접성(최근접 m) 백분위] 혼합** → 도메인 가중평균 → NLI 도메인 가중합 → **S/A/B/C/D** 등급(10/25/30/25/10).

보정:
- **인구가중 중심점**: 상가 밀집 위치로 대체(큰 동의 산지 기하중심 왜곡 방지)
- **도농 코호트**: 행정동명(면/읍/동) + **인구밀도 기반**(병행) 3분류
- **부정지표**: `neg` 플래그로 백분위 반전(교통사고 등 수집 시)
- 결측 재정규화, MIN_POP=100

**가중치**: 기본은 **균등**(OECD 복합지표 관행·투명성). 앱에서 페르소나 10종 + 객관가중 프리셋(**정보량/엔트로피·CRITIC**, `weight_analysis.py` 산출)을 실시간 적용. *분산 ≠ 중요도* 한계 명시.

---

## 파이프라인 재현

```bash
# 표준 순서 (루트에서 실행, 각 단계가 파일 산출)
./venv/bin/python pipeline/build_geoframe.py       # SGIS 경계+인구+주택 → nli.duckdb(dong, stat_long)
./venv/bin/python pipeline/score_engine.py         # 시설점 공간결합 → 밀도(인구+면적)·근접성·NLI·등급
./venv/bin/python pipeline/analyze_nli.py          # 사각지대·결핍·프로필 → nli_report.md
./venv/bin/python pipeline/export_map_geojson.py   # mapshaper 위상단순화 + 점수·실거래가 조인 → nli_map.geojson
./venv/bin/python pipeline/generate_points.py      # 시설 포인트 → nli_points.json
./venv/bin/python pipeline/build_web.py            # SPA 생성 → nli_map.html
cp nli_map.html index.html

# 검증 (총인구·조인·좌표·등급·세분·임베드 assert)
./venv/bin/python pipeline/verify_pipeline.py

# 로컬 미리보기
open index.html
```

**데이터 추가법**: `score_engine.py`의 `DATASETS` 리스트에 dict 하나 추가
`{key, name, domain, path, reader, lon, lat, [prox], [w], [catcol/catkeep], [neg]}` → 자동 편입.

---

## 대시보드 기능

7탭 SPA(지도 기본·홈·순위·추천·비교·통계·진단):

- **지도**: 지표별 백분위 색칠 · 사각지대/인구대비 모드 · 시설 포인트(확대 시) · 클릭 상세 · 사이드바에 페르소나 10종+객관가중 프리셋·실시간 가중치 슬라이더
- **🎯 추천(B2C)**: 가구유형(육아·1인·고령·반려)·예산·통근 입력 → 맞춤 가중 살기지수 **Top10** + **가성비 동네**(살기지수÷아파트값, 시도필터·공유)
- **순위**: 테마·시도·유형 필터 + **🚇 통근 보정**(기준지 반경 내 직선거리 필터)
- **비교**: 최대 4곳 지표 비교
- **통계**: 지역특성×도메인 상관 히트맵 · 도농 격차(명칭/밀도 토글) · 시도 순위 · 산점도·회귀(평문 해석)
- **🩺 진단(B2G)**: 지자체 229곳 생활여건 진단 — 취약 도메인·사각지대 동 자동판정 · 진단 리포트(복사·CSV·PDF) · 지도 연동
- **🔗 공유 딥링크**: 현재 상태(탭·선택동·가중치·지표·통근·산점도·비교)를 URL 해시에 인코딩

### 딥링크 예시
```
index.html#v=rank&cb=역삼1동&ck=10        # 역삼동 10km 통근 순위
index.html#d=노형동&m=D1&md=blind         # 노형동 상세 + 의료 사각지대 지도
index.html#v=stats&sx=dens&sy=D1          # 인구밀도↔의료 산점도
```

---

## 재현 스크립트

```
build_geoframe.py     경계+인구+주택[S] 지오프레임
score_engine.py       스코어링 엔진 (config 기반 DATASETS)
analyze_nli.py        사각지대·결핍·프로필 판정 + 리포트
export_map_geojson.py mapshaper 위상단순화 + 점수 조인
generate_points.py    시설 포인트 생성
build_web.py          SPA(index.html) 생성
weight_analysis.py    객관가중(엔트로피·CRITIC) 산출
verify_pipeline.py    파이프라인 정합성 검증기
collect_*.py          data.go.kr API 수집
geocode_welfare.py    VWorld 주소 → 좌표 지오코딩
고도화_로드맵_*.md      방법론 한계(M1~M10)·데이터갭·Phase
데이터수집_지시서_*.md   추가 데이터 수집 가이드(직접링크·검색어)
```

원본·중간 산출물(`data/`, `*.duckdb`, `*.geojson`, `*.csv/zip`)은 커밋하지 않음(`.gitignore`). 배포엔 자체완결 `index.html` 하나면 충분.

## 데이터 출처

공공데이터포털 표준데이터 · SGIS(통계지리정보) 경계·인구 · 건강보험심사평가원 · 소상공인시장진흥공단 · VWorld 지오코딩.

> 점수는 전국 상대평가(백분위) 기반 참고용입니다.
