# NLI API 온프렘 배포 가이드 (운영)

> 빠른 실행·엔드포인트·env는 [README.md](README.md) 참조. 이 문서는 **실제 서버(지자체·프롭테크) 프로덕션 배포**의 운영 관점 — 리버스 프록시·TLS·보안·백업·업데이트·문제해결.

## 0. 사전 요건
- Linux 서버(Ubuntu 22.04+ 권장), Docker + Docker Compose v2, 디스크 ~2GB, 메모리 **최소 1GB**(DuckDB가 geojson을 메모리 로드; 여유 2GB 권장).
- 인바운드: 앱은 8080(내부), 공개는 리버스 프록시(80/443)로.
- 스냅샷 3파일 전달받기: `nli_map.geojson`(~17MB) · `nli_points.json`(~26MB) · `datasets.yml`. (공급자가 `ingest.py`로 생성)

## 1. 배치
```bash
git clone <repo> nli && cd nli/server
mkdir -p snapshot && cp /전달경로/{nli_map.geojson,nli_points.json,datasets.yml} snapshot/
cp .env.example .env      # 아래 2절대로 API_KEY·레이트리밋 설정
docker compose up -d --build
curl -s localhost:8080/api/health   # {"status":"ok","snapshot":true,"dong":3559}
```

## 2. 보안 (공개 서버는 필수)
`.env`:
```
API_KEY=<32자+ 랜덤>     # 미설정=완전 공개. B2B/과금 대비 시 반드시 설정
RATELIMIT=1
RL_CAPACITY=120          # IP당 버킷 용량
RL_REFILL=2              # 초당 토큰 충전(=지속 2req/s, 버스트 120)
```
- **앱을 외부에 직접 노출하지 말 것.** compose 포트를 `127.0.0.1:8080:8080`으로 묶고 리버스 프록시 경유(3절).
- `API_KEY` 설정 시 모든 `/api/*`에 `?key=` 또는 `x-api-key` 헤더 필요(`/api/health`는 개방).
- 트래픽 많으면 `RL_CAPACITY/RL_REFILL` 상향. 레이트리밋은 인메모리(단일 인스턴스 기준).

## 3. 리버스 프록시 + TLS (nginx 예)
```nginx
server {
  listen 443 ssl;
  server_name nli.example.go.kr;
  ssl_certificate     /etc/letsencrypt/live/nli.example.go.kr/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/nli.example.go.kr/privkey.pem;
  client_max_body_size 1m;
  location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;   # 레이트리밋이 실제 IP 인식
    proxy_read_timeout 30s;
  }
}
```
- 인증서: `certbot --nginx -d nli.example.go.kr`. 폐쇄망이면 사설 CA/자가서명.
- 포트 80/443 차단 환경(일부 통신사)은 대체 포트(:8030 등) + `server_name` 매칭.

## 4. 헬스체크 · 자동복구
- compose에 healthcheck 내장(`/api/health` 30s). `restart: unless-stopped`로 크래시 자동 재기동.
- 외부 감시: 크론/uptime로 `curl -fsS localhost:8080/api/health || docker compose restart`.
- 로그: `docker compose logs -f nli`(접근·에러·레이트리밋).

## 5. 데이터 업데이트 · 롤백
```bash
# 공급자가 새 스냅샷 3파일 전달 → 무중단 근접 교체
cp /새경로/{nli_map.geojson,nli_points.json,datasets.yml} snapshot.new/
mv snapshot snapshot.bak.$(date +%F) && mv snapshot.new snapshot
docker compose restart nli && curl -s localhost:8080/api/health
# 롤백: mv snapshot snapshot.bad && mv snapshot.bak.<날짜> snapshot && docker compose restart
```
- 스냅샷은 읽기전용 마운트(`:ro`) — 앱이 데이터를 변조하지 않음.
- 버전 확인: `/api/meta`의 기준시점·`note`(복지 지오코딩 커버리지 등).

## 6. 백업
- 백업 대상 = **스냅샷 3파일 + `.env`**뿐(앱은 무상태). `tar czf nli-backup-$(date +%F).tgz snapshot .env`.
- 복구 = 클론 + 스냅샷·env 복원 + `up -d`.

## 7. 문제 해결
| 증상 | 원인·조치 |
|---|---|
| `{"error":"..."}` 400·한글 파라미터 | URL 한글은 **percent-encoding** 필수(예 `house=%EC%9C%A1%EC%95%84`). uvicorn이 raw 한글 URL 거부. |
| health `snapshot:false` | 스냅샷 경로/파일 확인(`docker compose logs`). `NLI_GEOJSON` env와 마운트 경로 일치. |
| 429 `rate_limited` | 정상 방어. 신뢰 클라이언트면 `RL_CAPACITY/REFILL` 상향 또는 프록시 화이트리스트. |
| 메모리 부족·OOM | DuckDB geojson 로드에 ~수백MB. 서버 메모리 1GB+ 확보. |
| 포트 충돌 | compose `ports` 변경(예 `18080:8080`). |

## 8. 비도커(systemd) 대안
```ini
# /etc/systemd/system/nli-api.service
[Service]
WorkingDirectory=/opt/nli
Environment=NLI_GEOJSON=/opt/nli/server/snapshot/nli_map.geojson
Environment=NLI_POINTS=/opt/nli/server/snapshot/nli_points.json
Environment=NLI_DATASETS=/opt/nli/server/snapshot/datasets.yml
Environment=API_KEY=<키>
ExecStart=/opt/nli/venv/bin/python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8080
Restart=always
```
`systemctl enable --now nli-api` + 3절 프록시.

---
점수는 전국 읍면동 상대평가(백분위) **참고용**(시설 밀도·근접 기반이라 도시성 일부 반영 → `nli_cohort`로 동일 도농유형 내 비교 권장). B2G 활용은 지역 *내부* 상대격차(사각지대·`/api/diag`)가 밀도편향에 강건. 출처·라이선스는 `/api/meta`.
