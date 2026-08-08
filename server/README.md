# NLI API 서버 — 온프렘 패키지

전국 읍면동 동네살기지수(NLI)를 REST+OpenAPI로 제공하는 FastAPI 서버. 스냅샷(정적 데이터) 읽기전용 서빙 + 추천·진단. 자가호스팅·온프렘.

## 빠른 실행 (Docker)
```bash
# 1) 스냅샷 3파일을 server/snapshot/ 에 배치
mkdir -p server/snapshot
cp data/processed/nli_map.geojson data/processed/nli_points.json data/datasets.yml server/snapshot/
#   (nli_points.json이 루트에 있으면 그걸 복사)

# 2) 기동
cd server
cp .env.example .env          # 필요 시 API_KEY 설정
docker compose up -d --build

# 3) 확인
curl http://localhost:8080/api/health
open http://localhost:8080/docs      # OpenAPI(Swagger)
open http://localhost:8080/           # 데모/도구
```

## 스냅샷 갱신
원본 데이터 갱신 → 루트에서 `./venv/bin/python pipeline/ingest.py` → 새 스냅샷 3파일을 `server/snapshot/`에 복사 → `docker compose restart`.

## 로컬 개발(도커 없이)
```bash
# 리포 루트에서(데이터 경로가 루트 기준)
./venv/bin/python -m uvicorn server.app.main:app --port 8080
```

## API 엔드포인트
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/health` | 상태·스냅샷 로드 여부 |
| GET | `/api/meta` | 도메인 정의·지표 출처·기준시점·라이선스 |
| GET | `/api/dong/{adm_cd}` | 동 상세(NLI·9도메인·가격·시설·특성) |
| GET | `/api/score?lat=&lon=` | 좌표 → 소속 동(point-in-polygon) |
| GET | `/api/rank?sido=&cohort=&metric=&limit=` | 순위 |
| GET | `/api/recommend?house=&budget=&base=&km=&limit=` | 맞춤 추천 Top(house: 일반/육아/1인/고령/반려) |
| GET | `/api/diag` · `/api/diag/{sgg}` | 지자체 진단(취약 도메인·사각지대) |
| GET | `/api/geojson` · `/api/points` | 지도용 원본 |

- 응답 UTF-8 JSON. 에러 `{error, message}`.
- OpenAPI 문서: `/docs`, `/openapi.json`.
- CORS: `GET /api/**` 전 오리진. 레이트리밋: IP 토큰버킷(기본 120/refill 2/s).
- 인증(선택): `API_KEY` env 설정 시 `?key=` 또는 `x-api-key` 헤더.

## 설정(env)
| 변수 | 기본 | 설명 |
|---|---|---|
| `API_KEY` | (없음) | 설정 시 인증 요구 |
| `RATELIMIT` | 1 | 레이트리밋 on/off |
| `NLI_GEOJSON`/`NLI_POINTS`/`NLI_DATASETS` | /app/data/... | 스냅샷 경로 |
| `PORT` | 8080 | 리슨 포트 |

## 아키텍처
```
스냅샷(geojson+points+datasets.yml)  ← ingest.py 산출
      │ DuckDB(spatial) 읽기전용 로드
   FastAPI ── REST+OpenAPI(/docs) + 정적(데모·도구)
      │ docker-compose
      ▼ :8080
```
점수는 전국 읍면동 상대평가(백분위) 참고용. 데이터 출처·라이선스는 `/api/meta` 참조.
