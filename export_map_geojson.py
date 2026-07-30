"""지도용 GeoJSON 생성 — 위상 보존 단순화(mapshaper) + 점수/근거 조인.
경계 폴리곤의 공유 경계를 보존해 인접 동 사이 흰 틈이 생기지 않게 함.
필요: node/npx (mapshaper 자동설치). 실행: ./venv/bin/python export_map_geojson.py
출력: data/processed/nli_map.geojson  (이후 build_web.py 실행)
"""
import duckdb, json, os, subprocess, tempfile

SHP = "data/processed/sgis/2. 경계/3. 2025년 2분기 기준 행정동 경계/bnd_dong_00_2025_2Q.shp"
SIMPLIFY = "5%"   # 낮을수록 부드럽고 가벼움. 위상 보존이라 %와 무관하게 틈 없음.
FAC = [('pharmacy','ph',1),('clinic','cl',1),('emergency','em',1),('school','sc',1),('store','st',0),
       ('park','pk',1),('bus','bs',1),('cctv','cc',1),('ev','ev',1),('welfare','wf',1)]


def simplify_boundary(dst):
    # mapshaper: SHP 직접 읽어 위상 단순화 + 슬리버 제거 + wgs84 재투영
    subprocess.run(["npx","-y","mapshaper",SHP,"-simplify",SIMPLIFY,"keep-shapes",
                    "-clean","-proj","wgs84","-o",dst,"format=geojson","precision=0.00001"], check=True)


def score_props():
    con = duckdb.connect("data/processed/nli.duckdb"); con.execute("LOAD spatial;")
    base = "data/processed/sgis/2. 경계"
    con.execute(f"CREATE OR REPLACE TEMP TABLE sido AS SELECT SIDO_CD,SIDO_NM FROM ST_Read('{base}/1. 2025년 2분기 기준 시도 경계/bnd_sido_00_2025_2Q.shp')")
    con.execute(f"CREATE OR REPLACE TEMP TABLE sgg AS SELECT SIGUNGU_CD,SIGUNGU_NM FROM ST_Read('{base}/2. 2025년 2분기 기준 시군구 경계/bnd_sigungu_00_2025_2Q.shp')")
    cnt = ",".join(f"s.{k}_cnt AS {c}_c" + (f", round(s.{k}_nearest_m) AS {c}_n" if n else "") for k,c,n in FAC)
    rows = con.execute(f"""SELECT s.adm_cd, sd.SIDO_NM||' '||sg.SIGUNGU_NM||' '||s.adm_nm AS full_nm, s.adm_nm, s.cohort, s.cohort_d, s.cen_lon AS clon, s.cen_lat AS clat, s.pop_total,
       s.NLI, s.grade, s.score_D1,s.score_D2,s.score_D3,s.score_D4,s.score_D5,s.score_D6,s.score_D7,s.score_D8,
       round(d.ratio_infant,3) AS r_inf, round(d.ratio_youth,3) AS r_yth, round(d.ratio_elderly,3) AS r_eld,
       round(d.pop_density,1) AS dens, round(d.ratio_apt,3) AS r_apt, round(d.ratio_oldhouse,3) AS r_old, {cnt}
       FROM nli_scores s LEFT JOIN dong d ON s.adm_cd=d.adm_cd
         LEFT JOIN sido sd ON substr(s.adm_cd,1,2)=sd.SIDO_CD LEFT JOIN sgg sg ON substr(s.adm_cd,1,5)=sg.SIGUNGU_CD""").df()
    props = {}
    for _, r in rows.iterrows():
        d = {}
        for c in rows.columns:
            if c == 'adm_cd': continue
            v = r[c]
            if isinstance(v, float) and v == v:   # not NaN
                d[c] = round(v, 5) if c in ('clon', 'clat') else round(v, 3) if c.startswith("r_") else (round(v, 1) if (c.startswith('score') or c == 'NLI') else int(v))
            else:
                d[c] = None if (isinstance(v, float)) else v
        props[r['adm_cd']] = d
    return props


def main():
    tmp = tempfile.mktemp(suffix=".geojson")
    simplify_boundary(tmp)
    props = score_props()
    geo = json.load(open(tmp))
    feats, miss = [], 0
    for f in geo['features']:
        p = props.get(f['properties'].get('ADM_CD'))
        if p is None: miss += 1; continue
        feats.append({"type": "Feature", "properties": p, "geometry": f['geometry']})
    json.dump({"type": "FeatureCollection", "features": feats},
              open("data/processed/nli_map.geojson", "w"), ensure_ascii=False, separators=(',', ':'))
    print(f"nli_map.geojson: {len(feats)}피처, 미매칭 {miss}, {round(os.path.getsize('data/processed/nli_map.geojson')/1e6,1)}MB")


if __name__ == "__main__":
    main()
