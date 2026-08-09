"""스토리 데모(demo.html) 생성 — 외부인이 스크롤로 가치를 3분 안에 파악.
정적·경량(데이터 인라인 X). 실데이터 큐레이션 예시 baking + 도구(index.html) 딥링크.
원칙: 1화면 1메시지 · '수치+해석' · 평문. 실행: ./venv/bin/python pipeline/build_demo.py
"""
import json, bisect, collections

G = json.load(open("data/processed/nli_map.geojson", encoding="utf-8"))
F = [f["properties"] for f in G["features"] if (f["properties"].get("pop_total") or 0) > 0]
DK = [f"D{i}" for i in range(1, 10)]
SH = {"D1": "의료", "D2": "교육", "D3": "생활편의", "D4": "문화·여가", "D5": "교통", "D6": "안전", "D7": "환경", "D8": "복지", "D9": "반려"}
MET = {"D1": "의료·건강", "D2": "교육·보육", "D3": "생활편의·상업", "D4": "문화·여가·체육", "D5": "교통·이동", "D6": "안전", "D7": "환경·기후", "D8": "복지·돌봄", "D9": "반려·동물"}
IC = {"D1": "🏥", "D2": "🎓", "D3": "🛒", "D4": "🎭", "D5": "🚌", "D6": "🛡️", "D7": "🌿", "D8": "🤝", "D9": "🐾"}
PY = 3.3058


def nli(p):
    s = [p["score_" + d] for d in DK if p.get("score_" + d) is not None]
    return sum(s) / len(s)


def top_domains(p, n=2):
    ds = sorted(((p["score_" + d], SH[d]) for d in DK if p.get("score_" + d) is not None), reverse=True)[:n]
    return "·".join(d for _, d in ds)


def pct_rank(p):
    arr = sorted(nli(x) for x in F)
    return round((1 - bisect.bisect_left(arr, nli(p)) / len(arr)) * 100)


# ── 큐레이션 데이터 ──
pr = [p for p in F if p.get("price") and (p.get("pop_total") or 0) >= 3000]
nS = sorted(nli(p) for p in pr); pS = sorted(p["price"] for p in pr)
value = sorted(pr, key=lambda p: -(bisect.bisect_left(nS, nli(p)) / len(nS) - bisect.bisect_left(pS, p["price"]) / len(pS)))[:3]

W = {"D1": 1.4, "D2": 2, "D3": 1, "D4": 1.3, "D5": 1, "D6": 1.6, "D7": 1, "D8": 1.2, "D9": 1}
def wn(p):
    s = t = 0
    for d in DK:
        v = p.get("score_" + d)
        if v is not None:
            s += W[d] * v; t += W[d]
    return s / t
rec = sorted([p for p in F if p.get("price") and p["price"] * PY <= 3000], key=lambda p: -wn(p))[:3]

Gs = collections.defaultdict(list)
for p in F:
    q = (p.get("full_nm") or "").split()
    if len(q) >= 2:
        Gs[(q[0], q[1])].append(p)
def blindn(L):
    return sum(1 for p in L for d in DK if (p.get("pop_total") or 0) >= 10000 and p.get("score_" + d) is not None and p["score_" + d] <= 20)
nat = {d: sum(p["score_" + d] for L in Gs.values() for p in L if p.get("score_" + d) is not None) /
          sum(1 for L in Gs.values() for p in L if p.get("score_" + d) is not None) for d in DK}
diag_sgg = sorted(Gs.items(), key=lambda kv: -blindn(kv[1]))[0]
(dsi, dsg), dL = diag_sgg
ddom = {d: sum(p["score_" + d] for p in dL if p.get("score_" + d) is not None) / max(1, len([p for p in dL if p.get("score_" + d) is not None])) for d in DK}
dweak = sorted(((d, round(ddom[d] - nat[d])) for d in DK), key=lambda x: x[1])[:3]
dblind = sorted([(p["adm_nm"], int(p["pop_total"])) for p in dL for d in DK
                 if (p.get("pop_total") or 0) >= 10000 and p.get("score_" + d) is not None and p["score_" + d] <= 20],
                key=lambda x: -x[1])[:3]

NDONG = len([f for f in G["features"]])

# ── HTML ──
def vcard(p):
    return (f'<div class="ex"><div class="exn">{p["full_nm"].split(" ",1)[1] if " " in p["full_nm"] else p["full_nm"]}'
            f'<span>{p["full_nm"].split()[0][:2]}</span></div>'
            f'<div class="exv"><b>살기 {round(nli(p))}점</b> · 상위 {pct_rank(p)}%<br><i>평당 {round(p["price"]*PY):,}만</i> · 강점 {top_domains(p)}</div></div>')

def rcard(p):
    return (f'<div class="ex"><div class="exn">{p["full_nm"].split(" ",1)[1] if " " in p["full_nm"] else p["full_nm"]}'
            f'<span>{p["full_nm"].split()[0][:2]}</span></div>'
            f'<div class="exv"><b>{round(wn(p),1)}점</b><br><i>평당 {round(p["price"]*PY):,}만</i></div></div>')

# 다이버징 막대(진단 최약 도메인)
maxa = max(1, max(abs(v) for _, v in dweak))
dbars = "".join(
    f'<div class="bar"><span class="bl">{IC[d]} {SH[d]}</span>'
    f'<span class="bt"><span class="bf" style="width:{abs(v)/maxa*100:.0f}%;background:{"#b0603f" if v<0 else "#2f6b4e"}"></span></span>'
    f'<span class="bv" style="color:{"#b0603f" if v<0 else "#2f6b4e"}">{"+" if v>=0 else ""}{v}</span></div>'
    for d, v in dweak)

DOMGRID = "".join(f'<div class="dg"><span>{IC[d]}</span>{MET[d]}</div>' for d in DK)

HTML = f"""<!doctype html><html lang=ko><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>동네살기지수 — 어디가 살기 좋을까?</title>
<meta name=description content="공공데이터로 전국 {NDONG:,}개 읍면동을 9가지 생활 도메인으로 채점. 살기지수 × 아파트값 × 대중교통.">
<meta property="og:title" content="동네살기지수 — 어디가 살기 좋을까?">
<meta property="og:description" content="전국 읍면동을 9가지로 채점 · 살기지수 × 아파트값. 나에게 맞는 동네 찾기.">
<style>
*{{box-sizing:border-box;margin:0}}
:root{{--ink:#1a2530;--mid:#5b6b77;--terra:#b0603f;--ocean:#2f6b4e;--sky:#3f8fa8;--bg:#faf8f4;--line:#ece7dd}}
body{{font-family:-apple-system,'Malgun Gothic',sans-serif;color:var(--ink);background:var(--bg);line-height:1.65;-webkit-font-smoothing:antialiased;letter-spacing:-.01em}}
.nav{{position:fixed;top:0;left:0;right:0;height:52px;display:flex;align-items:center;gap:8px;padding:0 18px;background:rgba(19,42,54,.92);backdrop-filter:blur(10px);color:#eaf1f2;z-index:100}}
.nav b{{font-weight:800}}.nav .sp{{margin-left:auto;display:flex;gap:6px}}
.nav a{{color:#eaf1f2;text-decoration:none;font-size:12.5px;padding:6px 11px;border:1px solid rgba(255,255,255,.25);border-radius:999px}}
.nav a.p{{background:#fff;color:var(--ink);border-color:#fff;font-weight:700}}
section{{min-height:88vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:80px 22px 60px;max-width:900px;margin:0 auto}}
.rev{{opacity:0;transform:translateY(24px);transition:.7s cubic-bezier(.22,1,.36,1)}}.rev.on{{opacity:1;transform:none}}
.kick{{color:var(--sky);font-weight:800;font-size:13px;letter-spacing:.08em;margin-bottom:12px}}
h1{{font-size:clamp(30px,6vw,52px);line-height:1.15;font-weight:800;letter-spacing:-.03em}}
h2{{font-size:clamp(24px,4.5vw,38px);font-weight:800;letter-spacing:-.02em}}
.sub{{color:var(--mid);font-size:clamp(15px,2.2vw,18px);margin-top:16px;max-width:620px}}
.kpis{{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:26px}}
.kpi{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 20px;box-shadow:0 1px 3px rgba(20,30,40,.05)}}
.kpi b{{display:block;font-size:26px;font-weight:800;color:var(--ocean)}}.kpi span{{font-size:12px;color:var(--mid)}}
.domg{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:28px;width:100%;max-width:560px}}
.dg{{background:#fff;border:1px solid var(--line);border-radius:13px;padding:16px 8px;font-size:13.5px;font-weight:600}}.dg span{{display:block;font-size:26px;margin-bottom:6px}}
.exs{{display:grid;gap:10px;margin-top:26px;width:100%;max-width:560px}}
.ex{{display:flex;justify-content:space-between;align-items:center;gap:10px;background:#fff;border:1px solid var(--line);border-radius:13px;padding:14px 18px;text-align:left}}
.exn{{font-weight:800;font-size:15px}}.exn span{{display:block;font-size:11.5px;color:var(--mid);font-weight:500}}
.exv{{text-align:right;font-size:12.5px;color:var(--mid)}}.exv b{{color:var(--ink);font-size:15px}}.exv i{{font-style:normal;color:var(--terra);font-weight:700}}
.bars{{width:100%;max-width:480px;margin-top:24px;background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 20px}}
.bar{{display:flex;align-items:center;gap:10px;margin:7px 0}}.bl{{width:96px;text-align:left;font-size:13px;font-weight:600}}
.bt{{flex:1;height:16px;background:#f0ede7;border-radius:5px;position:relative}}.bf{{position:absolute;right:50%;height:100%;border-radius:4px}}
.bt::before{{content:"";position:absolute;left:50%;top:-3px;bottom:-3px;width:1px;background:#c2b8a5}}.bv{{width:34px;text-align:right;font-weight:800;font-size:13px}}
.chips{{display:flex;gap:7px;flex-wrap:wrap;justify-content:center;margin-top:22px}}.chip{{background:#fff;border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:12.5px;color:var(--mid)}}
.cta{{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-top:32px}}
.btn{{text-decoration:none;padding:14px 26px;border-radius:999px;font-weight:700;font-size:15px;border:1.5px solid var(--ocean);color:var(--ocean);background:#fff;transition:.15s}}
.btn.p{{background:var(--ocean);color:#fff}}.btn:hover{{transform:translateY(-2px)}}
.note{{color:var(--mid);font-size:12.5px;margin-top:14px}}.hi{{color:var(--terra);font-weight:800}}.hg{{color:var(--ocean);font-weight:800}}
.foot{{text-align:center;color:var(--mid);font-size:11.5px;padding:30px 20px 50px;border-top:1px solid var(--line)}}
@media(max-width:560px){{.domg{{grid-template-columns:repeat(3,1fr)}}}}
</style></head><body>
<div class="nav"><span>🏘 <b>동네살기지수</b></span><div class="sp">
  <a href="index.html#v=rec">내 동네 찾기</a><a href="index.html#v=diag">지자체 진단</a><a class="p" href="index.html">전체 도구</a></div></div>

<section><div class="rev"><div class="kick">공공데이터로 답하다</div>
  <h1>어디가<br>살기 좋은 동네일까?</h1>
  <div class="sub">아파트값만 보면 모릅니다. 의료·교육·교통·안전·복지까지 — 전국 <b>{NDONG:,}개 읍면동</b>을 <b>9가지 생활 도메인·32개 지표</b>로 채점했습니다.</div>
  <div class="kpis"><div class="kpi"><b>{NDONG:,}</b><span>읍면동</span></div><div class="kpi"><b>9</b><span>생활 도메인</span></div><div class="kpi"><b>32</b><span>공공데이터 지표</span></div><div class="kpi"><b>×가격·교통</b><span>결합</span></div></div>
  <div class="cta"><a class="btn p" href="index.html">🗺 전국 지도 열기</a></div></div></section>

<section><div class="rev"><div class="kick">무엇으로 재나</div>
  <h2>'살기 좋음'은 9가지입니다</h2>
  <div class="sub">내 삶에 매일 닿는 것들. 각 도메인을 여러 공공데이터로 정량화했습니다.</div>
  <div class="domg">{DOMGRID}</div></div></section>

<section><div class="rev"><div class="kick">당신에게 맞는</div>
  <h2>가구에 맞는 동네는 다릅니다</h2>
  <div class="sub">육아 가구라면 교육·안전·의료를 더 중요하게 — 가중치를 바꿔 다시 계산합니다. <b>육아 가구 · 평당 3천만 이하</b> 추천:</div>
  <div class="exs">{''.join(rcard(p) for p in rec)}</div>
  <div class="cta"><a class="btn" href="index.html#v=rec">🎯 내 조건으로 추천받기</a></div></div></section>

<section><div class="rev"><div class="kick">가격 대비</div>
  <h2>싸고 살기 좋은 곳이 있다</h2>
  <div class="sub"><span class="hg">살기지수는 높은데 아파트값은 낮은</span> 가성비 동네. 비싼 동네가 꼭 살기 좋은 건 아닙니다.</div>
  <div class="exs">{''.join(vcard(p) for p in value)}</div>
  <div class="cta"><a class="btn" href="index.html#v=rec">💎 가성비 동네 더 보기</a></div></div></section>

<section><div class="rev"><div class="kick">지자체·기관용</div>
  <h2>우리 지역, 뭐가 부족할까?</h2>
  <div class="sub"><b>{dsi} {dsg}</b> — 인구는 많은데 특정 생활 인프라가 하위 20%인 <span class="hi">사각지대 {blindn(dL)}곳</span>. 시설 입지·예산 배분의 근거가 됩니다.</div>
  <div class="bars">{dbars}<div class="note" style="text-align:left;margin-top:10px">전국 지자체 평균 대비 편차 · 우선 보강: {', '.join(nm for nm,_ in dblind)}</div></div>
  <div class="cta"><a class="btn" href="index.html#v=diag">🩺 우리 지자체 진단 보기</a></div></div></section>

<section><div class="rev"><div class="kick">믿을 수 있나</div>
  <h2>100% 공공데이터 · 투명·재현</h2>
  <div class="sub">추측 없이, 전부 공개 데이터로. 점수 산출 방식도 공개합니다.</div>
  <div class="chips"><span class="chip">통계청 SGIS</span><span class="chip">국토교통부 실거래가</span><span class="chip">건강보험심사평가원</span><span class="chip">소상공인시장진흥공단</span><span class="chip">공공데이터포털 표준데이터</span><span class="chip">safetydata</span></div>
  <div class="note">점수는 전국 읍면동 상대평가(백분위) 기반 참고용입니다.</div></div></section>

<section style="min-height:70vh"><div class="rev">
  <h2>지금 확인해보세요</h2>
  <div class="cta">
    <a class="btn p" href="index.html#v=rec">🎯 내게 맞는 동네</a>
    <a class="btn" href="index.html#v=diag">🩺 지자체 진단</a>
    <a class="btn" href="mailto:seunghyun.oh@bespinglobal.com?subject=%5B%EB%8F%99%EB%84%A4%EC%82%B4%EA%B8%B0%EC%A7%80%EC%88%98%5D%20%EB%AC%B8%EC%9D%98">📬 도입 문의</a>
  </div></div></section>

<div class="foot">동네살기지수(NLI) · 공공데이터 기반 생활입지 인텔리전스 · 전국 상대평가 참고용</div>
<script>
const io=new IntersectionObserver((es)=>es.forEach(e=>{{if(e.isIntersecting)e.target.classList.add('on')}}),{{threshold:.15}});
document.querySelectorAll('.rev').forEach(el=>io.observe(el));
</script></body></html>"""

open("demo.html", "w", encoding="utf-8").write(HTML)
print(f"생성: demo.html ({len(HTML)//1024}KB) · 큐레이션: 가성비 {value[0]['full_nm']} · 추천 {rec[0]['full_nm']} · 진단 {dsi} {dsg} 사각지대 {blindn(dL)}건")
