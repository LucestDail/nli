"""
NLI 스코어링 엔진 (Phase 1 스켈레톤) — config 기반
파이프라인: 시설 포인트 로드 → 5179 재투영 → 읍면동 공간결합(point-in-polygon)
           → 공급밀도(인구 1만명당) + 근접성(최근접 m) → 전국 백분위 정규화
           → 도메인 점수(가중평균) → NLI(도메인 가중합) → 등급(S~D)

산출물: data/processed/nli.duckdb 테이블 nli_scores + data/processed/nli_scores_mvp.csv
실행:   ./venv/bin/python score_engine.py

★ 데이터 추가법: 아래 DATASETS 리스트에 dict 하나만 추가하면 자동으로 파이프라인에 편입.
  {key, name, domain, path, reader, lon, lat, [prox], [w], [filter], [catcol/catkeep], [neg]}
  neg=True → 부정지표(많을수록 나쁨): 백분위 반전. catcol/catkeep → 컬럼값으로 업종/유형 세분.
"""
import duckdb, pandas as pd, os

DB = "data/processed/nli.duckdb"
HIRA = "data/processed/hira"
RAW = "data/raw"
PROX_RADII = (1000, 4000, 16000, 64000, 256000)  # 근접성 확장반경(m): 가까운 반경부터 넓혀감
MIN_POP = 100       # 이 미만 인구 동은 밀도 정규화에서 제외(0/극소인구 왜곡 방지, 기획서 §4.2/§6-3)

# 도메인 정의. D1~D8 모두 읍면동 시설점 기반(D8=사회복지 지오코딩)
DOMAINS = {"D1": "의료·건강", "D2": "교육·보육", "D3": "생활편의·상업",
           "D4": "문화·여가·체육", "D5": "교통·이동", "D6": "안전", "D7": "환경·기후",
           "D8": "복지·돌봄"}

# 도메인 가중치(NLI 기본 = 균등). 웹 대시보드의 페르소나 슬라이더가 이 기본을 실시간 덮어씀.
DOMAIN_WEIGHTS = {d: 1.0 for d in DOMAINS}
# 지표(도메인 내) 가중치: DATASETS 각 dict의 w(기본 1.0)로 지정. 도메인 내 가중평균에 사용.

# ── 확보 데이터. 재수집분은 여기에 dict 추가만 하면 됨 ──
#    prox=False → 근접성 산출 생략(대용량·근접성 무의미한 밀집시설). 기본 True.
DATASETS = [
    dict(key="pharmacy", name="약국", domain="D1",
         path=f"{HIRA}/2.약국정보서비스(2026.6.).xlsx", reader="xlsx",
         lon="좌표(X)", lat="좌표(Y)"),
    dict(key="clinic", name="의료기관", domain="D1",
         path=f"{HIRA}/1.병원정보서비스(2026.6.).xlsx", reader="xlsx",
         lon="좌표(X)", lat="좌표(Y)"),
    dict(key="emergency", name="응급의료기관", domain="D1",
         path=f"{RAW}/전국응급의료기관_API.csv", reader="csv",
         lon="경도", lat="위도"),
    dict(key="school", name="초중등학교", domain="D2",
         path=f"{RAW}/한국교육시설안전원_초중등학교위치_20260320.csv", reader="csv",
         lon="경도", lat="위도"),
    # 상가(상권) 1개 파일을 상권업종대분류로 세분 → 도메인 정합↑(M5) & 단일지표 도메인 보강(M1)
    #   생활편의(음식·소매·수리·숙박)=D3 / 학원·교육=D2 / 예술·스포츠 여가=D4. B2B(부동산·과학기술·시설관리)·보건의료(HIRA중복) 제외.
    dict(key="store", name="생활편의상가", domain="D3",
         path=f"{RAW}/소상공인시장진흥공단_상가(상권)정보_20260331.zip", reader="zip_csv",
         lon="경도", lat="위도", catcol="상권업종대분류명",
         catkeep=["음식", "소매", "수리·개인", "숙박"], prox=False),  # 대량, 근접성 무의미 → 밀도만
    dict(key="academy", name="학원·교육상가", domain="D2",
         path=f"{RAW}/소상공인시장진흥공단_상가(상권)정보_20260331.zip", reader="zip_csv",
         lon="경도", lat="위도", catcol="상권업종대분류명", catkeep=["교육"]),
    dict(key="leisure", name="여가·스포츠상가", domain="D4",
         path=f"{RAW}/소상공인시장진흥공단_상가(상권)정보_20260331.zip", reader="zip_csv",
         lon="경도", lat="위도", catcol="상권업종대분류명", catkeep=["예술·스포츠"]),
    dict(key="park", name="도시공원", domain="D4",
         path=f"{RAW}/전국도시공원정보표준데이터.csv", reader="csv",
         lon="경도", lat="위도"),
    dict(key="bus", name="버스정류소", domain="D5",
         path=f"{RAW}/국토교통부_전국 버스정류장 위치정보_20251031.csv", reader="csv",
         lon="경도", lat="위도"),
    dict(key="cctv", name="CCTV", domain="D6",
         path=f"{RAW}/전국CCTV표준데이터.csv", reader="csv",
         lon="WGS84경도", lat="WGS84위도"),
    dict(key="ev", name="전기차충전소", domain="D7",
         path=f"{RAW}/한국전력공사_전기차충전소위경도_20251231.csv", reader="csv",
         lon="경도", lat="위도"),
    dict(key="welfare", name="사회복지시설", domain="D8",
         path=f"{RAW}/전국사회복지시설_좌표.csv", reader="csv",
         lon="경도", lat="위도"),   # VWorld 지오코딩(85% 커버) → 읍면동 정밀
    # ── P0 편입(2026-07-30): 도메인당 2+지표로 보강(M1) ──
    dict(key="childcare", name="어린이집", domain="D2",
         path=f"{RAW}/전국어린이집_운영중_좌표.csv", reader="csv",
         lon="경도", lat="위도"),   # prep_childcare.py 가공(운영중 21K)
    dict(key="library", name="도서관", domain="D2",
         path=f"{RAW}/전국도서관표준데이터.csv", reader="csv",
         lon="경도", lat="위도"),
    dict(key="parking", name="주차장", domain="D5",
         path=f"{RAW}/전국주차장정보표준데이터.csv", reader="csv",
         lon="경도", lat="위도"),
    dict(key="childzone", name="어린이보호구역", domain="D6",
         path=f"{RAW}/전국어린이보호구역표준데이터.csv", reader="csv",
         lon="경도", lat="위도"),
    dict(key="sports", name="체육시설", domain="D4",
         path=f"{RAW}/전국체육시설_공공_좌표.csv", reader="csv",
         lon="시설좌표경도", lat="시설좌표위도"),   # prep_sports.py 가공(공공 40K, 여가상가와 비중복)
    dict(key="shelter", name="무더위쉼터", domain="D7",
         path=f"{RAW}/전국무더위쉼터_API.csv", reader="csv",
         lon="LO", lat="LA"),   # collect_shelter.py 수집(safetydata API, 60.9K)
]


def _read_csv_any(path, usecols=None):
    for enc in ("cp949", "utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc, dtype=str, usecols=usecols)
        except (UnicodeDecodeError, LookupError):
            continue
    return pd.read_csv(path, encoding="cp949", dtype=str, usecols=usecols, errors="replace")


_ZIP_CACHE = {}   # 동일 zip(상가 2.7만건)을 업종 세분 데이터셋마다 재파싱하지 않도록 캐시


def _read_zip_csv(path, cols):
    """zip 안 여러 CSV(시도별 분할)를 cols만 읽어 concat. path 기준 캐시."""
    if path in _ZIP_CACHE:
        return _ZIP_CACHE[path]
    import zipfile, io
    z = zipfile.ZipFile(path)
    frames = []
    for n in z.namelist():
        if not n.lower().endswith(".csv"):
            continue
        raw = z.read(n)
        for enc in ("cp949", "utf-8-sig", "utf-8"):
            try:
                frames.append(pd.read_csv(io.BytesIO(raw), encoding=enc, usecols=cols, dtype=str)); break
            except (UnicodeDecodeError, LookupError, ValueError):
                continue
    df = pd.concat(frames, ignore_index=True)
    _ZIP_CACHE[path] = df
    return df


def read_points(ds):
    """시설 파일 → (lon, lat) DataFrame (유효 좌표만). reader: xlsx | csv | zip_csv."""
    if ds["reader"] == "xlsx":
        df = pd.read_excel(ds["path"], dtype=str)
    elif ds["reader"] == "zip_csv":
        cols = [ds["lon"], ds["lat"]] + ([ds["catcol"]] if ds.get("catcol") else [])
        df = _read_zip_csv(ds["path"], cols)
    else:
        df = _read_csv_any(ds["path"])
    if ds.get("catkeep"):   # 상권업종대분류 세분 필터
        df = df[df[ds["catcol"]].isin(ds["catkeep"])]
    if ds.get("filter"):
        df = df.query(ds["filter"])
    out = pd.DataFrame({
        "lon": pd.to_numeric(df[ds["lon"]], errors="coerce"),
        "lat": pd.to_numeric(df[ds["lat"]], errors="coerce"),
    }).dropna()
    # 한반도 범위 밖 좌표 제거
    out = out[(out.lon.between(124, 132)) & (out.lat.between(33, 39))]
    return out


def nearest_dist(con):
    """읍면동 중심점 → 최근접 시설 거리(m). RTREE 인덱스 + 확장반경.
    가까운 반경에서 해결된 동은 제외하고 남은 동만 다음 반경으로 확장 → 대용량도 빠름."""
    con.execute("CREATE OR REPLACE TEMP TABLE todo AS SELECT adm_cd, cen FROM frame")
    collected = []
    for R in PROX_RADII:
        df = con.execute(f"""
            SELECT t.adm_cd, min(ST_Distance(t.cen, p.pt)) AS d
            FROM todo t JOIN pts p ON ST_DWithin(t.cen, p.pt, {R})
            GROUP BY t.adm_cd""").df()
        if len(df):
            collected.append(df)
            con.register("resolved", df[["adm_cd"]])
            con.execute("DELETE FROM todo WHERE adm_cd IN (SELECT adm_cd FROM resolved)")
            con.unregister("resolved")
        if con.execute("SELECT count(*) FROM todo").fetchone()[0] == 0:
            break
    return pd.concat(collected, ignore_index=True) if collected else pd.DataFrame(columns=["adm_cd", "d"])


def main():
    con = duckdb.connect(DB)
    con.execute("LOAD spatial;")
    # 읍면동 프레임(geom=5179). cen=기하중심(임시)
    con.execute("""CREATE OR REPLACE TEMP TABLE frame AS
        SELECT adm_cd, adm_nm, pop_total, pop_density, geom, ST_Centroid(geom) AS cen FROM dong""")
    ndong = con.execute("SELECT count(*) FROM frame").fetchone()[0]

    # ── 인구가중 중심점: 상가 밀집 위치로 대체(큰 동의 기하중심 산지 왜곡 방지) ──
    #    상가는 정주지에 몰려 있어 인구 중심의 실용적 대용치. 상가 없는 동은 기하중심 유지.
    store_ds = next(d for d in DATASETS if d["key"] == "store")
    spts = read_points(store_ds)
    con.register("spts_raw", spts)
    con.execute("DROP TABLE IF EXISTS spts")
    con.execute("""CREATE TABLE spts AS SELECT
        ST_Transform(ST_Point(lon, lat), 'EPSG:4326', 'EPSG:5179', always_xy:=true) AS pt FROM spts_raw""")
    con.execute("CREATE INDEX spts_rtree ON spts USING RTREE (pt)")
    con.execute("""CREATE OR REPLACE TEMP TABLE popcen AS
        SELECT f.adm_cd, avg(ST_X(p.pt)) px, avg(ST_Y(p.pt)) py
        FROM frame f JOIN spts p ON ST_Contains(f.geom, p.pt) GROUP BY f.adm_cd""")
    con.execute("""CREATE OR REPLACE TEMP TABLE frame AS
        SELECT f.adm_cd, f.adm_nm, f.pop_total, f.pop_density, f.geom,
          CASE WHEN pc.px IS NOT NULL THEN ST_Point(pc.px, pc.py) ELSE ST_Centroid(f.geom) END AS cen
        FROM frame f LEFT JOIN popcen pc USING(adm_cd)""")
    con.execute("DROP TABLE IF EXISTS spts")
    fixed = con.execute("SELECT count(*) FROM popcen").fetchone()[0]
    print(f"인구가중 중심점 적용: {fixed}/{ndong}개 동(상가 기준), 나머지는 기하중심")

    # 인구가중 중심점을 4326 위경도로(통근 근접보정·지도 마커용)
    results = con.execute("""SELECT adm_cd, adm_nm, pop_total, pop_density,
        round(ST_X(ST_Transform(cen,'EPSG:5179','EPSG:4326',always_xy:=true)),5) AS cen_lon,
        round(ST_Y(ST_Transform(cen,'EPSG:5179','EPSG:4326',always_xy:=true)),5) AS cen_lat
        FROM frame ORDER BY adm_cd""").df()
    prox_flags = {}

    for ds in DATASETS:
        pts = read_points(ds)
        con.register("pts_raw", pts)
        # 5179 포인트 테이블 + RTREE 인덱스(근접성 확장반경 검색 가속)
        con.execute("DROP TABLE IF EXISTS pts")
        con.execute("""CREATE TABLE pts AS
            SELECT ST_Transform(ST_Point(lon, lat), 'EPSG:4326', 'EPSG:5179', always_xy:=true) AS pt
            FROM pts_raw""")
        con.execute("CREATE INDEX pts_rtree ON pts USING RTREE (pt)")
        npts = con.execute("SELECT count(*) FROM pts").fetchone()[0]

        # 공간결합 → 읍면동별 개수
        cnt = con.execute("""
            SELECT f.adm_cd, count(p.pt) AS n
            FROM frame f LEFT JOIN pts p ON ST_Contains(f.geom, p.pt)
            GROUP BY f.adm_cd""").df()
        cnt.columns = ["adm_cd", f"{ds['key']}_cnt"]
        results = results.merge(cnt, on="adm_cd", how="left")

        # 밀도(인구 1만명당) — 인구 MIN_POP 미만은 NaN 처리(도농/극소인구 왜곡 방지)
        c, dcol = f"{ds['key']}_cnt", f"{ds['key']}_dens"
        valid_pop = results["pop_total"].where(results["pop_total"] >= MIN_POP)
        results[dcol] = results[c] / valid_pop * 10000

        # 근접성(최근접 m) — RTREE + 확장반경. prox=False면 생략(밀도만)
        if ds.get("prox", True):
            prox = nearest_dist(con)
            prox.columns = ["adm_cd", f"{ds['key']}_nearest_m"]
            results = results.merge(prox, on="adm_cd", how="left")
            prox_flags[ds["key"]] = int(prox[f"{ds['key']}_nearest_m"].notna().sum())
            note = f"근접성 {prox_flags[ds['key']]}/{len(results)}"
        else:
            prox_flags[ds["key"]] = "skip"
            note = "근접성 skip(밀도만)"
        print(f"  [{ds['name']:8s}] 포인트 {npts:>7,} | {note}")

    # ── 도농 코호트 분류(행정동명 접미사): 면=농촌, 읍=도농복합, 그 외=도시 ──
    def cohort(nm):
        s = str(nm)
        return "농촌" if s.endswith("면") else "도농복합" if s.endswith("읍") else "도시"
    results["cohort"] = results["adm_nm"].map(cohort)

    # ── (M6) 인구밀도 기반 도농 3분류 — 행정동명이 실제 도시화도와 어긋나는 경우 보완 ──
    #    통계청 도시지역 관행 임계에 근사: 농촌<500, 도농복합 500~4000, 도시>4000 (명/km²)
    def cohort_by_density(d):
        if d != d:
            return "미상"
        return "농촌" if d < 500 else "도농복합" if d < 4000 else "도시"
    results["cohort_d"] = results["pop_density"].map(cohort_by_density)
    both = results[results["cohort_d"] != "미상"]
    agree = (both["cohort"] == both["cohort_d"]).mean() * 100
    print(f"도농 코호트: 행정동명 vs 인구밀도 일치율 {agree:.1f}% "
          f"(명칭기준 {results['cohort'].value_counts().to_dict()} / "
          f"밀도기준 {results['cohort_d'].value_counts().to_dict()})")

    # ── 지표 신호: 밀도백분위 + 근접성백분위(가까울수록↑) 혼합 ──
    #   근접성이 도농 왜곡을 완충(시골은 1인당 밀도↑여도 최근접거리↑→접근성↓)
    ind_sig = {}  # domain -> list of (signal_col, weight)
    for ds in DATASETS:
        k = ds["key"]
        dens_pct = results[f"{k}_dens"].rank(pct=True) * 100
        parts = [dens_pct]
        near_col = f"{k}_nearest_m"
        if near_col in results:                      # 가까울수록 높은 점수 → -거리로 랭크
            parts.append((-results[near_col]).rank(pct=True) * 100)
        sig = f"{k}_sig"
        results[sig] = pd.concat(parts, axis=1).mean(axis=1)
        if ds.get("neg"):        # 부정지표(교통사고·오염 등): 많을수록/가까울수록 나쁨 → 백분위 반전
            results[sig] = 100 - results[sig]
        ind_sig.setdefault(ds["domain"], []).append((sig, float(ds.get("w", 1.0))))

    def wmean(cols, weights):
        """NaN 무시 가중평균(있는 지표끼리만; 기획서 §4.3 결측 재정규화)."""
        sub = results[cols]
        wsum = (sub.notna() * weights).sum(axis=1)
        return (sub.fillna(0) * weights).sum(axis=1) / wsum.where(wsum > 0)

    # ── 도메인 점수(도메인 내 지표 가중평균) → NLI(도메인 가중합) → 등급 ──
    dom_cols, dom_w = [], []
    for dom, sigs in ind_sig.items():
        col = f"score_{dom}"
        results[col] = wmean([c for c, _ in sigs], [w for _, w in sigs])
        dom_cols.append(col); dom_w.append(DOMAIN_WEIGHTS.get(dom, 1.0))
    results["NLI"] = wmean(dom_cols, dom_w).round(1)
    r = results["NLI"].rank(pct=True)
    results["grade"] = pd.cut(r, [0, .10, .35, .65, .90, 1.0],
                              labels=["D", "C", "B", "A", "S"], include_lowest=True)

    # ── (보조축) 동일 도농 코호트 내 백분위 — 같은 유형끼리 공정 비교(기획서 §4.2) ──
    results["NLI_cohort"] = results.groupby("cohort")["NLI"].rank(pct=True) * 100

    # ── 저장 ──
    con.register("res", results)
    con.execute("CREATE OR REPLACE TABLE nli_scores AS SELECT * FROM res")
    os.makedirs("data/processed", exist_ok=True)
    results.to_csv("data/processed/nli_scores_mvp.csv", index=False, encoding="utf-8-sig")

    # ── 검증 출력 ──
    print(f"\n읍면동 {ndong}개 | 커버 도메인 {list(DOMAINS)} | 근접성 플래그 {prox_flags}")
    show = ["adm_nm", "cohort", "pop_total"] + dom_cols + ["NLI", "grade"]
    print("\n[NLI 상위 8]")
    print(results.sort_values("NLI", ascending=False).head(8)[show].to_string(index=False))
    print("\n[NLI 하위 8]")
    print(results.sort_values("NLI").head(8)[show].to_string(index=False))
    print("\n[도농 편향 점검] 인구 중앙값")
    tsort = results.sort_values("NLI", ascending=False)
    print(f"  상위20 인구중앙값 {int(tsort.head(20).pop_total.median()):>6,} | "
          f"하위20 {int(tsort.tail(20).pop_total.median()):>6,} | 전체 {int(results.pop_total.median()):>6,}")
    print("  (상위·하위·전체가 비슷할수록 도농 편향 없음)")
    print("\n[등급 분포]")
    print(results["grade"].value_counts().sort_index().to_string())
    print("\n저장: nli.duckdb::nli_scores , data/processed/nli_scores_mvp.csv")


if __name__ == "__main__":
    main()
