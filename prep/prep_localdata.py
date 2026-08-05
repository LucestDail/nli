"""
LOCALDATA 인허가정보 가공 (여러 도메인 편입)
입력: data/raw/인허가정보.zip (지방행정 인허가 전 업종, 좌표=EPSG:5174 중부원점TM)
처리: 카테고리별 CSV 추출 → 영업/정상만 → 좌표정보(X,Y) 5174→4326 변환 → 한반도 범위 → 경도/위도 CSV
출력: data/raw/localdata_<key>.csv
실행: ./venv/bin/python prep_localdata.py
"""
import zipfile, io, pandas as pd, duckdb, warnings
warnings.filterwarnings("ignore")

SRC = "data/raw/인허가정보.zip"

# (출력키, 파일명에 포함된 업종 문자열, 도메인메모)
CATS = [
    ("bigstore", "대규모점포", "D3 대규모점포(백화점·마트)"),
    ("gas",      "석유판매업", "D3 주유소·석유판매"),
    ("museum",   "박물관 및 미술관", "D4 박물관·미술관"),
    ("theater",  "공연장", "D4 공연장"),
    ("cinema",   "영화상영관", "D4 영화상영관"),
    ("vethospital", "동물병원", "D9 동물병원(반려)"),
    ("vetpharm",    "동물약국", "D9 동물약국(반려)"),
]


def find(z, kw):
    for zi in z.infolist():
        if zi.filename.endswith("/"):
            continue
        try:
            nm = zi.filename.encode("cp437").decode("cp949")
        except Exception:
            nm = zi.filename
        # '공연장'은 '관광공연장업' 등과 구분: 파일명이 '_공연장.csv'로 끝나는 것 우선
        if nm.split("/")[-1] == f"fulldata_문화_{kw}.csv" or nm.split("/")[-1].endswith(f"_{kw}.csv"):
            return zi.filename, nm
    for zi in z.infolist():
        try:
            nm = zi.filename.encode("cp437").decode("cp949")
        except Exception:
            nm = zi.filename
        if kw in nm:
            return zi.filename, nm
    return None, None


def main():
    z = zipfile.ZipFile(SRC)
    con = duckdb.connect(); con.execute("INSTALL spatial;LOAD spatial;")
    for key, kw, memo in CATS:
        fn, dec = find(z, kw)
        if not fn:
            print(f"  ❌ '{kw}' 파일 못 찾음"); continue
        raw = z.read(fn)
        for enc in ("cp949", "utf-8-sig", "utf-8"):
            try:
                d = pd.read_csv(io.BytesIO(raw), encoding=enc, dtype=str); break
            except Exception:
                continue
        n0 = len(d)
        d = d[d["영업상태명"] == "영업/정상"].copy()
        d["X"] = pd.to_numeric(d["좌표정보(X)"], errors="coerce")
        d["Y"] = pd.to_numeric(d["좌표정보(Y)"], errors="coerce")
        d = d.dropna(subset=["X", "Y"])
        con.register("t", d[["사업장명", "X", "Y"]])
        out = con.execute("""SELECT 사업장명,
            round(ST_X(ST_Transform(ST_Point(X,Y),'EPSG:5174','EPSG:4326',always_xy:=true)),6) AS 경도,
            round(ST_Y(ST_Transform(ST_Point(X,Y),'EPSG:5174','EPSG:4326',always_xy:=true)),6) AS 위도
            FROM t""").df()
        out = out[(out["경도"].between(124, 132)) & (out["위도"].between(33, 39))]
        path = f"data/raw/localdata_{key}.csv"
        out.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  ✅ {memo}: {n0:,} → 영업·좌표유효 {len(out):,} → {path}")


if __name__ == "__main__":
    main()
