"""NLI 데이터 인입·스냅샷 빌드 — 단일 진입점.

흐름: data/datasets.yml 검증 → 스코어링 → 판정 → 지도/포인트 export → 웹빌드 → verify.
사용: ./venv/bin/python pipeline/ingest.py [--validate-only] [--skip-verify] [--skip-web]

★ 새 지표 추가 = data/datasets.yml 에 항목 하나 추가 후 이 스크립트 실행 (코드 수정 불필요).
   온프렘 갱신 = 원본 파일을 datasets.yml의 path 위치에 교체 후 실행.
"""
import sys, os, subprocess, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YML = os.path.join(ROOT, "data/datasets.yml")
DOMAINS = [f"D{i}" for i in range(1, 10)]
READERS = ("csv", "xlsx", "zip_csv")
REQUIRED = ("key", "name", "domain", "path", "reader", "lon", "lat")


def validate():
    """datasets.yml 스키마·정합 검증. (errs, warns, datasets) 반환."""
    doc = yaml.safe_load(open(YML, encoding="utf-8"))
    ds = doc.get("datasets", [])
    errs, warns, seen = [], [], set()
    for i, d in enumerate(ds):
        k = d.get("key", f"#{i}")
        for f in REQUIRED:
            if not d.get(f):
                errs.append(f"'{k}': 필수필드 '{f}' 누락")
        if k in seen:
            errs.append(f"중복 key: {k}")
        seen.add(k)
        if d.get("domain") not in DOMAINS:
            errs.append(f"'{k}': domain 이상({d.get('domain')})")
        if d.get("reader") not in READERS:
            errs.append(f"'{k}': reader 이상({d.get('reader')})")
        p = d.get("path")
        if p and not os.path.exists(os.path.join(ROOT, p)):
            warns.append(f"'{k}': 원본 파일 없음 → {p}")
    return errs, warns, ds


def run(label, script):
    print(f"\n▶ {label} ({script})")
    r = subprocess.run([sys.executable, f"pipeline/{script}"], cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"❌ {script} 실패 (exit {r.returncode})")


def main():
    args = sys.argv[1:]
    print("=" * 56)
    print("NLI ingest — datasets.yml 검증")
    errs, warns, ds = validate()
    doms = sorted(set(d.get("domain") for d in ds))
    print(f"  데이터셋 {len(ds)}개 · 도메인 {doms} · export_points {sum(1 for d in ds if d.get('export_points'))}종")
    for w in warns:
        print(f"  ⚠️  {w}")
    if errs:
        for e in errs:
            print(f"  ❌ {e}")
        raise SystemExit("datasets.yml 오류 — 중단")
    print("  ✅ yml 검증 통과")
    if "--validate-only" in args:
        return

    run("스코어링(공간결합·밀도·근접성·NLI)", "score_engine.py")
    run("판정(사각지대·결핍·프로필)", "analyze_nli.py")
    run("지도 export(mapshaper·점수조인)", "export_map_geojson.py")
    run("시설포인트 생성", "generate_points.py")
    if "--skip-web" not in args:
        run("웹 빌드", "build_web.py")
        subprocess.run(["cp", "nli_map.html", "index.html"], cwd=ROOT)
        print("  cp nli_map.html → index.html")
    if "--skip-verify" not in args:
        run("정합 검증", "verify_pipeline.py")
    print("\n✔ ingest 완료 — 스냅샷(nli.duckdb · nli_map.geojson · nli_points.json)"
          + ("" if "--skip-web" in args else " + index.html") + " 갱신")


if __name__ == "__main__":
    main()
