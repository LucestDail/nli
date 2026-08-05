"""D8 사회복지시설 주소 → 좌표 지오코딩 (VWorld API, 읍면동 정밀화용).
.env VWORLD_KEY 사용. http 엔드포인트(ssl 이슈 회피) + 병렬 + 주소중복제거.
실행: ./venv/bin/python geocode_welfare.py
출력: data/raw/전국사회복지시설_좌표.csv (시설명,시설종류,주소,경도,위도)
"""
import os, csv, re, requests
from concurrent.futures import ThreadPoolExecutor

SRC = os.path.expanduser("~/Downloads/보건복지부_사회복지시설 정보_20260318.csv")
OUT = "data/raw/전국사회복지시설_좌표.csv"
URL = "http://api.vworld.kr/req/address"
KEY = [l.split("=", 1)[1].strip() for l in open(".env", encoding="utf-8") if l.startswith("VWORLD_KEY=")][0]
sess = requests.Session()


def clean(a):
    """VWorld 파서용 주소 정제: 괄호(법정동)·쉼표 뒤 층/호수 제거."""
    a = re.sub(r"\(.*?\)", "", str(a))
    a = a.split(",")[0]
    return re.sub(r"\s+", " ", a).strip()


import time


def _req(addr, typ):
    for attempt in range(2):           # 버스트 속도제한 대비 재시도
        try:
            r = sess.get(URL, params={"service": "address", "request": "getcoord", "version": "2.0",
                                      "crs": "epsg:4326", "type": typ, "address": addr,
                                      "format": "json", "key": KEY}, timeout=12)
            if not r.text.strip():      # 빈 응답 = 순간 차단 → 백오프 후 재시도
                time.sleep(0.3); continue
            j = r.json()
            st = j.get("response", {}).get("status")
            if st == "OK":
                p = j["response"]["result"]["point"]
                return float(p["x"]), float(p["y"])
            return None                 # NOT_FOUND 등 → 다음 typ로
        except Exception:
            time.sleep(0.3)
    return None


def geocode(addr):
    for typ in ("ROAD", "PARCEL"):     # 도로명 우선, 실패 시 지번
        xy = _req(addr, typ)
        if xy:
            return xy
    return None, None


CACHE = "data/processed/geocode_cache.json"


def main():
    import pandas as pd, json, threading
    df = pd.read_csv(SRC, encoding="cp949", dtype=str).fillna("")
    df["addr_clean"] = df["시설주소"].map(clean)
    uniq = sorted(set(a for a in df["addr_clean"] if a))
    # 재개: 캐시에 있는 주소는 건너뜀
    coords = {}
    if os.path.exists(CACHE):
        coords = {k: tuple(v) for k, v in json.load(open(CACHE, encoding="utf-8")).items()}
    todo = [a for a in uniq if a not in coords]
    print(f"시설 {len(df):,} · 고유주소 {len(uniq):,} · 캐시 {len(coords):,} · 신규 {len(todo):,} 지오코딩…")
    lock = threading.Lock()
    cnt = [0, 0]  # done, ok
    DELAY = 0.2    # 재개: 중속(~4/s) 단일스레드, 버스트 회피
    def work(a):
        xy = geocode(a)
        with lock:
            coords[a] = xy; cnt[0] += 1
            if xy[0]: cnt[1] += 1
            if cnt[0] % 300 == 0:
                json.dump(coords, open(CACHE, "w", encoding="utf-8"))   # 중간 저장(재개용)
                print(f"  {cnt[0]:,}/{len(todo):,} · 성공 {cnt[1]:,}")
        time.sleep(DELAY)
    with ThreadPoolExecutor(max_workers=1) as ex:   # 단일 스레드
        list(ex.map(work, todo))
    json.dump(coords, open(CACHE, "w", encoding="utf-8"))
    ok = sum(1 for v in coords.values() if v[0])
    print(f"고유주소 성공 {ok:,}/{len(uniq):,} ({100*ok//max(1,len(uniq))}%)")
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["시설명", "시설종류", "주소", "경도", "위도"])
        n = 0
        for _, r in df.iterrows():
            lon, lat = coords.get(r["addr_clean"], (None, None))
            w.writerow([r["시설명"], r.get("시설종류", ""), r["시설주소"], lon or "", lat or ""])
            if lon: n += 1
    print(f"저장 {OUT} · 시설 {len(df):,} 중 좌표 {n:,}건")


if __name__ == "__main__":
    main()
