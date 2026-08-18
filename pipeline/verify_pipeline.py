"""
NLI 파이프라인 검증기 (CLAUDE.md §2 "체커를 믿어라")
파이프라인 재실행 후 산출물의 정합성을 기계적으로 assert 한다.
검사: 총인구≈51.8M · 조인 매칭률 · 좌표 유효율 · 등급분포 · 상가세분 · geojson 피처수 · 딥링크/프리셋 임베드.
실행: ./venv/bin/python verify_pipeline.py   (FAIL 있으면 종료코드 1)
"""
import duckdb, json, os, sys, re

DB = "data/processed/nli.duckdb"
GEOJSON = "data/processed/nli_map.geojson"
POINTS = "data/processed/nli_points.json"
INDEX = "index.html"
N_DONG = 3559

_pass, _warn, _fail = [], [], []


def ck(cond, name, detail="", warn=False):
    (_pass if cond else (_warn if warn else _fail)).append(f"{name} — {detail}")
    mark = "✅" if cond else ("⚠️ " if warn else "❌")
    print(f"  {mark} {name}: {detail}")


def check_db():
    print("\n[1] nli.duckdb — dong / nli_scores")
    con = duckdb.connect(DB, read_only=True)
    nd = con.execute("SELECT count(*) FROM dong").fetchone()[0]
    ck(nd == N_DONG, "행정동 수", f"{nd} (기대 {N_DONG})")
    pop = con.execute("SELECT sum(pop_total) FROM dong").fetchone()[0]
    ck(51.0e6 <= pop <= 52.5e6, "전국 총인구", f"{int(pop):,} (기대 ≈51.8M)")
    nomatch = con.execute("SELECT count(*) FROM dong WHERE pop_total IS NULL").fetchone()[0]
    ck(nomatch == 0, "인구 조인 매칭", f"미매칭 {nomatch}건")
    for col in ("ratio_apt", "ratio_oldhouse"):
        rate = con.execute(f"SELECT count({col})*1.0/count(*) FROM dong").fetchone()[0]
        ck(rate > 0.99, f"{col} 파생율", f"{rate*100:.1f}%")

    ns = con.execute("SELECT count(*) FROM nli_scores").fetchone()[0]
    ck(ns == nd, "nli_scores 행수", f"{ns} (=dong {nd})")
    # 등급 5종 존재 + 합계 정합
    gr = dict(con.execute("SELECT grade, count(*) FROM nli_scores GROUP BY grade").fetchall())
    ck(set(gr) >= set("SABCD"), "등급 5종 존재", str({k: gr.get(k) for k in "SABCD"}))
    # 코호트 값 도메인
    coh = set(x[0] for x in con.execute("SELECT DISTINCT cohort FROM nli_scores").fetchall())
    ck(coh <= {"도시", "도농복합", "농촌"}, "cohort 값", str(coh))
    cohd = set(x[0] for x in con.execute("SELECT DISTINCT cohort_d FROM nli_scores").fetchall())
    ck(cohd <= {"도시", "도농복합", "농촌", "미상"}, "cohort_d 값(M6)", str(cohd))
    # 인구가중 중심점 좌표 유효율
    good = con.execute("""SELECT count(*) FROM nli_scores
        WHERE cen_lon BETWEEN 124 AND 132 AND cen_lat BETWEEN 33 AND 39""").fetchone()[0]
    ck(good/ns > 0.99, "중심점 좌표 유효율", f"{good/ns*100:.1f}% (통근·딥링크용)")
    # 상가 업종세분(M5): 생활편의 > 학원 > 여가, 모두 > 0
    st, ac, le = con.execute("SELECT sum(store_cnt),sum(academy_cnt),sum(leisure_cnt) FROM nli_scores").fetchone()
    ck(st > 0 and ac > 0 and le > 0, "상가 세분 카운트", f"생활편의 {int(st):,}·학원 {int(ac):,}·여가 {int(le):,}")
    ck(st > ac > le, "세분 크기 관계", "생활편의 > 학원 > 여가")
    con.close()


def check_geojson():
    print("\n[2] nli_map.geojson")
    if not os.path.exists(GEOJSON):
        ck(False, "파일 존재", GEOJSON); return
    feats = json.load(open(GEOJSON))["features"]
    ck(len(feats) >= N_DONG - 10, "피처 수", f"{len(feats)}")
    p = feats[0]["properties"]
    for key in ("r_old", "clat", "clon", "cohort_d", "NLI", "score_D1"):
        ck(key in p, f"프로퍼티 '{key}'", "존재" if key in p else "누락")
    sz = os.path.getsize(GEOJSON)/1e6
    ck(sz < 25, "파일 크기", f"{sz:.1f}MB", warn=True)


def check_points():
    print("\n[3] 시설 포인트")
    ck(os.path.exists(POINTS), "nli_points.json 존재",
       f"{os.path.getsize(POINTS)/1e6:.1f}MB" if os.path.exists(POINTS) else "누락")


def check_index():
    print("\n[4] index.html (배포 산출물)")
    if not os.path.exists(INDEX):
        ck(False, "파일 존재", INDEX); return
    html = open(INDEX, encoding="utf-8").read()
    sz = os.path.getsize(INDEX)/1e6
    ck(10 < sz < 22, "파일 크기", f"{sz:.1f}MB (경계 인라인, 시설점은 외부 지연로딩)")
    ck("nli_points.json" in html and "ensurePoints" in html, "시설점 지연로딩", "fetch('nli_points.json')")
    n_old = len(re.findall(r'"r_old":', html))
    ck(n_old >= N_DONG - 10, "r_old 임베드", f"{n_old}개")
    for token in ("function applyHash", "정보량(엔트로피)", "통근 보정", "인구밀도",
                  "지역 생활여건 진단", "내 동네 찾기", "이 동네 공유", "데이터 출처", "32개 지표"):
        ck(token in html, f"기능 문자열 '{token[:18]}'", "임베드됨" if token in html else "없음")
    # 탭 구조 무결성(3탭 IA: 지도/내동네/인사이트)
    for t in ("map", "find", "insight"):
        ck(f'data-v="{t}"' in html, f"탭 '{t}' 존재")
    for vid in ("v-map", "v-rec", "v-diag"):
        ck(f'id="{vid}"' in html, f"뷰 '{vid}' 보존")
    ck('data-v="home"' not in html, "홈 탭 제거(데모가 랜딩)")
    ck("30개 지표" not in html, "지표수 표기 정합(30 잔존 없음)")


def main():
    print("=" * 60 + "\nNLI 파이프라인 검증\n" + "=" * 60)
    check_db(); check_geojson(); check_points(); check_index()
    print("\n" + "=" * 60)
    print(f"결과: ✅ {len(_pass)} 통과 · ⚠️  {len(_warn)} 경고 · ❌ {len(_fail)} 실패")
    if _fail:
        print("\n실패 항목:")
        for f in _fail:
            print("  ❌ " + f)
        sys.exit(1)
    print("모든 필수 검사 통과.")


if __name__ == "__main__":
    main()
