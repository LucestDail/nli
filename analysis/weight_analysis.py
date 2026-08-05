"""
도메인 가중치 정교화(M7) — 객관 가중법 산출 · 근거 재현 스크립트
방법:
  · 엔트로피 가중법: 각 도메인 점수의 정보 발산도(1-엔트로피)로 가중. 지역 간 편차가 큰(정보량 많은) 도메인에 큰 가중.
  · CRITIC: 표준편차 × (1-상관)합 — 정보량에 더해 도메인 간 중복(상관)을 보정.
한계: 두 방법 모두 '통계적 분산'을 반영할 뿐 '살기좋음에 대한 중요도'가 아니다.
      따라서 NLI 기본 가중치는 균등(OECD 복합지표 관행)을 유지하고, 이 값들은 앱의 선택 프리셋으로만 제공한다.
출력: 균등=1.0 기준으로 정규화한(분수×8) 8원소 배열 → build_web.py PRESETS에 반영.
실행: ./venv/bin/python weight_analysis.py
"""
import duckdb, numpy as np

DK = [f"score_D{i}" for i in range(1, 10)]
NM = ['의료', '교육', '생활편의', '문화여가', '교통', '안전', '환경', '복지', '반려']


def main():
    con = duckdb.connect("data/processed/nli.duckdb")
    df = con.execute(f"SELECT {','.join(DK)} FROM nli_scores").df()
    M = df.dropna().values.astype(float)          # 8도메인 결측 없는 동만
    n, m = M.shape

    # 엔트로피 가중법
    P = M / M.sum(axis=0)
    P = np.where(P <= 0, 1e-12, P)
    e = -(1 / np.log(n)) * (P * np.log(P)).sum(axis=0)
    w_ent = (1 - e) / (1 - e).sum()

    # CRITIC
    sd = M.std(axis=0, ddof=1)
    conflict = (1 - np.corrcoef(M, rowvar=False)).sum(axis=1)
    c = sd * conflict
    w_crit = c / c.sum()

    print(f"표본 {n}개 동 · {m}개 도메인\n")
    print(f"{'도메인':<8}{'엔트로피%':>10}{'CRITIC%':>10}")
    for i, nm in enumerate(NM):
        print(f"{nm:<8}{w_ent[i]*100:>9.1f}{w_crit[i]*100:>10.1f}")

    # 균등=1.0 기준(분수×도메인수) → 앱 프리셋 스케일
    print("\n# build_web.py PRESETS 반영값 (균등=1.0 기준, 분수×8)")
    print(" '정보량(엔트로피)':[" + ",".join(f"{v*m:.2f}" for v in w_ent) + "],")
    print(" 'CRITIC(중복보정)':[" + ",".join(f"{v*m:.2f}" for v in w_crit) + "],")


if __name__ == "__main__":
    main()
