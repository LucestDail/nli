"""
NLI 지오 프레임 빌더 (Phase 0)
- 입력: data/processed/sgis/ (SGIS 행정구역 통계 및 경계 ZIP 압축 해제본)
- 출력: data/processed/nli.duckdb  (테이블: dong=경계+인구총괄, stat_long=전체 통계 long)
        data/processed/nli_geoframe.parquet (경계+인구 wide, geom=WKB)
- 분석 단위: 행정동(ADM_CD 8자리) 3,559개
실행: ./venv/bin/python build_geoframe.py
"""
import duckdb, pandas as pd, glob, os

BASE = "data/processed/sgis"

# SGIS 총괄 통계 코드 → 지오프레임 컬럼명
CORE = {
    'to_in_001': 'pop_total', 'to_in_007': 'pop_male', 'to_in_008': 'pop_female',
    'to_in_002': 'age_mean', 'to_in_003': 'pop_density', 'to_in_004': 'aging_index',
    'to_ga_001': 'hh_total', 'to_ho_001': 'house_total',
    'to_fa_010': 'biz_total', 'to_em_020': 'emp_total',
}


def load_stats():
    frames = []
    for f in glob.glob(BASE + "/1. 통계/**/*.csv", recursive=True):
        d = pd.read_csv(f, encoding='cp949', dtype={'행정구역코드': str, '통계항목': str})
        frames.append(d[['기준연도', '행정구역코드', '통계항목', '통계값']])
    stat = pd.concat(frames, ignore_index=True)
    stat.columns = ['year', 'adm_cd', 'code', 'val']
    return stat


def main():
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")

    stat = load_stats()
    dong = stat[stat['adm_cd'].str.len() == 8].copy()          # 8자리 = 행정동
    core = dong[dong['code'].isin(CORE)].copy()
    core['col'] = core['code'].map(CORE)
    core['val'] = pd.to_numeric(core['val'], errors='coerce')
    wide = core.pivot_table(index='adm_cd', columns='col', values='val', aggfunc='first').reset_index()

    # 연령구조 파생(페르소나용): in_age_001~021 = 5세 버킷(0-4 … 100+), 022=미상 제외
    age = dong[dong['code'].between('in_age_001', 'in_age_021')].copy()
    age['val'] = pd.to_numeric(age['val'], errors='coerce')
    an = age.pivot_table(index='adm_cd', columns='code', values='val', aggfunc='first').fillna(0)
    def s(cols): return an[[c for c in cols if c in an]].sum(axis=1)
    denom = an.sum(axis=1).replace(0, pd.NA)
    ar = pd.DataFrame({
        'ratio_infant':  s([f'in_age_00{i}' for i in [1]]) / denom,                       # 영유아 0-4
        'ratio_youth':   s([f'in_age_00{i}' for i in [1, 2, 3]]) / denom,                  # 유소년 0-14
        'ratio_working': s([f'in_age_{i:03d}' for i in range(4, 14)]) / denom,             # 청장년 15-64
        'ratio_elderly': s([f'in_age_{i:03d}' for i in range(14, 22)]) / denom,            # 고령 65+
    }).reset_index()
    wide = wide.merge(ar, on='adm_cd', how='left')
    con.register('pop', wide)

    shp = BASE + "/2. 경계/3. 2025년 2분기 기준 행정동 경계/bnd_dong_00_2025_2Q.shp"
    con.execute(f"CREATE TABLE bnd AS SELECT ADM_CD AS adm_cd, ADM_NM AS adm_nm, geom FROM ST_Read('{shp}')")
    con.execute("""CREATE TABLE dong AS
        SELECT b.adm_cd, b.adm_nm,
               p.pop_total, p.pop_male, p.pop_female, p.age_mean, p.pop_density, p.aging_index,
               p.hh_total, p.house_total, p.biz_total, p.emp_total,
               p.ratio_infant, p.ratio_youth, p.ratio_working, p.ratio_elderly, b.geom
        FROM bnd b LEFT JOIN pop p USING(adm_cd)""")

    # 검증
    n = con.execute("SELECT count(*) FROM dong").fetchone()[0]
    nomatch = con.execute("SELECT count(*) FROM dong WHERE pop_total IS NULL").fetchone()[0]
    poptot = con.execute("SELECT sum(pop_total) FROM dong").fetchone()[0]
    print(f"행정동 {n}개 | 인구 미매칭 {nomatch}건 | 전국 총인구 {int(poptot):,}")

    # 저장
    con.execute("COPY dong TO 'data/processed/nli_geoframe.parquet' (FORMAT parquet)")
    con.execute("ATTACH 'data/processed/nli.duckdb' AS nli;")
    con.execute("CREATE OR REPLACE TABLE nli.dong AS SELECT * FROM dong;")
    con.register('stat_all', stat)
    con.execute("CREATE OR REPLACE TABLE nli.stat_long AS SELECT * FROM stat_all;")
    con.execute("DETACH nli;")
    print("저장: data/processed/nli.duckdb (dong, stat_long), nli_geoframe.parquet")


if __name__ == "__main__":
    main()
