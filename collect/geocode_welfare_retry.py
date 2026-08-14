"""D8 사회복지시설 좌표 실패분 재지오코딩 (원본 다운로드 불필요 — 기존 좌표.csv의 주소 사용).
좌표 비어있는 행만 VWorld로 재시도: 도로명(road)·지번(parcel) 둘 다 시도해 커버리지 회복.
.env VWORLD_KEY 사용. 실행: ./venv/bin/python collect/geocode_welfare_retry.py
결과: data/raw/전국사회복지시설_좌표.csv 를 in-place 갱신(복구분 채움) + 백업.
"""
import os, csv, re, time, requests
from concurrent.futures import ThreadPoolExecutor

CSV = "data/raw/전국사회복지시설_좌표.csv"
URL = "http://api.vworld.kr/req/address"
KEY = [l.split("=", 1)[1].strip() for l in open(".env", encoding="utf-8") if l.startswith("VWORLD_KEY=")][0]
sess = requests.Session()


def clean(a):
    a = re.sub(r"\(.*?\)", "", str(a))
    a = a.split(",")[0]
    return re.sub(r"\s+", " ", a).strip()


STATS = {"http5xx": 0}   # VWorld 서버 스로틀(502/504) 감지용


def geocode(addr):
    a = clean(addr)
    if not a:
        return None
    for t in ("road", "parcel"):   # 도로명 우선, 실패 시 지번
        for attempt in (1, 2):     # 5xx(스로틀)면 잠깐 쉬고 1회 재시도
            try:
                r = sess.get(URL, params={"service": "address", "request": "getcoord",
                                          "version": "2.0", "crs": "epsg:4326", "type": t,
                                          "address": a, "key": KEY}, timeout=10)
                if r.status_code >= 500:   # 502/504 = 서버 스로틀 → 백오프 후 재시도
                    STATS["http5xx"] += 1
                    time.sleep(0.8)
                    continue
                j = r.json()
                if j.get("response", {}).get("status") == "OK":
                    p = j["response"]["result"]["point"]
                    return (p["x"], p["y"])
                break              # NOT_FOUND 등 정상응답 → 다음 type으로
            except Exception:
                time.sleep(0.3)
                continue
    return None


def main():
    rows = list(csv.reader(open(CSV, encoding="utf-8")))
    h, data = rows[0], rows[1:]
    ai = next(i for i, c in enumerate(h) if "주소" in c)
    xi = next(i for i, c in enumerate(h) if "경도" in c)
    yi = next(i for i, c in enumerate(h) if "위도" in c)
    fails = [r for r in data if not (len(r) > xi and r[xi].strip())]
    print(f"총 {len(data)}건 · 좌표 결측 {len(fails)}건 재시도")
    done = {"n": 0, "ok": 0}

    def work(r):
        res = geocode(r[ai])
        done["n"] += 1
        if done["n"] % 300 == 0:
            print(f"  진행 {done['n']}/{len(fails)} · 복구 {done['ok']} · 5xx {STATS['http5xx']}", flush=True)
        if res:
            r[xi], r[yi] = res
            done["ok"] += 1

    # 2026-08-13 교훈: 8워커는 VWorld 서버 스로틀(502/504) 유발 → 저동시성 기본 4(WORKERS로 조정)
    workers = int(os.environ.get("WORKERS", "4"))
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(work, fails))
    # 백업 후 저장
    os.replace(CSV, CSV + ".bak")
    w = csv.writer(open(CSV, "w", encoding="utf-8", newline=""))
    w.writerow(h); w.writerows(data)
    filled = sum(1 for r in data if len(r) > xi and r[xi].strip())
    print(f"복구 {done['ok']}건 · 최종 커버리지 {filled}/{len(data)} ({filled/len(data)*100:.1f}%) · 5xx {STATS['http5xx']} · {workers}워커 · {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
