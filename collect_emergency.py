"""전국 응급의료기관 API 수집 (국립중앙의료원 ErmctInfoInqireService).
data.go.kr 인증키(.env DATA_PORTAL_API_KEY) 사용. 출력: data/raw/전국응급의료기관_API.csv
실행: ./venv/bin/python collect_emergency.py
"""
import os, csv, time
import requests
import xml.etree.ElementTree as ET

KEY = None
for line in open(".env", encoding="utf-8"):
    if line.startswith("DATA_PORTAL_API_KEY="):
        KEY = line.split("=", 1)[1].strip()
BASE = "http://apis.data.go.kr/B552657/ErmctInfoInqireService/getEgytListInfoInqire"


def fetch():
    rows, page = [], 1
    while True:
        params = {"serviceKey": KEY, "pageNo": page, "numOfRows": 1000, "_type": "xml"}
        r = requests.get(BASE, params=params, timeout=30)
        root = ET.fromstring(r.content)
        header = root.findtext(".//resultCode")
        if header not in (None, "00"):
            print("API 응답코드:", header, root.findtext(".//resultMsg")); break
        items = root.findall(".//item")
        if not items:
            break
        for it in items:
            rows.append({
                "기관명": it.findtext("dutyName") or "",
                "주소": it.findtext("dutyAddr") or "",
                "전화": it.findtext("dutyTel1") or "",
                "기관분류": it.findtext("dgidIdName") or "",
                "경도": it.findtext("wgs84Lon") or "",
                "위도": it.findtext("wgs84Lat") or "",
            })
        total = int(root.findtext(".//totalCount") or 0)
        print(f"page {page}: 누적 {len(rows)}/{total}")
        if len(rows) >= total or len(items) < 1000:
            break
        page += 1
        time.sleep(0.2)
    return rows


def main():
    if not KEY:
        print("DATA_PORTAL_API_KEY 없음 (.env 확인)"); return
    rows = fetch()
    withxy = [r for r in rows if r["경도"] and r["위도"]]
    out = "data/raw/전국응급의료기관_API.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["기관명", "주소", "전화", "기관분류", "경도", "위도"])
        w.writeheader(); w.writerows(rows)
    print(f"저장 {out} · 총 {len(rows)}건, 좌표보유 {len(withxy)}건")


if __name__ == "__main__":
    main()
