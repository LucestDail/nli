"""추천·진단 도메인 로직 — 앱(build_web) JS와 동일 규칙을 서버로 이관."""
import math
from . import snapshot

DOMS = [f"D{i}" for i in range(1, 10)]
DOM_NAMES = {"D1": "의료·건강", "D2": "교육·보육", "D3": "생활편의·상업", "D4": "문화·여가·체육",
             "D5": "교통·이동", "D6": "안전", "D7": "환경·기후", "D8": "복지·돌봄", "D9": "반려·동물"}
# 가구유형 → 페르소나 가중치(build_web PRESETS와 동일)
PRESETS = {
    "일반": [1, 1, 1, 1, 1, 1, 1, 1, 1],
    "육아": [1.4, 2, 1, 1.3, 1, 1.6, 1, 1.2, 1],
    "1인": [1, 1, 2, 1.5, 1.5, 1, 1, 1, 1.5],
    "고령": [2, 1, 1.2, 1.2, 1.4, 1.2, 1.3, 2, 1.2],
    "반려": [1, 1, 1, 1.3, 1, 1.2, 1.3, 1, 2.5],
}
PYEONG = 3.3058  # ㎡ → 평


def _hav(a, b, c, d):
    R = 6371.0088; r = math.pi / 180
    dla = (c - a) * r; dlo = (d - b) * r
    s = math.sin(dla / 2) ** 2 + math.cos(a * r) * math.cos(c * r) * math.sin(dlo / 2) ** 2
    return 2 * R * math.asin(math.sqrt(s))


def _nliw(row, w):
    s = t = 0.0
    for i, d in enumerate(DOMS):
        v = row.get("score_" + d)
        if v is not None and v == v:  # not NaN
            s += w[i] * v; t += w[i]
    return round(s / t, 1) if t else None


def _rows(cols):
    df = snapshot.q(f"SELECT {cols} FROM dong WHERE pop_total > 0")
    return df.to_dict("records")


def recommend(house="일반", budget=None, base_adm=None, km=10, limit=10):
    w = PRESETS.get(house, PRESETS["일반"])
    cols = "adm_cd, adm_nm, full_nm, NLI, grade, price, clat, clon, pop_total, " + ", ".join("score_" + d for d in DOMS)
    rows = _rows(cols)
    base = None
    if base_adm:
        b = snapshot.q("SELECT clat, clon FROM dong WHERE adm_nm=? OR adm_cd=? LIMIT 1", [base_adm, base_adm])
        if len(b):
            base = (float(b["clat"][0]), float(b["clon"][0]))
    out = []
    for r in rows:
        if budget and not (r.get("price") == r.get("price") and r["price"] is not None and r["price"] * PYEONG <= budget):
            continue
        if base and r.get("clat") == r.get("clat") and r["clat"] is not None:
            dkm = _hav(base[0], base[1], r["clat"], r["clon"])
            if dkm > km:
                continue
            r["_km"] = round(dkm, 1)
        elif base:
            continue
        sc = _nliw(r, w)
        if sc is None:
            continue
        top = sorted(((r["score_" + d], DOM_NAMES[d]) for d in DOMS if r.get("score_" + d) == r.get("score_" + d)),
                     reverse=True)[:2]
        out.append({"adm_cd": r["adm_cd"], "full_nm": r["full_nm"], "score": sc,
                    "grade": r.get("grade"),
                    "price_pyeong": round(r["price"] * PYEONG) if (r.get("price") == r.get("price") and r["price"] is not None) else None,
                    "km": r.get("_km"), "top_domains": [t[1] for t in top]})
    out.sort(key=lambda x: -x["score"])
    return {"house": house, "weights": dict(zip(DOMS, w)),
            "conditions": {"budget_pyeong": budget, "base": base_adm, "km": km if base else None},
            "count": len(out), "items": out[:limit]}


def _sgg_frame():
    cols = "full_nm, adm_nm, pop_total, " + ", ".join("score_" + d for d in DOMS)
    rows = _rows(cols)
    for r in rows:
        p = (r.get("full_nm") or "").split()
        r["_sido"] = p[0] if len(p) >= 2 else ""
        r["_sgg"] = p[1] if len(p) >= 2 else ""
    return rows


def _nat_avg(rows):
    nat = {}
    for d in DOMS:
        vs = [r["score_" + d] for r in rows if r.get("score_" + d) == r.get("score_" + d)]
        nat[d] = sum(vs) / len(vs) if vs else 0
    return nat


def diag_list():
    rows = _sgg_frame()
    nat = _nat_avg(rows)
    g = {}
    for r in rows:
        k = (r["_sido"], r["_sgg"])
        if not k[1]:
            continue
        g.setdefault(k, []).append(r)
    res = []
    for (sido, sgg), L in g.items():
        nlis = [_nliw(r, [1] * 9) for r in L]
        nlis = [x for x in nlis if x is not None]
        blind = sum(1 for r in L for d in DOMS
                    if (r.get("pop_total") or 0) >= 10000 and r.get("score_" + d) == r.get("score_" + d) and r["score_" + d] <= 20)
        res.append({"sido": sido, "sgg": sgg, "avg_nli": round(sum(nlis) / len(nlis), 1) if nlis else 0,
                    "dongs": len(L), "blindspots": blind})
    res.sort(key=lambda x: x["avg_nli"])
    for i, x in enumerate(res, 1):
        x["rank"] = i
    return {"total": len(res), "items": res}


def diag(sgg):
    rows = _sgg_frame()
    nat = _nat_avg(rows)
    L = [r for r in rows if r["_sgg"] == sgg]
    if not L:
        return None
    sido = L[0]["_sido"]
    dom = {}
    for d in DOMS:
        vs = [r["score_" + d] for r in L if r.get("score_" + d) == r.get("score_" + d)]
        dom[d] = sum(vs) / len(vs) if vs else 0
    dev = sorted(((d, round(dom[d] - nat[d])) for d in DOMS), key=lambda x: x[1])
    nlis = [x for x in (_nliw(r, [1] * 9) for r in L) if x is not None]
    blind = []
    for r in L:
        for d in DOMS:
            v = r.get("score_" + d)
            if (r.get("pop_total") or 0) >= 10000 and v == v and v <= 20:
                blind.append({"adm_nm": r["adm_nm"], "pop": int(r["pop_total"]),
                              "domain": DOM_NAMES[d], "score": round(v)})
    blind.sort(key=lambda x: -x["pop"])
    # 전국 순위
    dl = diag_list()["items"]
    rank = next((x["rank"] for x in dl if x["sgg"] == sgg and x["sido"] == sido), None)
    return {"sido": sido, "sgg": sgg,
            "avg_nli": round(sum(nlis) / len(nlis), 1) if nlis else 0,
            "rank": rank, "total": len(dl), "dongs": len(L),
            "weak": [{"domain": d, "name": DOM_NAMES[d], "dev": v} for d, v in dev[:3]],
            "strong": [{"domain": d, "name": DOM_NAMES[d], "dev": v} for d, v in dev[-2:][::-1]],
            "blindspots_count": len(blind), "blindspots": blind[:20]}
