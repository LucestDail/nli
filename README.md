# 동네살기지수 (NLI · Neighborhood Livability Index)

공공데이터 표준데이터를 **읍면동(행정동) 단위**로 융합해 지역 생활여건을 9개 도메인으로 정량화한 지수 + 정적 웹 대시보드 + 온프렘 API.

- **분석 단위**: 전국 행정동 3,559개 (SGIS 2025 2분기 경계) · 총인구 정합 51.8M
- **스택**: 순수 Python (pandas · DuckDB spatial · mapshaper) 데이터/지오 파이프라인 → 자체완결 단일 `index.html` (Leaflet SPA) + FastAPI 온프렘 패키지(`server/`)
- **빌드 프레임워크 없음**: 검증은 "스크립트 실행 + 실측 수치·상식 확인" (`verify_pipeline.py`, 41개 assert)

> 점수는 전국 읍면동 **상대평가(백분위) 참고용**입니다. 시설 밀도·근접 기반이라 도시성(인구밀도)을 일부 반영하므로, **동일 도농유형 내 상대비교**와 **지역 내부 사각지대 진단**에 활용을 권합니다(절대순위 맹신 X).

---

## 9개 도메인 · 32개 지표

| 도메인 | 지표 |
|---|---|
| D1 의료·건강 | 약국 · 의료기관 · 응급의료 |
| D2 교육·보육 | 초중등학교 · 학원(상가 세분) · 어린이집 · 도서관 |
| D3 생활편의·상업 | 생활편의 상가(음식·소매·수리·숙박) · 대규모점포 · 주유소 · 무료와이파이 |
| D4 문화·여가·체육 | 도시공원 · 여가 상가(예술·스포츠) · 체육시설 · 박물관·미술관 · 공연장 · 영화관 |
| D5 교통·이동 | 버스정류소 · 지하철역 · 주차장 · 자전거(보관소·대여소) |
| D6 안전 | CCTV · 어린이보호구역 · 안전비상벨 · 민방위대피 |
| D7 환경·기후 | 전기차충전소 · 무더위쉼터 · 보호수 |
| D8 복지·돌봄 | 사회복지시설(VWorld 지오코딩 약 95% 커버) · 경로당·마을회관 |
| D9 반려·동물 | 동물병원 |

*지역특성 축*: 인구밀도 · 인구 · 고령/유소년비중 · 아파트비율 · 노후주택비율(1999년 이전) · 아파트 실거래 평당가.

## 방법론 (스코어링)

지표별 **[밀도(인구 1만명당 · 면적 ㎢당 혼합) 백분위 + 근접성(최근접 m) 백분위]** → 도메인 가중평균 → NLI 도메인 가중합 → **S/A/B/C/D** 등급(10/25/30/25/10).

보정:
- **인구가중 중심점**: 상가 밀집 위치로 대체(큰 동의 산지 기하중심 왜곡 방지)
- **도농 코호트**: 행정동명(면/읍/동) + 인구밀도 기반 3분류(병행)
- **동일 유형 상대비교(`NLI_cohort`)**: 밀도가 다른 지역을 억지로 한 줄로 세우지 않도록, 같은 도농유형(도시/도농복합/농촌)끼리 백분위 제공 — 앱에서 "동일 유형 내 상위 %"로 표시
- 결측 재정규화 · MIN_POP=100 · 부정지표 `neg` 백분위 반전

**가중치**: 기본은 **균등**(OECD 복합지표 관행·투명성). 앱에서 페르소나(가구유형)와 객관가중 프리셋(정보량/엔트로피·CRITIC, `analysis/weight_analysis.py`)을 실시간 적용. *분산 ≠ 중요도* 한계 명시.

---

## 파이프라인 재현

```bash
# 원본 데이터(gitignore) → 스냅샷 한 번에: score→analyze→export→points→web→cp→verify
./venv/bin/python pipeline/ingest.py

# (지오프레임까지 새로: 경계·인구·주택 변경 시)
./venv/bin/python pipeline/build_geoframe.py    # SGIS 경계+인구+주택 → nli.duckdb
./venv/bin/python pipeline/ingest.py

# 검증(총인구·조인·좌표·등급·세분·임베드 assert)
./venv/bin/python pipeline/verify_pipeline.py
open index.html
```

**데이터 추가법**: `data/datasets.yml`에 항목 하나 추가
`{key, name, domain, path, reader, lon, lat, [prox], [w], [neg], [export_points]}` → 자동 편입(코드 수정 없음).

디렉토리: `pipeline/`(코어) · `prep/`(가공) · `collect/`(API수집) · `analysis/`(가중치·통계) · `legacy/`(구 Selenium, 미사용). 원본·중간 산출물(`data/`, `*.duckdb`, `*.geojson`, `nli_points.json`)은 커밋하지 않음(`.gitignore`).

---

## 대시보드 (3탭 SPA)

**① 지도** — 지표별 백분위 색칠 · 사각지대/인구대비 모드 · 시설 포인트 11종(확대 시 토글: 약국·응급·어린이집·학교·도서관·공원·체육·주차·전기차·복지·경로당) · 동 클릭 상세(9도메인·시설개수·최근접·아파트 실거래·통근·**동일 유형 내 상위 %**) · 사이드바 페르소나·가중치 슬라이더.

**② 내 동네 찾기 (B2C)** — 가구유형(육아·1인·고령·반려)·예산·통근으로 **맞춤 Top10** · **가성비 동네**(살기지수÷아파트값) · 지역 순위 · 동 검색 → 상세 카드(전국/동일유형 상위 % 이중 표시) · 상세 모달 · "이 동네가 속한 지역 진단 보기" 연결.

**③ 인사이트 (B2G)** — 지자체 229곳 **생활여건 진단**: 취약 도메인·**사각지대 동**(인구 1만+ 인데 특정 도메인 전국 하위 20%) 자동판정 · **전국/동일 유형(자치구·시·군) 취약순위** · 다중선택 → **통계 분석 모달**(레이더·상관 히트맵·회귀 산점도·관할 동 스크롤) · **진단 리포트(PDF)**.

**공유 딥링크** — 현재 상태(탭·선택동·가중치·지표·통근·비교)를 URL 해시에 인코딩:
```
index.html#v=find                 # 내 동네 찾기
index.html#v=insight              # 지자체 진단
index.html#d=노형동&m=D1&md=blind  # 노형동 상세 + 의료 사각지대 지도
index.html#c=역삼1동~노형동         # 지역 비교 패널
```

---

## 온프렘 API 패키지 (`server/`)

FastAPI + DuckDB. 스냅샷(정적 데이터) 읽기전용 서빙 + 추천·진단. `clone → docker compose up → API+데모`.

```bash
cd server && cp .env.example .env && docker compose up -d --build
curl localhost:8080/api/health        # {"status":"ok","dong":3559}
open localhost:8080/docs              # OpenAPI(Swagger) 자동
```

주요 엔드포인트: `/api/dong/{adm_cd}` · `/api/score?lat=&lon=` · `/api/rank` · `/api/recommend` · `/api/diag[/{sgg}]` · `/api/geojson` · `/api/points` · `/api/meta` · `/api/health`. 에러 `{error,message}` · CORS · IP 레이트리밋 · 선택 API키. 설치·운영은 [`server/README.md`](server/README.md) · [`server/DEPLOY.md`](server/DEPLOY.md).

---

## 재현 스크립트 (핵심)

```
build_geoframe.py     경계+인구+주택 지오프레임 → nli.duckdb
score_engine.py       스코어링 엔진 (datasets.yml 기반)
analyze_nli.py        사각지대·결핍·프로필 판정
export_map_geojson.py mapshaper 위상단순화 + 점수·실거래가 조인
generate_points.py    시설 포인트(지연로딩)
build_web.py          SPA(index.html) 생성
ingest.py             score→…→web→verify 오케스트레이션
verify_pipeline.py    파이프라인 정합성 검증기(41 assert)
analysis/weight_analysis.py  객관가중(엔트로피·CRITIC)
collect/*.py          data.go.kr API 수집 · VWorld 지오코딩
```

## 데이터 출처

공공데이터포털 표준데이터 · SGIS(통계지리정보) 경계·인구(2025 2Q) · 건강보험심사평가원 · 소상공인시장진흥공단 · 국토교통부 아파트 실거래가 · safetydata.go.kr · VWorld 지오코딩. 출처·시점은 앱 하단 및 `/api/meta` 참조.

**라이브**: [lucestdail.github.io/nli](https://lucestdail.github.io/nli/)
