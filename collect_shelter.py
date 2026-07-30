"""
전국무더위쉼터표준데이터 수집 (D7 편입 예정) — 오픈API
파일 다운로드는 100건 제한 → 오픈API 필수. 원천=safetydata.go.kr(국민재난안전포털), data.go.kr 15013199/15138456.

⚠️ ENDPOINT 미확정: 정확한 요청주소는 data.go.kr에서 해당 오픈API **활용신청 승인 후**
   '상세기능정보 / 샘플코드'에 표시되는 요청 URL을 그대로 붙여야 한다.
   (키 DATA_PORTAL_API_KEY는 게이트웨이에서 이미 정상 수락됨 = resultCode 12는 서비스명 미상 의미)

확정되면 아래 ENDPOINT 한 줄만 채우고 실행: ./venv/bin/python collect_shelter.py
출력: data/raw/전국무더위쉼터_API.csv (위경도 자동 탐지)
"""
import os, csv, json, time, requests
import xml.etree.ElementTree as ET

KEY = [l.split("=", 1)[1].strip() for l in open(".env", encoding="utf-8")
       if l.startswith("DATA_PORTAL_API_KEY=")][0]

# TODO: 활용신청 승인된 요청주소로 교체 (예: http://api.data.go.kr/openapi/tn_pubr_public_XXXXX_api)
ENDPOINT = ""
OUT = "data/raw/전국무더위쉼터_API.csv"


def parse(text):
    """JSON 또는 XML 응답에서 (items, totalCount) 추출."""
    try:
        j = json.loads(text)
        body = j.get("response", {}).get("body", j.get("body", j))
        items = body.get("items", body.get("item", []))
        if isinstance(items, dict):
            items = items.get("item", [])
        if isinstance(items, dict):
            items = [items]
        total = int(body.get("totalCount", len(items)) or 0)
        return items, total
    except json.JSONDecodeError:
        root = ET.fromstring(text)
        rc = root.findtext(".//resultCode")
        if rc not in (None, "00", "0"):
            print("API 오류:", rc, root.findtext(".//resultMsg")); return None, 0
        items = [{c.tag: (c.text or "") for c in it} for it in root.findall(".//item")]
        return items, int(root.findtext(".//totalCount") or len(items))


def main():
    if not ENDPOINT:
        print("❌ ENDPOINT 미설정. data.go.kr 15013199/15138456 오픈API 활용신청 후\n"
              "   승인된 '요청주소'를 이 파일 ENDPOINT 에 넣고 다시 실행하세요.")
        return
    rows, page = [], 1
    while True:
        r = requests.get(ENDPOINT, params={"serviceKey": KEY, "pageNo": page,
                                           "numOfRows": 1000, "type": "json", "dataType": "JSON"}, timeout=40)
        if r.status_code == 403:
            print("403 Forbidden — 활용신청 승인 전파 대기(수십분~1h 후 재시도)."); return
        items, total = parse(r.text)
        if items is None:
            print("응답 확인:", r.text[:200]); return
        if not items:
            break
        rows.extend(items)
        print(f"page {page}: 누적 {len(rows)}/{total}")
        if len(rows) >= total or len(items) < 1000:
            break
        page += 1; time.sleep(0.2)
    if not rows:
        print("수집 0건 — 응답 형식 확인 필요:", r.text[:200]); return
    cols = sorted({k for row in rows for k in row})
    lat = [c for c in cols if any(k in c for k in ["위도", "lat", "la"])]
    lon = [c for c in cols if any(k in c for k in ["경도", "lon", "lo"])]
    os.makedirs("data/raw", exist_ok=True)
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"저장 {len(rows):,}행 → {OUT} | 좌표컬럼 후보 위도={lat} 경도={lon}")


if __name__ == "__main__":
    main()
