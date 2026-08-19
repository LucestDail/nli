"""
국토부 아파트 매매 실거래가 수집 (상품가치 격상: '살기지수 × 가격')
API: apis.data.go.kr/1613000/RTMSDataSvcAptTrade (data.go.kr, 국토부)
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
URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
LAWD_FILE = "data/raw/lawd_cd.csv"
OUT = "data/raw/apt_trades.csv"
MONTHS = ["202601", "202602", "202603", "202604", "202605", "202606"]   # 수집 대상 계약년월

FIELDS = {"sggCd": "지역코드", "umdNm": "법정동", "aptNm": "아파트",
          "excluUseAr": "전용면적", "dealAmount": "거래금액", "floor": "층",
          "buildYear": "건축년도", "dealYear": "년", "dealMonth": "월", "dealDay": "일"}


def _get(params, tries=4):
    """타임아웃·일시오류 재시도(백오프). 실패해도 None 반환하고 계속 진행."""
    for t in range(tries):
        try:
            return requests.get(URL, params=params, timeout=20)
        except requests.exceptions.RequestException:
            time.sleep(1.5 * (t + 1))
    return None


def fetch(lawd, ymd):
    rows, page = [], 1
    while True:
        r = _get({"serviceKey": KEY, "LAWD_CD": lawd, "DEAL_YMD": ymd, "numOfRows": 1000, "pageNo": page})
        if r is None:
            print(f"  ⚠️ {lawd}/{ymd} 재시도 실패 → 건너뜀"); return rows or None
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError:
            return rows or None
        rc = root.findtext(".//resultCode") or root.findtext(".//returnReasonCode")
        if rc == "30":
            print("❌ 코드30 미등록 — 이 API 활용신청 필요"); return "STOP"
        if rc in ("22", "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR"):
            print("❌ 일일 트래픽(10,000) 초과 — 내일 재개"); return "STOP"
        if rc not in ("00", "000", None, ""):
            print(f"  ⚠️ {lawd}/{ymd} 응답코드 {rc} → 건너뜀"); return rows or None
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
    cols = list(FIELDS.values()) + ["sigungu_nm"]

    def save(rows):
        with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    all_rows, done, stopped = [], 0, False
    for L in lawds:
        for ymd in MONTHS:
            res = fetch(L["lawd_cd"], ymd)
            if res == "STOP":
                stopped = True; break
            if res:
                for x in res:
                    x["sigungu_nm"] = L.get("sigungu_nm", "")
                all_rows.extend(res)
            time.sleep(0.05)
        if stopped:
            break
        done += 1
        if done % 20 == 0:
            save(all_rows)   # 체크포인트: 크래시/중단 대비 중간 저장
            print(f"  {done}/{len(lawds)} 시군구 · 누적 {len(all_rows):,}건 (체크포인트 저장)")
    if not all_rows:
        print("수집 0건"); return
    save(all_rows)
    tag = " [중단됨-부분수집]" if stopped else ""
    print(f"저장 {len(all_rows):,}건 → {OUT} ({len(MONTHS)}개월 × {done}/{len(lawds)}시군구){tag}")


if __name__ == "__main__":
    main()
