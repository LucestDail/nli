"""NLI 통계 분석 — 상관·회귀·격차 (대시보드 통계탭 근거 검증용).
실행: ./venv/bin/python stats_analysis.py
"""
import duckdb, numpy as np, pandas as pd

DOMS = [f"score_D{i}" for i in range(1, 9)]
NM = {"score_D1": "의료", "score_D2": "교육", "score_D3": "생활편의", "score_D4": "문화여가",
      "score_D5": "교통", "score_D6": "안전", "score_D7": "환경", "score_D8": "복지"}


def ols(X, y):
    """단순 OLS(절편 포함) → 계수, R²."""
    m = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    X, y = X[m], y[m]
    A = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = A @ beta
    ss_res = ((y - yhat) ** 2).sum(); ss_tot = ((y - y.mean()) ** 2).sum()
    return beta, 1 - ss_res / ss_tot


def main():
    con = duckdb.connect("data/processed/nli.duckdb")
    df = con.execute("""SELECT s.*, d.ratio_infant, d.ratio_elderly, d.pop_density
                        FROM nli_scores s JOIN dong d USING(adm_cd) WHERE s.pop_total>0""").df()
    print(f"분석 대상 {len(df):,}개 읍면동\n")

    # 1) 도메인 간 상관
    print("=== 도메인 상관계수 (주요) ===")
    C = df[DOMS].corr()
    pairs = [(NM[a], NM[b], C.loc[a, b]) for i, a in enumerate(DOMS) for b in DOMS[i+1:]]
    for a, b, r in sorted(pairs, key=lambda x: -abs(x[2]))[:6]:
        print(f"  {a}↔{b}: {r:+.2f}")

    # 2) 연령구조·인구와 도메인
    print("\n=== 고령비중 ↔ 각 도메인 상관 (음수=고령많을수록 열악) ===")
    for d in DOMS:
        r = df["ratio_elderly"].corr(df[d])
        print(f"  {NM[d]}: {r:+.2f}", end="   ")
    print()

    # 3) 회귀: 의료 접근성(D1) ~ 고령비중 + 인구밀도
    print("\n=== 회귀: 의료점수 ~ 고령비중 + log인구밀도 ===")
    X = np.column_stack([df["ratio_elderly"].values, np.log1p(df["pop_density"].values)])
    beta, r2 = ols(X, df["score_D1"].values)
    print(f"  의료 = {beta[0]:.1f} + ({beta[1]:.1f})·고령비중 + ({beta[2]:.1f})·log밀도  |  R²={r2:.2f}")

    # 4) 회귀: 복지(D8) ~ 고령비중 (고령지역에 복지가 따라가나)
    beta2, r2b = ols(df[["ratio_elderly"]].values, df["score_D8"].values)
    print(f"  복지 = {beta2[0]:.1f} + ({beta2[1]:.1f})·고령비중  |  R²={r2b:.2f}")

    # 5) 도농 격차
    print("\n=== 도농(코호트) 도메인 평균 ===")
    g = df.groupby("cohort")[DOMS].mean().rename(columns=NM)
    print(g.round(1).to_string())

    # 6) 시도 격차 (평균 NLI 상하위)
    df["sido"] = df["adm_nm"]  # placeholder; sido는 대시보드에서 full_nm로. 여기선 생략
    print("\n분석 완료. (대시보드 통계탭에서 상관 히트맵·산점도·도농/시도 막대로 시각화)")


if __name__ == "__main__":
    main()
