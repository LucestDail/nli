"""
도메인 중요도 가중치 — AHP(Analytic Hierarchy Process) 설계 (M7 잔여)
쌍대비교 행렬 → 고유벡터(기하평균법) 가중치 + 일관성비율(CR) 검증.

⚠️ 중요도 판단은 '가치'라 임의로 정하지 않는다. 아래 TIERS는 **제안 기본안**이며,
   사용자가 계층/강도를 조정해 확정한다. (분산기반인 엔트로피/CRITIC과 달리 '의미 기반')

기본안(3계층 · 살기좋은 동네 관점):
  · 필수·안심: 의료(D1)·안전(D6)
  · 일상 필수: 교육(D2)·교통(D5)·복지(D8)
  · 편의·쾌적: 생활편의(D3)·문화여가(D4)·환경(D7)
강도(Saaty): 상위계층/하위계층 = 필수>일상 3배, 일상>편의 3배, 필수>편의 5배. 동일계층 = 1.
실행: ./venv/bin/python ahp_weights.py
"""
import numpy as np

DOMS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
NM = {"D1": "의료", "D2": "교육", "D3": "생활편의", "D4": "문화여가",
      "D5": "교통", "D6": "안전", "D7": "환경", "D8": "복지", "D9": "반려"}

# 각 도메인의 계층(1=필수·안심, 2=일상 필수, 3=편의·쾌적)
TIERS = {"D1": 1, "D6": 1, "D2": 2, "D5": 2, "D8": 2, "D3": 3, "D4": 3, "D7": 3, "D9": 3}
# 계층 우위 강도 (상위,하위) → Saaty 값
INTENSITY = {(1, 2): 3, (2, 3): 3, (1, 3): 5}
# 무작위 지수(Saaty RI), n=8
RI = {1: 0, 2: 0, 3: .58, 4: .90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}


def pairwise():
    n = len(DOMS)
    A = np.ones((n, n))
    for i in range(n):
        for j in range(n):
            ti, tj = TIERS[DOMS[i]], TIERS[DOMS[j]]
            if ti < tj:
                A[i, j] = INTENSITY[(ti, tj)]
            elif ti > tj:
                A[i, j] = 1 / INTENSITY[(tj, ti)]
    return A


def ahp(A):
    n = A.shape[0]
    w = np.prod(A, axis=1) ** (1 / n)      # 기하평균법 우선순위 벡터
    w = w / w.sum()
    lam = (A @ w / w).mean()               # 최대 고유값 근사
    CI = (lam - n) / (n - 1)
    CR = CI / RI[n]
    return w, CR


def main():
    A = pairwise()
    w, CR = ahp(A)
    order = np.argsort(-w)
    print("AHP 도메인 중요도 가중치 (제안 기본안)\n")
    print(f"{'도메인':<8}{'계층':>4}{'가중치':>10}")
    for i in order:
        tier = {1: "필수", 2: "일상", 3: "편의"}[TIERS[DOMS[i]]]
        print(f"{NM[DOMS[i]]:<8}{tier:>4}{w[i]*100:>9.1f}%")
    print(f"\n일관성비율 CR = {CR:.3f}  ({'✅ 일관성 있음(<0.1)' if CR < 0.1 else '❌ 재조정 필요'})")
    print("\n# build_web.py PRESETS 반영값 (균등=1.0 기준, ×8)")
    print(" '중요도(AHP)':[" + ",".join(f"{w[DOMS.index(d)]*8:.2f}" for d in DOMS) + "],")


if __name__ == "__main__":
    main()
