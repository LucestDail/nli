"""
NLI 판정 로직 (기획서 §6) — 현재 7도메인 스코어 기반
- 사각지대(blind spot): 인구 많은데 특정 도메인 점수 최하위 → 다수 주민이 인프라 소외
- 결핍(deficiency): 인구 있는 동인데 필수시설이 반경 R 내 0개
- 균형성: 도메인 점수 분산 → 올라운드형 vs 특화형
입력: data/processed/nli.duckdb::nli_scores
출력: 콘솔 리포트 + data/processed/nli_flags.csv
"""
import duckdb, pandas as pd

DOM_NAMES = {"D1": "의료", "D2": "교육", "D3": "생활편의", "D4": "문화여가",
             "D5": "교통", "D6": "안전", "D7": "환경", "D8": "복지"}
DOM_COLS = [f"score_{d}" for d in DOM_NAMES]

# 결핍 판정: 필수시설별 (개수컬럼, 반경m). 동 안에 0개 AND 최근접>R 이면 결핍.
#   ※ 개수 0개 조건 필수 — 큰 동(예 제주 노형동 45km²)은 기하중심이 산지라
#     최근접거리가 왜곡됨(시설 47개인데 4km로 나옴). 인구가중중심점 도입 전까지 개수로 방어.
ESSENTIAL = {"pharmacy": ("약국", 3000), "clinic": ("의료기관", 3000),
             "school": ("학교", 2000), "park": ("공원", 2000),
             "bus": ("버스정류장", 1000)}
BLINDSPOT_POP = 10000      # 사각지대: 이 이상 인구
BLINDSPOT_PCT = 20         # 도메인 점수 이 이하(하위 20%)
DEFICIENCY_POP = 500       # 결핍: 이 이상 인구인데 필수시설 없음


def main():
    con = duckdb.connect("data/processed/nli.duckdb")
    full = con.execute("SELECT * FROM nli_scores").df()   # 정본(3559 전체) — 저장은 이걸로
    # 균형성/프로필은 전체에 부여(지도·정본 보존). 인구 0 동은 NaN.
    full["balance_std"] = full[DOM_COLS].std(axis=1)
    full["profile"] = pd.cut(full["balance_std"], [0, 12, 22, 100],
                             labels=["올라운드", "보통", "특화/편중"], include_lowest=True)
    df = full[full["pop_total"] > 0].copy()   # 사각지대·결핍·리포트 분석은 유인구 동만

    # ── 사각지대: 인구 많은데 특정 도메인 최하위 ──
    blind = []
    for d, nm in DOM_NAMES.items():
        sc = f"score_{d}"
        hit = df[(df["pop_total"] >= BLINDSPOT_POP) & (df[sc] <= BLINDSPOT_PCT)]
        for _, r in hit.iterrows():
            blind.append({"adm_nm": r["adm_nm"], "pop": int(r["pop_total"]),
                          "도메인": nm, "점수": round(r[sc], 1)})
    blind = pd.DataFrame(blind).sort_values("pop", ascending=False) if blind else pd.DataFrame()

    # ── 결핍: 인구 있는데 필수시설 반경 내 0개 ──
    defi = []
    pop_ok = df[df["pop_total"] >= DEFICIENCY_POP]
    for key, (nm, R) in ESSENTIAL.items():
        cnt_col, near_col = f"{key}_cnt", f"{key}_nearest_m"
        # 동 안에 0개 AND 최근접 시설도 R 밖 → 진짜 결핍
        hit = pop_ok[(pop_ok[cnt_col] == 0) & (pop_ok[near_col] > R)]
        for _, r in hit.iterrows():
            defi.append({"adm_nm": r["adm_nm"], "cohort": r["cohort"], "pop": int(r["pop_total"]),
                         "결핍시설": nm, "최근접_m": int(r[near_col]), "기준_m": R})
    defi = pd.DataFrame(defi).sort_values("pop", ascending=False) if defi else pd.DataFrame()

    # ── 리포트 ──
    print(f"분석 대상: 인구>0 행정동 {len(df):,}개\n")
    print("=" * 60)
    print(f"■ 사각지대 (인구 {BLINDSPOT_POP:,}+ 인데 도메인 점수 하위 {BLINDSPOT_PCT}%)")
    print(f"  총 {len(blind)}건 (동네×도메인)")
    if len(blind):
        print("  도메인별 건수:", blind["도메인"].value_counts().to_dict())
        print("\n  [인구 많은 사각지대 TOP 10]")
        print(blind.head(10).to_string(index=False))
    print("\n" + "=" * 60)
    print(f"■ 결핍 (인구 {DEFICIENCY_POP}+ 인데 필수시설 반경 내 0개)")
    print(f"  총 {len(defi)}건")
    if len(defi):
        print("  시설별 건수:", defi["결핍시설"].value_counts().to_dict())
        print("  코호트별:", defi["cohort"].value_counts().to_dict())
        print("\n  [인구 많은 결핍 TOP 10 — 가장 시급]")
        print(defi.head(10).to_string(index=False))
    print("\n" + "=" * 60)
    print("■ 동네 프로필 (도메인 균형성)")
    print(df["profile"].value_counts().sort_index().to_string())

    # ── 저장 ──
    if len(blind): blind.to_csv("data/processed/nli_blindspots.csv", index=False, encoding="utf-8-sig")
    if len(defi): defi.to_csv("data/processed/nli_deficiencies.csv", index=False, encoding="utf-8-sig")
    con.register("res", full)
    con.execute("CREATE OR REPLACE TABLE nli_scores AS SELECT * FROM res")  # 전체 3559 + balance_std/profile
    write_report(df, blind, defi)
    print("\n저장: nli_blindspots.csv, nli_deficiencies.csv, nli_report.md, nli_scores(+balance_std,profile)")


def write_report(df, blind, defi):
    """정책용 사각지대·결핍 리포트(마크다운) 자동생성 — 기획서 §6 B2G/데이터저널리즘 산출물."""
    def md_table(rows, cols):
        h = "| " + " | ".join(cols) + " |\n| " + " | ".join(["---"] * len(cols)) + " |\n"
        return h + "".join("| " + " | ".join(str(r[c]) for c in cols) + " |\n" for r in rows)
    L = []
    L.append("# 동네살기지수(NLI) — 사각지대·결핍 리포트\n")
    L.append(f"> 자동생성. 분석 대상: 인구>0 읍면동 {len(df):,}개 · 8개 도메인\n")
    gd = df["grade"].value_counts()
    L.append(f"- 등급 분포: " + " · ".join(f"{g} {int(gd.get(g,0))}" for g in ["S","A","B","C","D"]))
    L.append(f"- 사각지대(동네×도메인): **{len(blind)}건** · 결핍(필수시설 부재): **{len(defi)}건**\n")

    L.append("## 🔴 사각지대 — 인구 많은데 특정 도메인 최하위 (정책 우선순위)\n")
    if len(blind):
        L.append("도메인별 건수: " + ", ".join(f"{k} {v}" for k, v in blind["도메인"].value_counts().items()) + "\n")
        top = blind.sort_values("pop", ascending=False).head(20)
        L.append(md_table([{"지역": r["adm_nm"], "인구": f'{r["pop"]:,}', "도메인": r["도메인"], "점수": r["점수"]}
                           for _, r in top.iterrows()], ["지역", "인구", "도메인", "점수"]))

    L.append("\n## 🟠 결핍 — 인구 있는데 필수시설 0개 (가장 시급)\n")
    if len(defi):
        L.append("시설별: " + ", ".join(f"{k} {v}" for k, v in defi["결핍시설"].value_counts().items()))
        L.append("코호트별: " + ", ".join(f"{k} {v}" for k, v in defi["cohort"].value_counts().items()) + "\n")
        top = defi.sort_values("pop", ascending=False).head(20)
        L.append(md_table([{"지역": r["adm_nm"], "유형": r["cohort"], "인구": f'{r["pop"]:,}',
                            "결핍시설": r["결핍시설"], "최근접": f'{r["최근접_m"]:,}m'} for _, r in top.iterrows()],
                          ["지역", "유형", "인구", "결핍시설", "최근접"]))

    L.append("\n## 🧭 동네 프로필 (도메인 균형성)\n")
    pc = df["profile"].value_counts()
    L.append(md_table([{"유형": k, "동네 수": int(pc.get(k, 0))} for k in ["올라운드", "보통", "특화/편중"]],
                      ["유형", "동네 수"]))
    L.append("\n---\n*점수는 전국 상대평가(백분위)로 참고용. D8 복지는 지오코딩 85% 커버.*\n")
    open("data/processed/nli_report.md", "w", encoding="utf-8").write("\n".join(L))


if __name__ == "__main__":
    main()
