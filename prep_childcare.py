"""
어린이집 가공 (D2 편입 전처리)
입력: data/raw/childcare_src/*.xls  (어린이집정보공개포털 시도별 조각 16개, .xls)
처리: 운영중(정상·재개)만 필터 → 명+주소 중복제거 → 위경도 유효만
출력: data/raw/전국어린이집_운영중_좌표.csv
실행: ./venv/bin/python prep_childcare.py   (xlrd 필요)
"""
import pandas as pd, glob, os

SRC = "data/raw/childcare_src"
OUT = "data/raw/전국어린이집_운영중_좌표.csv"


def main():
    files = sorted(glob.glob(f"{SRC}/*.xls"))
    df = pd.concat([pd.read_excel(f, dtype=str) for f in files], ignore_index=True)
    n0 = len(df)
    df = df[df["운영현황"].astype(str).str.contains("정상|재개", na=False)]      # 폐지·휴지 제외
    df = df.drop_duplicates(subset=["어린이집명", "주소"])                        # 조각 경계 중복 제거
    lat = pd.to_numeric(df["위도"], errors="coerce")
    lon = pd.to_numeric(df["경도"], errors="coerce")
    df = df[lat.between(33, 39) & lon.between(124, 132)]                          # 한반도 범위
    # 지오코딩 실패 폴백 제거: 서울시청(37.5665,126.9780)에 전국 주소가 165개 몰림
    bad = (lat.round(4) == 37.5665) & (lon.round(4) == 126.978)
    n_bad = int(bad[df.index].sum())
    df = df[~bad[df.index]]
    print(f"  서울시청 폴백좌표 제거: {n_bad}건")
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"어린이집: 원본 {n0:,} → 운영중·중복제거·좌표유효 {len(df):,}행 저장")
    print(f"  {OUT}")


if __name__ == "__main__":
    main()
