"""전국 사회복지시설 API 수집 (한국사회보장정보원 sclWlfrFcltInfoInqirService1).
data.go.kr 인증키(.env DATA_PORTAL_API_KEY) 사용. 응답 필드를 동적으로 전부 캡처
→ 좌표(위경도) 포함 여부를 자동 확인. 출력: data/raw/전국사회복지시설_API.csv
실행: ./venv/bin/python collect_welfare.py
"""
import os, csv, time, requests
import xml.etree.ElementTree as ET

KEY = [l.split("=", 1)[1].strip() for l in open(".env", encoding="utf-8")
       if l.startswith("DATA_PORTAL_API_KEY=")][0]
BASE = "https://apis.data.go.kr/B554287/sclWlfrFcltInfoInqirService1/getFcltListInfoInqire"


def fetch():
    rows, page = [], 1
    while True:
        r = requests.get(BASE, params={"serviceKey": KEY, "numOfRows": 1000, "pageNo": page}, timeout=40)
        if r.status_code == 403:
            print("403 Forbidden — 신규 승인 서비스 전파 대기중일 수 있음(수십분~1h 후 재시도)."); return None
        try:
            root = ET.fromstring(r.content)
        except Exception:
            print("XML 파싱 실패:", r.text[:200]); return None
        rc = root.findtext(".//resultCode")
        if rc not in (None, "00", "0"):
            print("API 오류:", rc, root.findtext(".//resultMsg")); return None
        items = root.findall(".//item")
        if not items:
            break
        for it in items:
            rows.append({c.tag: (c.text or "") for c in it})
        total = int(root.findtext(".//totalCount") or 0)
        print(f"page {page}: 누적 {len(rows)}/{total}")
        if len(rows) >= total or len(items) < 1000:
            break
        page += 1; time.sleep(0.2)
    return rows


def main():
    rows = fetch()
    if not rows:
        print("수집 실패/대기. (전파 후 재실행)"); return
    cols = sorted({k for r in rows for k in r})
    print("\n=== 응답 필드(전체) ===\n", cols)
    coord = [c for c in cols if any(k in c.lower() for k in ["la", "lo", "lat", "lot", "위도", "경도", "좌표", "xcnt", "ydnt"])]
    print("좌표 후보 컬럼:", coord)
    out = "data/raw/전국사회복지시설_API.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"저장 {out} · {len(rows)}건")


if __name__ == "__main__":
    main()
