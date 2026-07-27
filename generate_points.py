"""지도 표시용 시설 포인트 추출 (줌인 뷰포트 렌더용).
대용량(상가 270만·버스 22만·CCTV 37만)은 제외, 핵심 POI만 컴팩트 배열로.
출력: data/processed/nli_points.json  { "em":[[lon,lat],...], "ph":..., ... }
"""
import pandas as pd, json, os

HIRA = "data/processed/hira"; RAW = "data/raw"
SETS = {
    "em": ("전국응급의료기관", f"{RAW}/전국응급의료기관_API.csv", "csv", "경도", "위도"),
    "ph": ("약국", f"{HIRA}/2.약국정보서비스(2026.6.).xlsx", "xlsx", "좌표(X)", "좌표(Y)"),
    "cl": ("의료기관", f"{HIRA}/1.병원정보서비스(2026.6.).xlsx", "xlsx", "좌표(X)", "좌표(Y)"),
    "sc": ("학교", f"{RAW}/한국교육시설안전원_초중등학교위치_20260320.csv", "csv", "경도", "위도"),
    "pk": ("공원", f"{RAW}/전국도시공원정보표준데이터.csv", "csv", "경도", "위도"),
    "ev": ("전기차충전소", f"{RAW}/한국전력공사_전기차충전소위경도_20251231.csv", "csv", "경도", "위도"),
}


def read(path, kind, lon, lat):
    if kind == "xlsx":
        df = pd.read_excel(path, dtype=str)
    else:
        for enc in ("cp949", "utf-8-sig", "utf-8"):
            try: df = pd.read_csv(path, encoding=enc, dtype=str); break
            except Exception: df = None
    x = pd.to_numeric(df[lon], errors="coerce"); y = pd.to_numeric(df[lat], errors="coerce")
    m = x.between(124, 132) & y.between(33, 39)
    return [[round(a, 5), round(b, 5)] for a, b in zip(x[m], y[m])]


def main():
    out = {}
    for k, (name, path, kind, lon, lat) in SETS.items():
        pts = read(path, kind, lon, lat)
        out[k] = pts
        print(f"{name:12s} {len(pts):>7,}")
    json.dump(out, open("data/processed/nli_points.json", "w"), separators=(",", ":"))
    tot = sum(len(v) for v in out.values())
    print(f"총 {tot:,}점 · {round(os.path.getsize('data/processed/nli_points.json')/1e6,1)}MB")


if __name__ == "__main__":
    main()
