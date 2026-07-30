"""
개발 인수인계용 핵심 입력 번들러 (allowlist 방식)
파이프라인이 실제 읽는 입력만 zip으로 묶는다. 개인파일·미사용 다운로드는 목록에 없으므로 절대 포함 안 됨.
새 개발자는: git clone → 이 zip을 repo 루트에 풀기 → 파이프라인 재실행.
실행: ./venv/bin/python make_handoff.py
출력: nli_handoff_data.zip (repo 루트, .gitignore의 *.zip 로 커밋 제외)
"""
import os, zipfile, textwrap

# 파이프라인이 실제 참조하는 입력만 (score_engine/build_geoframe/export/geocode에서 추출)
INCLUDE_DIRS = [
    "data/processed/sgis",     # 경계+통계(build_geoframe·export)
    "data/processed/hira",     # 약국·병원(score_engine)
    "data/raw/childcare_src",  # 어린이집 16조각(prep_childcare)
]
INCLUDE_FILES = [
    "data/processed/geocode_cache.json",
    "data/raw/소상공인시장진흥공단_상가(상권)정보_20260331.zip",
    "data/raw/전국CCTV표준데이터.csv",
    "data/raw/국토교통부_전국 버스정류장 위치정보_20251031.csv",
    "data/raw/전국도서관표준데이터.csv",
    "data/raw/전국도시공원정보표준데이터.csv",
    "data/raw/전국사회복지시설_좌표.csv",
    "data/raw/전국어린이보호구역표준데이터.csv",
    "data/raw/전국어린이집_운영중_좌표.csv",
    "data/raw/전국응급의료기관_API.csv",
    "data/raw/전국주차장정보표준데이터.csv",
    "data/raw/한국교육시설안전원_초중등학교위치_20260320.csv",
    "data/raw/한국전력공사_전기차충전소위경도_20251231.csv",
]

HANDOFF_MD = textwrap.dedent("""\
    # NLI 개발 인수인계 — 핵심 입력 데이터

    이 zip은 파이프라인이 실제 사용하는 입력만 담았습니다(개인파일·미사용 다운로드 제외).

    ## 설치
    1. 코드: `git clone https://github.com/LucestDail/nli.git && cd nli`
    2. 이 zip을 **repo 루트에서 그대로 풀기** → `data/` 가 채워집니다.
    3. 가상환경: `python3 -m venv venv && ./venv/bin/pip install duckdb pandas openpyxl xlrd requests`

    ## 파이프라인 재현
    ```
    ./venv/bin/python build_geoframe.py
    ./venv/bin/python score_engine.py
    ./venv/bin/python analyze_nli.py
    ./venv/bin/python export_map_geojson.py   # node/npx(mapshaper) 필요
    ./venv/bin/python generate_points.py
    ./venv/bin/python build_web.py
    cp nli_map.html index.html
    ./venv/bin/python verify_pipeline.py       # 28개 검사
    ```

    ## 참고
    - `.env`(API 키)는 보안상 미포함. 재수집(`collect_*.py`)·지오코딩(`geocode_welfare.py`)만 필요하고,
      **위 파이프라인 재현에는 불필요**(입력 데이터가 이미 포함됨).
    - 추가 데이터 수집은 `데이터수집_지시서_20260729.md` 참고.
    """)


def add(zf, path):
    if os.path.isdir(path):
        n = 0
        for root, _, files in os.walk(path):
            for fn in files:
                fp = os.path.join(root, fn)
                zf.write(fp, fp); n += 1
        return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(path) for f in fs), n
    else:
        zf.write(path, path); return os.path.getsize(path), 1


def main():
    out = "nli_handoff_data.zip"
    total, count, missing = 0, 0, []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        zf.writestr("HANDOFF.md", HANDOFF_MD)
        for p in INCLUDE_DIRS + INCLUDE_FILES:
            if not os.path.exists(p):
                missing.append(p); print(f"  ⚠️ 없음(건너뜀): {p}"); continue
            sz, n = add(zf, p)
            total += sz; count += n
            print(f"  ✅ {p}  ({sz/1e6:.1f}MB, {n}개)")
    print(f"\n번들: {out}")
    print(f"  원본 합계 {total/1e6:.0f}MB · 파일 {count}개 · zip 크기 {os.path.getsize(out)/1e6:.0f}MB")
    if missing:
        print(f"  누락 {len(missing)}건: {missing}")
    print("\n전달법: 이 zip을 클라우드(드라이브 등)로 공유 → 받는 사람은 repo clone 후 루트에서 압축해제.")


if __name__ == "__main__":
    main()
