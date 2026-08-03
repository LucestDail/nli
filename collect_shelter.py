"""
전국무더위쉼터표준데이터 수집 (D7 편입) — safetydata.go.kr V2 오픈API
엔드포인트: https://www.safetydata.go.kr/V2/api/DSSP-IF-10942  (행정안전부 국민재난안전포털)
좌표필드: LO(경도)·LA(위도).  파일 다운로드는 100건 제한이라 이 API가 유일한 전국 수집 경로.

⚠️ 키: safetydata.go.kr는 data.go.kr과 별도 포털 → .env에 SAFETYDATA_API_KEY 필요.
   data.go.kr 키(DATA_PORTAL_API_KEY)로는 "SERVICE KEY IS NOT REGISTERED"(코드30) 발생.
   → .env에 한 줄 추가:  SAFETYDATA_API_KEY=발급받은키   그리고 실행.

실행: ./venv/bin/python collect_shelter.py
출력: data/raw/전국무더위쉼터_API.csv
"""
import os, csv, time, requests


def _key():
    env = dict(l.strip().split("=", 1) for l in open(".env", encoding="utf-8")
               if "=" in l and not l.strip().startswith("#"))
    return env.get("SAFETYDATA_API_KEY") or env.get("DATA_PORTAL_API_KEY")


ENDPOINT = "https://www.safetydata.go.kr/V2/api/DSSP-IF-10942"
OUT = "data/raw/전국무더위쉼터_API.csv"


def main():
    key = _key()
    if not key or key.startswith("SAFETYDATA_API_KEY"):
        print("❌ SAFETYDATA_API_KEY 미설정. safetydata.go.kr 발급 키를 .env에 추가하세요.")
        return
    rows, page = [], 1
    while True:
        r = requests.get(ENDPOINT, params={"serviceKey": key, "pageNo": page,
                                           "numOfRows": 1000, "returnType": "json"}, timeout=40)
        try:
            j = r.json()
        except Exception:
            print("JSON 파싱 실패:", r.text[:200]); return
        head = j.get("header", {})
        rc = str(head.get("resultCode", ""))
        if rc not in ("00", "0", ""):
            print(f"API 오류 [{rc}] {head.get('resultMsg')} {head.get('errorMsg','')}"); return
        body = j.get("body") or []
        if isinstance(body, dict):
            body = body.get("items", body.get("item", [])) or []
        if not body:
            break
        rows.extend(body)
        total = int(head.get("totalCount") or 0)
        print(f"page {page}: 누적 {len(rows)}/{total}")
        if (total and len(rows) >= total) or len(body) < 1000:
            break
        page += 1; time.sleep(0.2)
    if not rows:
        print("수집 0건 — 응답 확인:", r.text[:200]); return
    cols = list({k for row in rows for k in row})
    os.makedirs("data/raw", exist_ok=True)
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    # 좌표 유효율(LO=경도, LA=위도)
    ok = sum(1 for x in rows if _f(x.get("LO")) and _f(x.get("LA"))
             and 124 < _f(x.get("LO")) < 132 and 33 < _f(x.get("LA")) < 39)
    print(f"저장 {len(rows):,}행 → {OUT} | 좌표유효(LO/LA) {ok:,} ({ok/len(rows)*100:.1f}%)")


def _f(v):
    try: return float(v)
    except (TypeError, ValueError): return None


if __name__ == "__main__":
    main()
