"""D8 사회복지시설 — 시군구 단위 집계 (좌표 없어 시군구 해상도로 D8 점등).
보건복지부_사회복지시설 정보(주소보유 36K)의 시설주소에서 시도·시군구를 파싱,
SGIS adm_code.xlsx (시도명·시군구명→코드) 로 매핑 → 시군구별 시설수.
출력: data/processed/welfare_sgg.csv  (sgg5=SGIS 시군구코드5자리, welfare_cnt)
"""
import pandas as pd, os

SRC = os.path.expanduser("~/Downloads/보건복지부_사회복지시설 정보_20260318.csv")
ADM = "data/processed/sgis/3. 코드집/1. 행정구역 코드(adm_code).xlsx"


def build_map():
    a = pd.read_excel(ADM, header=1, dtype=str)
    a.columns = ["sido_cd", "sido_nm", "sgg_cd", "sgg_nm", "emd_cd", "emd_nm"]
    a = a.dropna(subset=["sido_nm", "sgg_nm"]).drop_duplicates(["sido_nm", "sgg_nm"])
    a["sgg5"] = a["sido_cd"].str.zfill(2) + a["sgg_cd"].str.zfill(3)
    # 시도명 → [(시군구명, sgg5)] (긴 이름 우선 매칭)
    m = {}
    for _, r in a.iterrows():
        m.setdefault(r["sido_nm"], []).append((r["sgg_nm"], r["sgg5"]))
    for k in m:
        m[k].sort(key=lambda x: -len(x[0]))
    return m


def main():
    m = build_map()
    df = pd.read_csv(SRC, encoding="cp949", dtype=str)
    cnt, miss, matched = {}, [], 0
    for addr in df["시설주소"].fillna(""):
        addr = addr.strip()
        sido = addr.split(" ")[0] if addr else ""
        cands = m.get(sido) or []
        hit = next((code for nm, code in cands if nm in addr), None)
        if not hit and sido == "세종특별자치시":
            hit = "29010"  # 세종: adm_code에 시군구 없음 → SGIS 세종시 코드로 매핑
        if hit:
            cnt[hit] = cnt.get(hit, 0) + 1; matched += 1
        else:
            miss.append(addr[:25])
    out = pd.DataFrame([(k, v) for k, v in cnt.items()], columns=["sgg5", "welfare_cnt"])
    out.to_csv("data/processed/welfare_sgg.csv", index=False, encoding="utf-8-sig")
    print(f"총 {len(df):,}건 · 매칭 {matched:,} · 미매칭 {len(miss):,} · 시군구 {len(cnt)}개")
    print("합계 검증(전국 사회복지시설):", out.welfare_cnt.sum())
    from collections import Counter
    print("미매칭 상위:", Counter(miss).most_common(5))


if __name__ == "__main__":
    main()
