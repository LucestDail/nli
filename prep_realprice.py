"""
아파트 실거래가 → 행정동 ㎡당가 (살기지수 × 가격)
입력: data/raw/apt_trades.csv, data/raw/lawd_cd.csv, nli.duckdb(dong)+SGIS 경계
처리: ㎡당가 → (시군구,법정동) median → 법정동명↔행정동명 정규화 매칭(+시군구 폴백) → 행정동 price_m2
출력: data/processed/dong_price.csv (adm_cd, price_m2, price_src)  ← build_geoframe에서 조인
실행: ./venv/bin/python prep_realprice.py

⚠️ SGIS 코드≠법정동코드 → 시군구/시도는 '이름'으로 매칭(SGIS SIGUNGU_NM == lawd sgg_short).
"""
import pandas as pd, duckdb, re

SGIS = "data/processed/sgis/2. 경계"


def norm(nm):
    """법정동/행정동명 → 공통 기준명. 역삼1동·역삼동→역삼, 평창동→평창. 다법정동 행정동은 매칭 실패→시군구폴백."""
    s = re.sub(r'\.?\d+동?$', '', str(nm))   # 끝의 숫자(+동)
    s = re.sub(r'\d+가$', '', s)             # N가
    return s.rstrip('동가·').strip()


def main():
    tr = pd.read_csv("data/raw/apt_trades.csv", dtype=str)
    tr["amt"] = pd.to_numeric(tr["거래금액"].str.replace(",", ""), errors="coerce")   # 만원
    tr["ar"] = pd.to_numeric(tr["전용면적"], errors="coerce")
    tr = tr[(tr.amt > 0) & (tr.ar > 0)].copy()
    tr["m2"] = tr.amt / tr.ar
    tr = tr[(tr.m2 > 5) & (tr.m2 < 5000)]                                            # 이상치 컷
    tr["sgg"] = tr["지역코드"].str[:5]

    lawd = pd.read_csv("data/raw/lawd_cd.csv", dtype=str)
    l2 = {r.lawd_cd: (r.sido, r.sgg_short) for r in lawd.itertuples()}
    tr["sido"] = tr["sgg"].map(lambda c: l2.get(c, ("", ""))[0])
    tr["sggnm"] = tr["sgg"].map(lambda c: l2.get(c, ("", ""))[1])
    tr["umd_base"] = tr["법정동"].map(norm)

    # (시도,시군구,법정동기준) median + (시도,시군구) median
    umd = tr.groupby(["sido", "sggnm", "umd_base"])["m2"].median()
    sgg = tr.groupby(["sido", "sggnm"])["m2"].median()

    # 행정동 → 시도/시군구명 (SGIS 경계 조인)
    con = duckdb.connect("data/processed/nli.duckdb"); con.execute("LOAD spatial;")
    con.execute(f"CREATE OR REPLACE TEMP TABLE sido AS SELECT SIDO_CD,SIDO_NM FROM ST_Read('{SGIS}/1. 2025년 2분기 기준 시도 경계/bnd_sido_00_2025_2Q.shp')")
    con.execute(f"CREATE OR REPLACE TEMP TABLE sg AS SELECT SIGUNGU_CD,SIGUNGU_NM FROM ST_Read('{SGIS}/2. 2025년 2분기 기준 시군구 경계/bnd_sigungu_00_2025_2Q.shp')")
    dong = con.execute("""SELECT d.adm_cd, d.adm_nm, sd.SIDO_NM AS sido, sg.SIGUNGU_NM AS sggnm
        FROM dong d LEFT JOIN sido sd ON substr(d.adm_cd,1,2)=sd.SIDO_CD
                    LEFT JOIN sg ON substr(d.adm_cd,1,5)=sg.SIGUNGU_CD""").df()
    dong["base"] = dong["adm_nm"].map(norm)

    def price(r):
        k = (r.sido, r.sggnm, r.base)
        if k in umd.index:
            return umd[k], "법정동"
        if (r.sido, r.sggnm) in sgg.index:
            return sgg[(r.sido, r.sggnm)], "시군구"
        return None, "없음"
    out = dong.apply(lambda r: pd.Series(price(r), index=["price_m2", "price_src"]), axis=1)
    dong = pd.concat([dong[["adm_cd", "adm_nm"]], out], axis=1)
    dong["price_m2"] = pd.to_numeric(dong["price_m2"], errors="coerce").round(1)
    dong[["adm_cd", "price_m2", "price_src"]].to_csv("data/processed/dong_price.csv", index=False, encoding="utf-8-sig")

    n = len(dong); cov = dong["price_m2"].notna().sum()
    src = dong["price_src"].value_counts().to_dict()
    print(f"거래 {len(tr):,}건 → 행정동 {n}개 중 가격부여 {cov}({cov/n*100:.0f}%) · 출처 {src}")
    print("행정동 ㎡당가 상위5(만원/㎡):")
    for r in dong.sort_values("price_m2", ascending=False).head(5).itertuples():
        print(f"  {r.adm_nm} {r.price_m2:.0f} (평당 {r.price_m2*3.3058:.0f}) [{r.price_src}]")
    print("저장: data/processed/dong_price.csv")


if __name__ == "__main__":
    main()
