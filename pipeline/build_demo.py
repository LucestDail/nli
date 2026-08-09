"""스토리 데모(demo.html) 생성 v2 — 스크롤 스냅·배경 그래픽·호버/탭 카드·마스킹·데이터 마퀴.
정적·경량. 실데이터 계산하되 추천/가성비 '값'은 마스킹(제품가치 보호). 출처 32종은 슬라이드로 노출.
실행: ./venv/bin/python pipeline/build_demo.py
"""
import json, bisect, collections, yaml

G = json.load(open("data/processed/nli_map.geojson", encoding="utf-8"))
F = [f["properties"] for f in G["features"] if (f["properties"].get("pop_total") or 0) > 0]
DS = yaml.safe_load(open("data/datasets.yml", encoding="utf-8"))["datasets"]
DK = [f"D{i}" for i in range(1, 10)]
SH = {"D1": "의료", "D2": "교육", "D3": "생활편의", "D4": "문화·여가", "D5": "교통", "D6": "안전", "D7": "환경", "D8": "복지", "D9": "반려"}
MET = {"D1": "의료·건강", "D2": "교육·보육", "D3": "생활편의·상업", "D4": "문화·여가·체육", "D5": "교통·이동", "D6": "안전", "D7": "환경·기후", "D8": "복지·돌봄", "D9": "반려·동물"}
IC = {"D1": "🏥", "D2": "🎓", "D3": "🛒", "D4": "🎭", "D5": "🚌", "D6": "🛡️", "D7": "🌿", "D8": "🤝", "D9": "🐾"}
PURPOSE = {"D1": "아플 때 얼마나 가까운가", "D2": "아이 키우고 배우기 좋은가", "D3": "일상 장보기·편의가 가까운가",
           "D4": "즐기고 쉴 곳이 있는가", "D5": "오가기 편한가", "D6": "안전한가",
           "D7": "환경·기후에 대응돼 있나", "D8": "돌봄이 필요할 때 받쳐주나", "D9": "반려동물과 살기 좋은가"}
COMPUTE = "인구 1만명당·면적 ㎢당 시설 수(공급밀도)와 가장 가까운 시설까지 거리(근접성)를 전국 백분위로 환산해 합산."
IND_BY_DOM = collections.defaultdict(list)
for d in DS:
    IND_BY_DOM[d["domain"]].append(d["name"])
NDONG = len(G["features"])


def nli(p):
    s = [p["score_" + d] for d in DK if p.get("score_" + d) is not None]
    return sum(s) / len(s)


def top_domains(p, n=2):
    ds = sorted(((p["score_" + d], SH[d]) for d in DK if p.get("score_" + d) is not None), reverse=True)[:n]
    return "·".join(d for _, d in ds)


# ── 큐레이션(마스킹해서 보여줄 실데이터) ──
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
rec = sorted([p for p in F if p.get("price") and p["price"] * 3.3058 <= 3000], key=lambda p: -wn(p))[:3]

# ── 진단(사각지대 최다 지자체) ──
Gs = collections.defaultdict(list)
for p in F:
    q = (p.get("full_nm") or "").split()
    if len(q) >= 2:
        Gs[(q[0], q[1])].append(p)
def blindn(L):
    return sum(1 for p in L for d in DK if (p.get("pop_total") or 0) >= 10000 and p.get("score_" + d) is not None and p["score_" + d] <= 20)
nat = {d: sum(p["score_" + d] for L in Gs.values() for p in L if p.get("score_" + d) is not None) /
          sum(1 for L in Gs.values() for p in L if p.get("score_" + d) is not None) for d in DK}
(dsi, dsg), dL = sorted(Gs.items(), key=lambda kv: -blindn(kv[1]))[0]
ddom = {d: sum(p["score_" + d] for p in dL if p.get("score_" + d) is not None) / max(1, len([p for p in dL if p.get("score_" + d) is not None])) for d in DK}
dweak = sorted(((d, round(ddom[d] - nat[d])) for d in DK), key=lambda x: x[1])[:3]
maxa = max(1, max(abs(v) for _, v in dweak))

# ── HTML 조립 ──
STYLE = """
*{box-sizing:border-box;margin:0}
:root{--ink:#1a2530;--mid:#5b6b77;--terra:#b0603f;--ocean:#2f6b4e;--sky:#3f8fa8;--bg:#f7f5ef;--line:#e7e1d5}
html{scroll-snap-type:y mandatory;scroll-behavior:smooth;-webkit-overflow-scrolling:touch}
body{font-family:-apple-system,'Malgun Gothic',sans-serif;color:var(--ink);background:var(--bg);line-height:1.65;-webkit-font-smoothing:antialiased;letter-spacing:-.01em;overflow-x:hidden}
/* 배경 그래픽 */
.bg{position:fixed;inset:0;z-index:-2;overflow:hidden;background:linear-gradient(160deg,#f9f7f1,#eef3ef 60%,#eaf0f2)}
.blob{position:absolute;border-radius:50%;filter:blur(60px);opacity:.42;animation:drift 22s ease-in-out infinite}
.b1{width:52vw;height:52vw;left:-12vw;top:-8vw;background:#bcd6c6}
.b2{width:44vw;height:44vw;right:-10vw;top:22vh;background:#cfe0e6;animation-delay:-7s}
.b3{width:40vw;height:40vw;left:18vw;bottom:-14vw;background:#e6d8c2;animation-delay:-13s}
@keyframes drift{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(4vw,-3vh) scale(1.08)}66%{transform:translate(-3vw,4vh) scale(.95)}}
.dots{position:fixed;inset:0;z-index:-1;opacity:.5;background-image:radial-gradient(rgba(60,80,90,.12) 1px,transparent 1px);background-size:26px 26px}
.nav{position:fixed;top:0;left:0;right:0;height:52px;display:flex;align-items:center;gap:8px;padding:0 16px;background:rgba(19,42,54,.9);backdrop-filter:blur(10px);color:#eaf1f2;z-index:100}
.nav b{font-weight:800}.nav .sp{margin-left:auto;display:flex;gap:6px}
.nav a{color:#eaf1f2;text-decoration:none;font-size:12px;padding:6px 10px;border:1px solid rgba(255,255,255,.25);border-radius:999px;white-space:nowrap}
.nav a.p{background:#fff;color:var(--ink);border-color:#fff;font-weight:700}
section{min-height:100vh;scroll-snap-align:start;scroll-snap-stop:always;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:70px 20px 46px;position:relative}
.wrap{max-width:900px;width:100%;margin:0 auto}
.rev{opacity:0;transform:translateY(22px);transition:.7s cubic-bezier(.22,1,.36,1)}.rev.on{opacity:1;transform:none}
.kick{color:var(--sky);font-weight:800;font-size:12.5px;letter-spacing:.09em;margin-bottom:12px}
h1{font-size:clamp(30px,6vw,54px);line-height:1.14;font-weight:800;letter-spacing:-.03em}
h2{font-size:clamp(23px,4.4vw,38px);font-weight:800;letter-spacing:-.02em}
.sub{color:var(--mid);font-size:clamp(14.5px,2.1vw,18px);margin:16px auto 0;max-width:600px;word-break:keep-all}
.kpis{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:26px}
.kpi{position:relative;background:rgba(255,255,255,.9);border:1px solid var(--line);border-radius:15px;padding:14px 20px;cursor:help;box-shadow:0 2px 8px rgba(20,30,40,.05)}
.kpi b{display:block;font-size:26px;font-weight:800;color:var(--ocean)}.kpi span{font-size:12px;color:var(--mid)}
.badge{margin-top:20px;display:inline-block;background:rgba(47,107,78,.1);color:var(--ocean);border-radius:999px;padding:9px 18px;font-size:13px;font-weight:700}
.domg{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:26px}
.dg{position:relative;background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:14px;padding:16px 8px;font-size:13.5px;font-weight:700;cursor:help;transition:.15s}
.dg:hover{border-color:var(--sky);transform:translateY(-2px)}.dg .i{display:block;font-size:26px;margin-bottom:6px}
/* 호버/탭 카드 */
.tip{position:absolute;left:50%;bottom:calc(100% + 10px);transform:translateX(-50%) translateY(6px);width:250px;background:#132a36;color:#eef4f2;border-radius:12px;padding:12px 14px;font-size:12px;font-weight:400;line-height:1.55;text-align:left;box-shadow:0 8px 24px rgba(0,0,0,.22);opacity:0;pointer-events:none;transition:.16s;z-index:50}
.tip b{color:#fff}.tip .t{font-weight:800;font-size:12.5px;display:block;margin-bottom:4px}.tip .m{color:#9fc3b4;font-size:11px;margin-top:6px}
.tip::after{content:"";position:absolute;left:50%;top:100%;transform:translateX(-50%);border:6px solid transparent;border-top-color:#132a36}
.kpi:hover .tip,.dg:hover .tip,.has.open .tip{opacity:1;transform:translateX(-50%);pointer-events:auto}
.exs{display:grid;gap:10px;margin-top:22px;max-width:560px;margin-left:auto;margin-right:auto}
.ex{display:flex;justify-content:space-between;align-items:center;gap:10px;background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:13px;padding:14px 18px;text-align:left;position:relative;overflow:hidden}
.exn{font-weight:800;font-size:15px}.exn .reg{display:block;font-size:11.5px;color:var(--mid);font-weight:500}
.exv{text-align:right;font-size:12.5px;color:var(--mid);white-space:nowrap}.exv b{color:var(--ink);font-size:15px}.exv i{font-style:normal;color:var(--terra);font-weight:700}
.p{color:var(--terra);font-weight:800;letter-spacing:.5px}
.f{display:none}
.ex.has{cursor:pointer}.ex.has:hover{border-color:var(--sky);box-shadow:0 5px 16px rgba(20,30,40,.09)}
.ex:hover .p,.ex.open .p{display:none}.ex:hover .f,.ex.open .f{display:inline}
.hint{margin-top:12px;font-size:12.5px;color:var(--mid)}
.bars{max-width:480px;margin:22px auto 0;background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:15px;padding:18px 20px}
.bar{display:flex;align-items:center;gap:10px;margin:8px 0}
.bl{width:104px;flex-shrink:0;text-align:left;font-size:13px;font-weight:700}
.bt{flex:1;height:16px;background:#f0ede7;border-radius:6px;overflow:hidden}
.bf{display:block;height:100%;border-radius:6px;background:linear-gradient(90deg,#c9754f,#b0603f);transition:width .8s cubic-bezier(.22,1,.36,1)}
.bv{width:38px;flex-shrink:0;text-align:right;font-weight:800;font-size:13px;color:var(--terra)}
.cta{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-top:30px}
.btn{text-decoration:none;padding:13px 24px;border-radius:999px;font-weight:700;font-size:14.5px;border:1.5px solid var(--ocean);color:var(--ocean);background:rgba(255,255,255,.7);transition:.15s;white-space:nowrap}
.btn.p{background:var(--ocean);color:#fff}.btn:hover{transform:translateY(-2px)}
.links{display:grid;grid-template-columns:1fr 1fr;gap:12px;max-width:640px;margin:26px auto 0}
.lc{position:relative;display:block;text-decoration:none;text-align:left;background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:16px;padding:18px 20px;color:var(--ink);transition:.16s;box-shadow:0 2px 8px rgba(20,30,40,.05)}
.lc:hover{border-color:var(--ocean);transform:translateY(-3px);box-shadow:0 8px 22px rgba(20,30,40,.1)}
.lc .i{font-size:26px;display:block;margin-bottom:8px}.lc b{font-size:16px;display:block}.lc .d{font-size:12.5px;color:var(--mid);display:block;margin-top:3px}
.lc .ar{position:absolute;top:18px;right:18px;color:var(--ocean);font-weight:800;font-size:18px}
@media(max-width:640px){.links{grid-template-columns:1fr}}
.note{color:var(--mid);font-size:12px;margin-top:14px}.hi{color:var(--terra);font-weight:800}.hg{color:var(--ocean);font-weight:800}
/* 데이터 마퀴 */
.marq{margin-top:24px;width:100vw;overflow:hidden;-webkit-mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);mask-image:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent)}
.track{display:flex;gap:10px;width:max-content;animation:scrollx 40s linear infinite}
.track.r{animation-direction:reverse;animation-duration:48s;margin-top:10px}
@keyframes scrollx{to{transform:translateX(-50%)}}
.src{flex-shrink:0;background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:999px;padding:9px 15px;font-size:12.5px;font-weight:600}
.src span{color:var(--mid);font-weight:500;font-size:11px}
.foot{text-align:center;color:var(--mid);font-size:11px;padding:24px 20px;scroll-snap-align:none}
@media(max-width:640px){.domg{grid-template-columns:repeat(3,1fr);gap:8px}.dg{padding:12px 5px;font-size:11.5px}.dg .i{font-size:22px}
  .tip{width:210px}.exv{font-size:11.5px}.kpi{padding:12px 15px}.kpi b{font-size:22px}}
"""

DOMG = "".join(
    f'<div class="dg has" tabindex="0"><span class="i">{IC[d]}</span>{MET[d]}'
    f'<div class="tip"><span class="t">{IC[d]} {MET[d]}</span>{PURPOSE[d]}. '
    f'<b>지표</b>: {" · ".join(IND_BY_DOM[d])}.<div class="m">산출: {COMPUTE}</div></div></div>'
    for d in DK)

def part(n):
    # 앞자리만 노출, 나머지 * (예: 78→7*, 2258→2***)
    s = str(int(round(n)))
    return s[0] + "*" * (len(s) - 1)

def num(full, n):
    # 기본=앞자리+* / 카드 호버 시 실제값
    return f'<span class="p">{part(n)}</span><span class="f">{full}</span>'

def card(name, reg, big_html, small_html):
    return (f'<div class="ex has" tabindex="0"><div class="exn">{name}<span class="reg">{reg}</span></div>'
            f'<div class="exv">{big_html}<br>{small_html}</div></div>')

REC = "".join(card(p["full_nm"].split(" ", 1)[1], p["full_nm"].split()[0][:2],
                   f'<b>{num(round(wn(p),1), wn(p))}점</b>',
                   f'평당 {num(f"{round(p["price"]*3.3058):,}", p["price"]*3.3058)}만') for p in rec)
VAL = "".join(card(p["full_nm"].split(" ", 1)[1], p["full_nm"].split()[0][:2],
                   f'<b>살기 {num(round(nli(p)), nli(p))}점</b>',
                   f'평당 {num(f"{round(p["price"]*3.3058):,}", p["price"]*3.3058)}만 · 강점 {top_domains(p)}') for p in value)
DBARS = "".join(
    f'<div class="bar"><span class="bl">{IC[d]} {SH[d]}</span>'
    f'<span class="bt"><span class="bf" style="width:{abs(v)/maxa*100:.0f}%"></span></span>'
    f'<span class="bv">{v}</span></div>' for d, v in dweak)

# 데이터 출처 마퀴(32종, 2행)
srcs = [f'<span class="src">{d["name"]} <span>· {d["source"]}</span></span>' for d in DS]
half = (len(srcs) + 1) // 2
row1 = "".join(srcs[:half]) * 2
row2 = "".join(srcs[half:]) * 2

BODY = f"""
<div class="bg"><div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div></div><div class="dots"></div>
<div class="nav"><span>🏘 <b>동네살기지수</b></span></div>

<section><div class="wrap rev"><div class="kick">공공데이터로 답하다</div>
  <h1>어디가<br>살기 좋은 동네일까?</h1>
  <div class="sub">아파트값만 보면 모릅니다. 의료·교육·교통·안전·복지까지, 전국 읍면동을 <b>9가지 생활 도메인</b>으로 채점하고 <b>아파트 실거래가·대중교통 소요시간</b>까지 결합했습니다.</div>
  <div class="kpis">
    <div class="kpi has" tabindex="0"><b>{NDONG:,}</b><span>읍면동</span><div class="tip"><span class="t">전국 읍면동(행정동)</span>실제 생활권 단위. 시군구(약 250개)보다 <b>14배 정밀</b>한 해상도로 채점.</div></div>
    <div class="kpi has" tabindex="0"><b>9</b><span>생활 도메인</span><div class="tip"><span class="t">9개 생활 도메인</span>의료·교육·생활편의·문화여가·교통·안전·환경·복지·반려. 삶에 매일 닿는 영역으로 종합.</div></div>
    <div class="kpi has" tabindex="0"><b>32</b><span>공공데이터 지표</span><div class="tip"><span class="t">32개 공공데이터 지표</span>9개 도메인을 32종 공개 데이터로 정량화. 100% 재현 가능.</div></div>
  </div>
  <div class="badge">＋ 아파트 실거래가 · 대중교통 결합</div>
  <div class="note">↓ 스크롤해서 살펴보세요</div></div></section>

<section><div class="wrap rev"><div class="kick">무엇으로 재나</div>
  <h2>'살기 좋음'은 9가지입니다</h2>
  <div class="sub">집값·평수로는 안 보입니다. 병원이 가까운지, 아이 학교·안전은, 버스는 자주 오는지 — 매일의 삶을 만드는 건 이 <b>9가지</b>입니다.</div>
  <div class="domg">{DOMG}</div></div></section>

<section><div class="wrap rev"><div class="kick">당신에게 맞는</div>
  <h2>가구에 맞는 동네는 다릅니다</h2>
  <div class="sub">육아 가구라면 교육·안전·의료를 더 중요하게 — 가중치를 바꿔 다시 계산합니다.</div>
  <div class="exs">{REC}</div></div></section>

<section><div class="wrap rev"><div class="kick">가격 대비</div>
  <h2>싸고 살기 좋은 곳이 있다</h2>
  <div class="sub"><span class="hg">살기지수는 높은데 아파트값은 낮은</span> 가성비 동네. 비싼 동네가 꼭 살기 좋은 건 아닙니다.</div>
  <div class="exs">{VAL}</div>
  <div class="note">카드에 마우스를 올리면(모바일은 탭) 실제 점수가 보입니다</div></div></section>

<section><div class="wrap rev"><div class="kick">지자체·기관용</div>
  <h2>우리 지역, 뭐가 부족할까?</h2>
  <div class="sub">인구는 많은데 특정 생활 인프라가 하위 20%인 <span class="hi">사각지대</span>를 찾아냅니다. 시설 입지·예산 배분의 근거.</div>
  <div class="bars"><div style="text-align:left;font-weight:800;margin-bottom:10px">가장 부족한 3개 영역 <span style="color:var(--mid);font-weight:500;font-size:12px">(전국 평균 대비 부족폭)</span></div>{DBARS}</div></div></section>

<section><div class="wrap rev"><div class="kick">믿을 수 있나</div>
  <h2>100% 공공데이터 · 투명·재현</h2>
  <div class="sub">추측 없이, 전부 공개 데이터로. 이만큼 긁어다 융합했습니다 — 32개 지표.</div></div>
  <div class="marq"><div class="track">{row1}</div><div class="track r">{row2}</div></div>
  <div class="wrap rev"><div class="note">점수는 전국 읍면동 상대평가(백분위) 기반 참고용입니다.</div></div></section>

<section style="min-height:88vh"><div class="wrap rev">
  <h2>이제 직접 확인해보세요</h2>
  <div class="sub">데모는 여기까지. 실제 데이터·수치는 도구에서.</div>
  <div class="links">
    <a class="lc" href="index.html#v=rec"><span class="i">🎯</span><b>내 동네 찾기</b><span class="d">가구·예산·통근으로 맞춤 추천 + 가성비 동네</span><span class="ar">→</span></a>
    <a class="lc" href="index.html#v=diag"><span class="i">🩺</span><b>지자체 진단</b><span class="d">우리 지역 취약 도메인·사각지대 리포트</span><span class="ar">→</span></a>
    <a class="lc" href="index.html"><span class="i">🗺</span><b>전국 지도 탐색</b><span class="d">동별 색칠·시설 위치·클릭 상세</span><span class="ar">→</span></a>
    <a class="lc" href="mailto:seunghyun.oh@bespinglobal.com?subject=%5B%EB%8F%99%EB%84%A4%EC%82%B4%EA%B8%B0%EC%A7%80%EC%88%98%5D%20%EB%8F%84%EC%9E%85%C2%B7%EC%A0%9C%ED%9C%B4%20%EB%AC%B8%EC%9D%98"><span class="i">📬</span><b>도입·제휴 문의</b><span class="d">지자체·기관·프롭테크</span><span class="ar">→</span></a>
  </div>
  <div class="foot" style="margin-top:32px">동네살기지수(NLI) · 공공데이터 기반 생활입지 인텔리전스</div></div></section>
"""

JS = """
<script>
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('on')}),{threshold:.12});
document.querySelectorAll('.rev').forEach(el=>io.observe(el));
// 모바일 탭 카드: .has 클릭 시 open 토글(터치 기기)
document.querySelectorAll('.has').forEach(el=>{
  el.addEventListener('click',ev=>{ev.stopPropagation();
    const was=el.classList.contains('open');
    document.querySelectorAll('.has.open').forEach(x=>x.classList.remove('open'));
    if(!was)el.classList.add('open');});
});
document.addEventListener('click',()=>document.querySelectorAll('.has.open').forEach(x=>x.classList.remove('open')));
</script>
"""

HTML = ("<!doctype html><html lang=ko><head><meta charset=utf-8>"
        "<meta name=viewport content=\"width=device-width,initial-scale=1\">"
        "<title>동네살기지수 — 어디가 살기 좋을까?</title>"
        "<meta name=description content=\"공공데이터로 전국 읍면동을 9가지 생활 도메인으로 채점. 살기지수 × 아파트값 × 대중교통.\">"
        "<meta property=\"og:title\" content=\"동네살기지수 — 어디가 살기 좋을까?\">"
        "<meta property=\"og:description\" content=\"전국 읍면동을 9가지로 채점 · 살기지수 × 아파트값. 나에게 맞는 동네 찾기.\">"
        f"<style>{STYLE}</style></head><body>{BODY}{JS}</body></html>")

open("demo.html", "w", encoding="utf-8").write(HTML)
print(f"생성: demo.html ({len(HTML)//1024}KB) · 스냅·배경·툴팁·마스킹·마퀴({len(DS)}출처) · 진단 {dsi} {dsg} 사각지대 {blindn(dL)}")
