"""
국토부 아파트 매매 실거래가 수집 (상품가치 격상: '살기지수 × 가격')
API: apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev (data.go.kr, 국토부)
파라미터: serviceKey, LAWD_CD(법정동 시군구 5자리), DEAL_YMD(YYYYMM)

⚠️ 두 가지 선행 필요:
 1) 이 API **활용신청**(data.go.kr 아파트매매 실거래가 상세) → 기존 DATA_PORTAL_API_KEY 계정. (미등록시 코드30)
 2) **법정동 시군구 코드(LAWD_CD) 목록** = data/raw/lawd_cd.csv (컬럼: lawd_cd,sigungu_nm)
    · SGIS 시군구코드(11230)≠법정동코드(11680)이므로 행안부 법정동코드 자료로 별도 구성.

수집: 최근 N개월 × 250 시군구 → 개별 거래(전용면적·거래금액·법정동·건축년도) 저장.
출력: data/raw/apt_trades.csv
실행: ./venv/bin/python collect_realprice.py   (완료까지 시간 소요, 재개 가능)
"""
import os, csv, time, requests
import xml.etree.ElementTree as ET

KEY = [l.split("=", 1)[1].strip() for l in open(".env", encoding="utf-8")
       if l.startswith("DATA_PORTAL_API_KEY=")][0]
URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
LAWD_FILE = "data/raw/lawd_cd.csv"
OUT = "data/raw/apt_trades.csv"
MONTHS = ["202601", "202602", "202603", "202604", "202605", "202606"]   # 수집 대상 계약년월

FIELDS = {"sggCd": "지역코드", "umdNm": "법정동", "aptNm": "아파트",
          "excluUseAr": "전용면적", "dealAmount": "거래금액", "floor": "층",
          "buildYear": "건축년도", "dealYear": "년", "dealMonth": "월", "dealDay": "일"}


def fetch(lawd, ymd):
    rows, page = [], 1
    while True:
        r = requests.get(URL, params={"serviceKey": KEY, "LAWD_CD": lawd, "DEAL_YMD": ymd,
                                       "numOfRows": 1000, "pageNo": page}, timeout=30)
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError:
            return None
        rc = root.findtext(".//resultCode") or root.findtext(".//returnReasonCode")
        if rc == "30":
            print("❌ 코드30 미등록 — 이 API 활용신청 필요"); return "STOP"
        items = root.findall(".//item")
        for it in items:
            rows.append({v: (it.findtext(k) or "").strip() for k, v in FIELDS.items()})
        total = int(root.findtext(".//totalCount") or 0)
        if len(rows) >= total or len(items) < 1000 or not items:
            break
        page += 1; time.sleep(0.1)
    return rows


def main():
    if not os.path.exists(LAWD_FILE):
        print(f"❌ {LAWD_FILE} 없음 — 법정동 시군구코드 목록 필요(행안부 법정동코드 자료).")
        return
    lawds = list(csv.DictReader(open(LAWD_FILE, encoding="utf-8-sig")))
    all_rows, done = [], 0
    for L in lawds:
        for ymd in MONTHS:
            res = fetch(L["lawd_cd"], ymd)
            if res == "STOP":
                return
            if res:
                for x in res:
                    x["sigungu_nm"] = L.get("sigungu_nm", "")
                all_rows.extend(res)
            time.sleep(0.05)
        done += 1
        if done % 20 == 0:
            print(f"  {done}/{len(lawds)} 시군구 · 누적 {len(all_rows):,}건")
    if not all_rows:
        print("수집 0건"); return
    cols = list(FIELDS.values()) + ["sigungu_nm"]
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(all_rows)
    print(f"저장 {len(all_rows):,}건 → {OUT} ({len(MONTHS)}개월 × {len(lawds)}시군구)")


if __name__ == "__main__":
    main()
