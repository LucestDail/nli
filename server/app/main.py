"""NLI API — FastAPI. 스냅샷(geojson) 읽기전용 서빙 + 추천·진단.
OpenAPI 문서: /docs · /openapi.json. daero 패턴(CORS·레이트리밋·헬스·에러규격·env).
"""
import time, os, math, threading
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config, snapshot, logic

app = FastAPI(title="NLI API — 동네살기지수", version=config.VERSION,
              description="전국 읍면동 9도메인 32지표 생활입지 인텔리전스. 공공데이터 기반·참고용(전국 상대 백분위).")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

DOMS = logic.DOMS


# ── 에러 규격 {error, message} ──
def err(code, msg, status=400):
    return JSONResponse({"error": code, "message": msg}, status_code=status)


@app.exception_handler(Exception)
async def _unhandled(req, exc):
    return err("internal_error", "서버 오류", 500)


# ── 레이트리밋(IP 토큰버킷, daero 차용) + API키(선택) ──
_buckets = {}
_rl_lock = threading.Lock()


@app.middleware("http")
async def _guard(request: Request, call_next):
    if request.url.path.startswith("/api"):
        if config.API_KEY:
            key = request.query_params.get("key") or request.headers.get("x-api-key")
            if key != config.API_KEY:
                return err("unauthorized", "API 키 필요", 401)
        if config.RATELIMIT:
            ip = request.client.host if request.client else "?"
            now = time.time()
            with _rl_lock:
                tok, last = _buckets.get(ip, (config.RL_CAPACITY, now))
                tok = min(config.RL_CAPACITY, tok + (now - last) * config.RL_REFILL) - 1
                _buckets[ip] = (tok, now)
                if tok < 0:
                    return JSONResponse({"error": "rate_limited", "message": "요청이 많습니다"},
                                        status_code=429, headers={"Retry-After": "1"})
    return await call_next(request)


def _row(adm_cd=None, adm_nm=None):
    if adm_cd:
        df = snapshot.q("SELECT * EXCLUDE(geom) FROM dong WHERE adm_cd=?", [adm_cd])
    else:
        df = snapshot.q("SELECT * EXCLUDE(geom) FROM dong WHERE adm_nm=? LIMIT 1", [adm_nm])
    return df.to_dict("records")[0] if len(df) else None


def _dong_view(r):
    fac = {}
    for k, v in r.items():
        if k.endswith("_c") and v == v and v is not None:
            key = k[:-2]
            fac.setdefault(key, {})["cnt"] = int(v)
        elif k.endswith("_n") and v == v and v is not None:
            fac.setdefault(k[:-2], {})["nearest_m"] = int(v)
    def g(k):
        v = r.get(k); return v if (v == v and v is not None) else None
    return {"adm_cd": r.get("adm_cd"), "full_nm": r.get("full_nm"), "adm_nm": r.get("adm_nm"),
            "cohort": r.get("cohort"), "pop_total": g("pop_total"),
            "NLI": g("NLI"), "grade": r.get("grade"),
            "nli_cohort": g("nli_coh"),  # 동일 도농유형 내 백분위(밀도편향 보완)
            "domains": {d: g("score_" + d) for d in DOMS},
            "price_m2": g("price"),
            "price_pyeong": round(r["price"] * logic.PYEONG) if g("price") else None,
            "traits": {"density": g("dens"), "eld": g("r_eld"), "yth": g("r_yth"),
                       "inf": g("r_inf"), "apt": g("r_apt"), "old": g("r_old")},
            "facilities": fac}


# ── 엔드포인트 ──
@app.get("/api/health")
def health():
    n = snapshot.ready()
    return {"status": "ok" if n else "degraded", "snapshot": bool(n), "dong": n, "version": config.VERSION}


@app.get("/api/meta")
def meta():
    ds = snapshot.datasets_meta()
    return {"domains": logic.DOM_NAMES, "indicators": len(ds),
            "sources": [{"key": d.get("key"), "name": d.get("name"), "domain": d.get("domain"),
                         "source": d.get("source"), "updated": d.get("updated"), "license": d.get("license")} for d in ds],
            "note": "점수는 전국 읍면동 상대평가(백분위) 참고용(시설 밀도·근접 기반이라 도시성 일부 반영 → nli_cohort로 동일 도농유형 내 비교 권장). 복지 지오코딩 약 95% 커버."}


@app.get("/api/dong/{adm_cd}")
def dong(adm_cd: str):
    r = _row(adm_cd=adm_cd)
    if not r:
        return err("not_found", f"동 없음: {adm_cd}", 404)
    return _dong_view(r)


@app.get("/api/score")
def score(lat: float = Query(...), lon: float = Query(...)):
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return err("invalid_input", "좌표 범위 오류")
    df = snapshot.q("SELECT * EXCLUDE(geom) FROM dong WHERE ST_Contains(geom, ST_Point(?, ?)) LIMIT 1", [lon, lat])
    if not len(df):
        return err("out_of_bounds", "행정동 경계 밖", 404)
    return _dong_view(df.to_dict("records")[0])


@app.get("/api/rank")
def rank(sido: str = "", cohort: str = "", metric: str = "NLI", limit: int = Query(50, le=500)):
    col = metric if (metric == "NLI" or metric in DOMS or metric.startswith("score_")) else "NLI"
    if col in DOMS:
        col = "score_" + col
    where = ["pop_total > 0", f"{col} IS NOT NULL"]
    params = []
    if sido:
        where.append("full_nm LIKE ?"); params.append(sido + " %")
    if cohort:
        where.append("cohort = ?"); params.append(cohort)
    df = snapshot.q(f"SELECT adm_cd, full_nm, cohort, {col} AS val, grade FROM dong WHERE {' AND '.join(where)} ORDER BY val DESC LIMIT {int(limit)}", params)
    items = [{"rank": i + 1, "adm_cd": r["adm_cd"], "full_nm": r["full_nm"],
              "value": round(r["val"], 1), "grade": r["grade"]} for i, r in enumerate(df.to_dict("records"))]
    return {"metric": metric, "filter": {"sido": sido or None, "cohort": cohort or None}, "count": len(items), "items": items}


@app.get("/api/recommend")
def recommend(house: str = "일반", budget: int = None, base: str = "", km: int = 10, limit: int = Query(10, le=50)):
    if house not in logic.PRESETS:
        return err("invalid_input", f"house는 {list(logic.PRESETS)} 중 하나")
    return logic.recommend(house, budget, base or None, km, limit)


@app.get("/api/diag")
def diag_list():
    return logic.diag_list()


@app.get("/api/diag/{sgg}")
def diag(sgg: str):
    r = logic.diag(sgg)
    if not r:
        return err("not_found", f"지자체 없음: {sgg} (예: 시흥시)", 404)
    return r


@app.get("/api/geojson")
def geojson():
    if not os.path.exists(config.GEOJSON):
        return err("snapshot_unavailable", "geojson 없음", 503)
    return FileResponse(config.GEOJSON, media_type="application/geo+json")


@app.get("/api/points")
def points():
    if not os.path.exists(config.POINTS):
        return err("snapshot_unavailable", "points 없음", 503)
    return FileResponse(config.POINTS, media_type="application/json")


# ── 정적(데모·도구) — API 라우트 뒤에 마운트 ──
if os.path.isdir(config.STATIC_DIR):
    app.mount("/", StaticFiles(directory=config.STATIC_DIR, html=True), name="static")
