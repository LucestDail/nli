# 동네살기지수 NLI — 배포 가이드

`index.html`(= `nli_map.html`)은 **외부 의존성이 없는 자체완결 단일 파일**입니다
(지도 타일 CartoDB·폰트 CDN만 인터넷 필요). 정적 호스팅에 파일 하나만 올리면 서비스됩니다.

## 옵션 A — GitHub Pages (무료, 추천)
```bash
# 1) GitHub에 새 repo 생성 후 (예: nli-dongne)
gh repo create nli-dongne --public --source=. --remote=origin   # gh CLI 사용 시
# 또는 수동: git remote add origin https://github.com/<계정>/nli-dongne.git

git add index.html nli_map.html *.py *.md .gitignore
git commit -m "NLI 대시보드 1차 배포"
git branch -M main && git push -u origin main

# 2) GitHub repo → Settings → Pages → Source: main / root 저장
#    → https://<계정>.github.io/nli-dongne/ 에서 접속
```

## 옵션 B — Netlify / Vercel (드래그앤드롭)
- Netlify: app.netlify.com → "Add new site" → `index.html` 있는 폴더 드래그. 즉시 URL 발급.
- Vercel: `vercel` CLI 또는 대시보드에서 폴더 배포.

## 옵션 C — 사내 서버 (nginx)
- `index.html`을 웹루트(예: `/var/www/nli/`)에 복사 → nginx location 하나 추가.
- 홈랩 게이트웨이(192.168.11.25)에 `/nli/` 경로로 추가 가능.

## 갱신(재빌드) 방법
데이터가 추가되면:
```bash
./venv/bin/python score_engine.py        # 스코어 재계산
./venv/bin/python analyze_nli.py          # 사각지대·결핍 재판정
./venv/bin/python export_map_geojson.py   # 지도 경계(mapshaper 위상 단순화)
./venv/bin/python generate_points.py      # 시설 포인트
./venv/bin/python build_web.py            # nli_map.html 생성
cp nli_map.html index.html                # 배포 진입점 갱신
```

## 주의
- `data/`, 원천 CSV/ZIP, `.env`는 `.gitignore`로 제외됨(대용량·민감). 배포엔 불필요.
- `index.html` 약 18MB(지오데이터 내장). GitHub 100MB 제한 이내라 정상 커밋됨.
