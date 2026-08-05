"""지도 표시용 시설 포인트 추출 (뷰포트 렌더 + 호버/클릭 상세).
대용량(상가 270만·버스 22만·CCTV 37만·의료기관 8만)은 점 표시 제외.
출력: data/processed/nli_points.json  { "em":{"p":[[lon,lat]],"n":[이름],"a":[주소],"t":[전화],"c":[분류]}, ... }
"""
import pandas as pd, json, os

HIRA = "data/processed/hira"; RAW = "data/raw"
# (표시명, 경로, 종류, 경도, 위도, 이름, [주소후보], 전화컬럼|"", [분류컬럼들])
SETS = {
    "em": ("전국응급의료기관", f"{RAW}/전국응급의료기관_API.csv", "csv", "경도", "위도", "기관명", ["주소"], "전화", ["기관분류"]),
    "ph": ("약국", f"{HIRA}/2.약국정보서비스(2026.6.).xlsx", "xlsx", "좌표(X)", "좌표(Y)", "요양기관명", ["주소"], "전화번호", []),
    "sc": ("학교", f"{RAW}/한국교육시설안전원_초중등학교위치_20260320.csv", "csv", "경도", "위도", "학교명", ["소재지도로명주소", "소재지지번주소"], "", ["학교급구분", "설립형태"]),
    "pk": ("공원", f"{RAW}/전국도시공원정보표준데이터.csv", "csv", "경도", "위도", "공원명", ["소재지도로명주소", "소재지지번주소"], "전화번호", ["공원구분", "공원면적"]),
    "ev": ("전기차충전소", f"{RAW}/한국전력공사_전기차충전소위경도_20251231.csv", "csv", "경도", "위도", "충전소명", ["충전소주소"], "", []),
    "wf": ("사회복지시설", f"{RAW}/전국사회복지시설_좌표.csv", "csv", "경도", "위도", "시설명", ["주소"], "", ["시설종류"]),
}


def read(path, kind, lon, lat, nm, addrs, tel, cats):
    if kind == "xlsx":
        df = pd.read_excel(path, dtype=str)
    else:
        for enc in ("cp949", "utf-8-sig", "utf-8"):
            try: df = pd.read_csv(path, encoding=enc, dtype=str); break
            except Exception: df = None
    x = pd.to_numeric(df[lon], errors="coerce"); y = pd.to_numeric(df[lat], errors="coerce")
    def col(c): return df[c].fillna("") if c in df.columns else pd.Series([""] * len(df))
    names = col(nm)
    acol = next((c for c in addrs if c in df.columns), None)
    addr = col(acol) if acol else pd.Series([""] * len(df))
    telc = col(tel) if tel else pd.Series([""] * len(df))

    def catstr(row):
        parts = []
        for c in cats:
            v = str(row.get(c, "") or "").strip()
            if not v or v.lower() == "nan": continue
            if c == "공원면적":
                try: v = f"{int(float(v)):,}㎡"
                except Exception: pass
            parts.append(v)
        return " · ".join(parts)
    catser = df.apply(catstr, axis=1) if cats else pd.Series([""] * len(df))

    m = x.between(124, 132) & y.between(33, 39)
    P, N, A, T, C = [], [], [], [], []
    for a, b, n, ad, t, c in zip(x[m], y[m], names[m], addr[m], telc[m], catser[m]):
        P.append([round(a, 5), round(b, 5)]); N.append(str(n)[:40])
        A.append(str(ad)[:60]); T.append(str(t)[:20]); C.append(str(c)[:40])
    return P, N, A, T, C


def main():
    out = {}
    for k, (name, path, kind, lon, lat, nm, addrs, tel, cats) in SETS.items():
        P, N, A, T, C = read(path, kind, lon, lat, nm, addrs, tel, cats)
        out[k] = {"p": P, "n": N, "a": A, "t": T, "c": C}
        print(f"{name:12s} {len(P):>7,}")
    json.dump(out, open("data/processed/nli_points.json", "w"), ensure_ascii=False, separators=(",", ":"))
    tot = sum(len(v["p"]) for v in out.values())
    print(f"총 {tot:,}점 · {round(os.path.getsize('data/processed/nli_points.json')/1e6,1)}MB")


if __name__ == "__main__":
    main()
