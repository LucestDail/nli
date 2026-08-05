"""
체육시설 가공 (D4 편입 전처리)
입력: data/raw/전국체육시설표준데이터.zip (전국체육시설현황 표준데이터, 개별시설+시설좌표위경도)
처리: 정상운영만 + 공공·커뮤니티(업종명이 '업'으로 끝나는 민간 등록업종 제외 → 여가상가 중복 회피) + 좌표유효
출력: data/raw/전국체육시설_공공_좌표.csv
실행: ./venv/bin/python prep_sports.py
"""
import zipfile, io, pandas as pd

SRC = "data/raw/전국체육시설표준데이터.zip"
OUT = "data/raw/전국체육시설_공공_좌표.csv"


def main():
    z = zipfile.ZipFile(SRC)
    name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
    for enc in ("cp949", "utf-8-sig", "utf-8"):
        try:
            df = pd.read_csv(io.BytesIO(z.read(name)), encoding=enc, dtype=str); break
        except (UnicodeDecodeError, LookupError):
            continue
    n0 = len(df)
    df = df[df["시설상태명"] == "정상운영"]                                   # 폐업 제외
    df = df[~df["업종명"].astype(str).str.endswith("업")]                     # 민간 등록업종(여가상가 중복) 제외
    lat = pd.to_numeric(df["시설좌표위도"], errors="coerce")
    lon = pd.to_numeric(df["시설좌표경도"], errors="coerce")
    df = df[lat.between(33, 39) & lon.between(124, 132)]                       # 한반도 범위
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"체육시설: 원본 {n0:,} → 정상운영·공공·좌표유효 {len(df):,}행 저장")
    print(f"  {OUT}")


if __name__ == "__main__":
    main()
