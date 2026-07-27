"""동네살기지수 NLI — 배포용 SPA 대시보드 빌더 (모던 디자인 + 자동완성).
입력: data/processed/nli_map.geojson · 출력: nli_map.html (자체완결 단일파일)
재생성: ./venv/bin/python build_web.py
"""
import os

geojson = open("data/processed/nli_map.geojson", encoding="utf-8").read()
points = open("data/processed/nli_points.json", encoding="utf-8").read()

TEMPLATE = r'''<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>동네살기지수 NLI · 어디가 살기 좋은 동네인가</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Noto+Serif+KR:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css"/>
<style>
 :root{
  --ocean:#173a4b;--ocean2:#22586c;--sky:#3f8fa8;--sage:#6f9e86;--terra:#c47c52;--amber:#d4a056;
  --bg:#f5f3ee;--card:#ffffff;--ink:#16232e;--mid:#5b6b77;--light:#9aa7b2;--line:#ece7dd;--line2:#f4f0e9;
  --serif:"Cormorant Garamond","Noto Serif KR",Georgia,serif;
  --sans:"Pretendard Variable",Pretendard,-apple-system,BlinkMacSystemFont,"Noto Sans KR",sans-serif;
  --r:14px;--r-lg:18px;--r-xl:26px;
  --sh:0 1px 3px rgba(20,30,40,.05);--sh2:0 12px 34px -10px rgba(20,30,40,.22);
  --grad:linear-gradient(135deg,#1c4c60,#2f7d94);}
 *{box-sizing:border-box}
 html,body{margin:0;height:100%;font-family:var(--sans);color:var(--ink);background:var(--bg);line-height:1.55;-webkit-font-smoothing:antialiased;letter-spacing:-.01em}
 #app{display:flex;flex-direction:column;height:100%}
 nav{background:rgba(19,42,54,.88);backdrop-filter:saturate(180%) blur(12px);color:#eaf1f2;display:flex;align-items:center;gap:6px;padding:0 20px;height:60px;flex-shrink:0;position:relative;z-index:1000;border-bottom:1px solid rgba(255,255,255,.06)}
 nav .logo{width:30px;height:30px;border-radius:9px;background:var(--grad);display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 3px 10px rgba(0,0,0,.25)}
 nav .brand{font-weight:700;font-size:17px;letter-spacing:-.02em;margin:0 18px 0 9px;white-space:nowrap;color:#fff}
 nav .brand small{font-weight:400;opacity:.5;font-size:10px;margin-left:6px;letter-spacing:2px}
 nav .tab{padding:8px 15px;border-radius:999px;cursor:pointer;font-size:13.5px;font-weight:500;color:#a9c0c8;transition:.18s}
 nav .tab:hover{background:rgba(255,255,255,.08);color:#fff}
 nav .tab.on{background:#fff;color:var(--ocean);font-weight:600}
 .gsearch{margin-left:auto;position:relative}
 .gsearch input{padding:9px 15px 9px 34px;border:0;border-radius:999px;font-size:13px;width:250px;background:rgba(255,255,255,.14);color:#fff;font-family:var(--sans);transition:.18s}
 .gsearch input::placeholder{color:#9fb6bf}.gsearch input:focus{background:#fff;color:var(--ink);width:290px;outline:none}
 .gsearch::before{content:"⌕";position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#9fb6bf;font-size:16px;pointer-events:none}
 .gsearch input:focus + .ac,.gsearch:focus-within::before{color:var(--mid)}
 .ac{position:absolute;top:44px;right:0;width:300px;background:#fff;border-radius:var(--r);box-shadow:var(--sh2);overflow:hidden;display:none;z-index:1200;border:1px solid var(--line)}
 .ac-item{padding:10px 14px;font-size:13px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:8px;color:var(--ink)}
 .ac-item:hover{background:var(--line2)}
 .view{flex:1;overflow:auto;min-height:0}
 .view.map{overflow:hidden;position:relative;display:flex}
 .wrap{max-width:1220px;margin:0 auto;padding:34px 30px 60px}
 .hero-t{font-family:var(--serif);font-size:38px;font-weight:700;letter-spacing:-.5px;margin:0 0 6px;color:var(--ocean);line-height:1.1}
 h2{font-size:24px;font-weight:700;letter-spacing:-.03em;margin:0 0 5px;color:var(--ink)}
 .sub{color:var(--mid);font-size:14.5px;margin-bottom:26px;max-width:640px}
 .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:30px}
 .kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--r-lg);padding:20px;box-shadow:var(--sh);position:relative;overflow:hidden}
 .kpi::before{content:"";position:absolute;left:0;top:0;width:100%;height:3px;background:var(--grad);opacity:.85}
 .kpi b{display:block;font-size:36px;font-weight:800;color:var(--ocean);line-height:1.05;letter-spacing:-.02em}
 .kpi span{color:var(--mid);font-size:12.5px;font-weight:500}
 .grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:var(--r-lg);padding:24px;box-shadow:var(--sh);transition:.2s}
 .card h3{font-weight:700;margin:0 0 15px;font-size:16px;color:var(--ink);letter-spacing:-.02em}
 .barrow{display:flex;align-items:center;gap:10px;font-size:12.5px;margin:6px 0}
 .barrow .nm{width:120px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--mid)}
 .barrow .bar{flex:1;height:8px;background:var(--line2);border-radius:6px;overflow:hidden}
 .barrow .bar>span{display:block;height:100%;border-radius:6px}.barrow .v{width:38px;text-align:right;font-weight:700}
 .place{display:flex;justify-content:space-between;align-items:center;padding:9px 11px;border-radius:11px;cursor:pointer;transition:.14s}
 .place:hover{background:var(--line2)}
 table{width:100%;border-collapse:collapse;font-size:13px}
 th,td{padding:10px 11px;border-bottom:1px solid var(--line2);text-align:left}
 th{color:var(--mid);font-size:11.5px;font-weight:600;position:sticky;top:0;background:#fff;text-transform:uppercase;letter-spacing:.03em}
 td.n{text-align:right;font-variant-numeric:tabular-nums}
 tbody tr{cursor:pointer}tbody tr:hover td{background:var(--line2)}
 .g{display:inline-flex;align-items:center;justify-content:center;min-width:24px;height:24px;border-radius:7px;color:#fff;font-weight:700;font-size:12px;padding:0 5px}
 select,input[type=text]{padding:9px 12px;border:1px solid var(--line);border-radius:11px;font-size:13px;background:#fff;font-family:var(--sans);color:var(--ink);transition:.15s}
 select:focus,input:focus{outline:none;border-color:var(--sky)}
 button.btn{padding:8px 15px;border:1px solid var(--line);background:#fff;border-radius:999px;cursor:pointer;font-size:13px;font-family:var(--sans);color:var(--ink);font-weight:500;transition:.15s}
 button.btn:hover{border-color:var(--sage);color:var(--sage);background:#f4f8f5}
 button.btn.on{background:var(--ocean);color:#fff;border-color:var(--ocean);font-weight:600}
 aside{width:312px;background:#faf8f4;border-right:1px solid var(--line);overflow:auto;padding:20px;flex-shrink:0}
 aside .sec{margin-bottom:19px}aside h3{margin:0 0 9px;font-size:11px;letter-spacing:.08em;color:var(--terra);text-transform:uppercase;font-weight:700}
 aside select{width:100%}
 .seg{display:flex;background:var(--line2);border-radius:12px;padding:3px;gap:2px}
 .seg button{flex:1;padding:8px 3px;border:0;background:transparent;border-radius:9px;font-size:12.5px;cursor:pointer;font-family:var(--sans);color:var(--mid);font-weight:500;transition:.15s}
 .seg button.on{background:#fff;color:var(--ocean);font-weight:700;box-shadow:var(--sh)}
 #map{flex:1}
 .legend i{width:13px;height:13px;display:inline-block;margin-right:8px;vertical-align:-2px;border-radius:4px}.legend div{margin:3px 0;font-size:12px;color:var(--mid)}
 .detail{position:absolute;top:18px;right:18px;z-index:900;width:320px;max-height:calc(100% - 36px);overflow:auto;background:#fff;border-radius:var(--r-lg);box-shadow:var(--sh2);padding:20px;font-size:13px;border:1px solid var(--line)}
 .detail h4{margin:0 0 4px;font-size:20px;color:var(--ink);font-weight:700;letter-spacing:-.02em;line-height:1.2}
 .muted{color:var(--mid);font-size:12px}
 .bar{height:8px;background:var(--line2);border-radius:5px;overflow:hidden;margin:4px 0}.bar>span{display:block;height:100%;border-radius:5px}
 .dom{margin-top:10px;padding-top:10px;border-top:1px solid var(--line2)}.dom .hd{display:flex;justify-content:space-between;font-weight:600;font-size:13px}
 .ev{font-size:12px;color:var(--mid);margin-top:2px}.warn{color:var(--terra);font-weight:700}
 .close{float:right;cursor:pointer;color:var(--light);font-size:18px;line-height:1}
 .rng{display:flex;align-items:center;gap:10px;margin:7px 0}.rng label{width:84px;font-size:12px;color:var(--mid)}.rng input{flex:1}.rng b{width:26px;text-align:right;font-size:12px;color:var(--ocean);font-weight:700}
 .heart{cursor:pointer;font-size:15px;color:var(--terra)}
 .foot{color:var(--light);font-size:11px;padding:20px 30px;text-align:center;border-top:1px solid var(--line);line-height:1.8}
 .flex{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
 input[type=range]{accent-color:var(--ocean);height:4px}
 ::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:#d9d1c3;border-radius:10px;border:2px solid var(--bg)}
</style></head><body>
<div id="app">
 <nav>
   <div class="logo">🏘</div><div class="brand">동네살기지수<small>NLI</small></div>
   <div class="tab on" data-v="home">홈</div>
   <div class="tab" data-v="map">지도</div>
   <div class="tab" data-v="rank">순위</div>
   <div class="tab" data-v="compare">비교</div>
   <div class="tab" data-v="persona">맞춤설정</div>
   <div class="gsearch"><input id="gsearch" placeholder="지역 검색 (예: 강남구 역삼)" autocomplete="off"><div class="ac" id="gac"></div></div>
 </nav>

 <div class="view" id="v-home"><div class="wrap">
   <div class="hero-t">어디가 살기 좋은 동네일까</div>
   <div class="sub">공공데이터 표준 300종을 읍면동 단위로 융합한 살기좋은동네 지수 · 전국 3,553개 읍면동 · 7개 도메인</div>
   <div class="kpis" id="kpis"></div>
   <div class="grid2">
     <div class="card"><h3>시도별 평균 지수</h3><div id="sidoBars"></div></div>
     <div class="card"><h3>등급 분포</h3><div id="gradeBars"></div>
       <h3 style="margin-top:20px">전국 상위</h3><div id="homeTop"></div>
       <h3 style="margin-top:16px">전국 하위</h3><div id="homeBot"></div></div>
   </div>
 </div><div class="foot" id="foot1"></div></div>

 <div class="view map" id="v-map" style="display:none">
   <aside>
     <div class="sec"><h3>지표 선택</h3><select id="metric"></select></div>
     <div class="sec"><h3>뷰 모드</h3><div class="seg" id="modes">
       <button data-m="basic" class="on">기본</button><button data-m="blind">사각지대</button><button data-m="pop">인구대비</button></div>
       <div class="muted" id="modeDesc" style="margin-top:8px"></div></div>
     <div class="sec"><h3>인구 필터 (최소)</h3><div class="flex"><input type="range" id="popmin" min="0" max="50000" step="1000" value="0" style="flex:1"><span id="popval" style="font-size:12px;width:56px;text-align:right;color:var(--mid)">전체</span></div></div>
     <div class="sec"><h3>시설 표시</h3><div id="ptToggles"></div><div class="muted" id="ptHint" style="margin-top:7px"></div></div>
     <div class="sec"><h3>범례</h3><div class="legend" id="legend"></div></div>
     <div class="muted">맞춤설정 탭에서 가중치를 바꾸면 종합 지수 색이 실시간으로 반영됩니다.</div>
   </aside>
   <div id="map"></div>
   <div class="detail" id="detail" style="display:none"></div>
 </div>

 <div class="view" id="v-rank" style="display:none"><div class="wrap">
   <h2>지역 순위</h2><div class="sub">테마·시도·유형을 골라 정렬하세요. 행 클릭 → 상세, ⊕ → 비교담기, ♡ → 관심</div>
   <div class="flex" style="margin-bottom:16px">
     <select id="rankMetric"></select><select id="rankSido"></select>
     <select id="rankCohort"><option value="">전체 유형</option><option>도시</option><option>도농복합</option><option>농촌</option></select>
     <span class="muted" id="rankCount"></span></div>
   <div class="card" style="padding:0;max-height:64vh;overflow:auto"><table id="rankTable"></table></div>
 </div></div>

 <div class="view" id="v-compare" style="display:none"><div class="wrap">
   <h2>지역 비교 <span class="muted" style="font-size:14px;font-weight:400">최대 4곳</span></h2>
   <div class="sub">검색으로 추가하거나 순위·지도에서 ⊕로 담으세요. 각 행에서 가장 좋은 값은 초록으로 강조됩니다.</div>
   <div class="flex" style="margin-bottom:16px;position:relative"><input type="text" id="cmpSearch" placeholder="지역 추가 (예: 노형동)" style="width:280px" autocomplete="off"><div class="ac" id="cmpac" style="left:0;top:44px;right:auto"></div><button class="btn" id="cmpClear">비우기</button></div>
   <div id="compareBody"></div>
 </div></div>

 <div class="view" id="v-persona" style="display:none"><div class="wrap">
   <h2>나에게 맞는 동네</h2><div class="sub">중요한 도메인의 비중을 조절하면 전국 순위·지도가 즉시 재계산됩니다.</div>
   <div class="grid2">
     <div class="card"><h3>페르소나 프리셋</h3><div class="flex" id="presets"></div>
       <div id="sliders" style="margin-top:18px"></div>
       <button class="btn" id="resetW" style="margin-top:14px">균등으로 초기화</button></div>
     <div class="card"><h3>이 가중치 기준 전국 상위 15</h3><div id="personaTop"></div></div>
   </div>
 </div></div>
</div>
<script>
const DATA=__GEOJSON__;
const POINTS=__POINTS__;
const F=DATA.features;
const DOMS=['D1','D2','D3','D4','D5','D6','D7'];
const METRICS={NLI:'종합 지수',D1:'의료·건강',D2:'교육·보육',D3:'생활편의·상업',D4:'문화·여가·체육',D5:'교통·이동',D6:'안전',D7:'환경·기후',grade:'등급'};
const DOMFAC={D1:[['ph','약국',1],['cl','의료기관',1],['em','응급의료기관',1]],D2:[['sc','학교',1]],D3:[['st','상가',0]],D4:[['pk','공원',1]],D5:[['bs','버스정류장',1]],D6:[['cc','CCTV',1]],D7:[['ev','전기차충전소',1]]};
const GC={S:'#2f6b4e',A:'#6f9e86',B:'#d4a056',C:'#cf8a5c',D:'#b0603f'};
const PRESETS={'균등':[1,1,1,1,1,1,1],'영유아 양육':[1.4,2,1,1.3,1,1.6,1],'고령':[2,1,1.2,1.2,1.4,1.2,1.3],'1인 청년':[1,1,2,1.5,1.5,1,1],'반려동물':[1,1,1,2,1,1.2,1.3]};
let W=[1,1,1,1,1,1,1];
let fav=JSON.parse(localStorage.getItem('nli_fav')||'[]');
let cmp=[];

F.forEach(f=>{f.properties.sido=(f.properties.full_nm||'').split(' ')[0];});
const pops=F.map(f=>f.properties.pop_total||0).sort((a,b)=>a-b);
function popPct(v){let lo=0,hi=pops.length;while(lo<hi){let m=(lo+hi)>>1;if(pops[m]<v)lo=m+1;else hi=m}return lo/pops.length}
function color(v){if(v==null||isNaN(v))return '#dcd2bf';return v>=80?'#2f6b4e':v>=65?'#6f9e86':v>=50?'#a9c3ad':v>=35?'#e6d3a0':v>=20?'#d59f72':'#b0603f';}
function nliW(p){let s=0,w=0;DOMS.forEach((d,i)=>{let v=p['score_'+d];if(v!=null&&!isNaN(v)){s+=W[i]*v;w+=W[i]}});return w?+(s/w).toFixed(1):null}
function metricVal(p,m){return (m==='NLI'||m==='grade')?nliW(p):p['score_'+m]}
let nliRank=new Map();
function recompRank(){const arr=F.map(f=>[f.properties.adm_nm,nliW(f.properties)]).sort((a,b)=>a[1]-b[1]);arr.forEach((x,i)=>nliRank.set(x[0],i/arr.length));}
function gradeOf(p){const r=nliRank.get(p.adm_nm);return r==null?p.grade:(r>=.9?'S':r>=.65?'A':r>=.35?'B':r>=.1?'C':'D')}
function fullN(p){return p.full_nm||p.adm_nm}
function dist(m){return m==null?'':m<1000?m+'m':(m/1000).toFixed(1)+'km'}
function walk(m){return m==null?'':' (도보 '+Math.max(1,Math.round(m/80))+'분)'}
const BS_POP=10000,BS_SCORE=20;
function isBlind(p,m){return (p.pop_total||0)>=BS_POP && (metricVal(p,m||'NLI'))<=BS_SCORE}

/* 자동완성 */
function attachAC(input,box,onPick){
  input.addEventListener('input',()=>{const q=input.value.trim();if(!q){box.style.display='none';return}
    const ms=[];for(const f of F){if((f.properties.full_nm||'').includes(q)){ms.push(f.properties);if(ms.length>=8)break}}
    if(!ms.length){box.style.display='none';return}
    box.innerHTML=ms.map(p=>`<div class="ac-item" data-adm="${p.adm_nm}"><span>${p.full_nm}</span><span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></div>`).join('');
    box.style.display='block';
    box.querySelectorAll('.ac-item').forEach(it=>it.onclick=()=>{box.style.display='none';input.value='';onPick(it.dataset.adm)});});
  input.addEventListener('keydown',e=>{if(e.key==='Enter'){const first=box.querySelector('.ac-item');const q=input.value.trim();const f=first?F.find(x=>x.properties.adm_nm===first.dataset.adm):F.find(x=>(x.properties.full_nm||'').includes(q));if(f){box.style.display='none';input.value='';onPick(f.properties.adm_nm)}}if(e.key==='Escape')box.style.display='none';});
  document.addEventListener('click',e=>{if(!input.parentElement.contains(e.target))box.style.display='none'});
}

document.querySelectorAll('nav .tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('nav .tab').forEach(x=>x.classList.remove('on'));t.classList.add('on');
  const v=t.dataset.v;['home','map','rank','compare','persona'].forEach(x=>document.getElementById('v-'+x).style.display=(x===v?(x==='map'?'flex':'block'):'none'));
  if(v==='map'&&map)setTimeout(()=>map.invalidateSize(),60);
  if(v==='home')renderHome();if(v==='rank')renderRank();if(v==='compare')renderCompare();if(v==='persona')renderPersona();
});

function renderHome(){
  const avg=(F.reduce((s,f)=>s+(nliW(f.properties)||0),0)/F.length).toFixed(1);
  const gd={};F.forEach(f=>{const g=gradeOf(f.properties);gd[g]=(gd[g]||0)+1});
  const bs=F.filter(f=>isBlind(f.properties,'NLI')).length;
  document.getElementById('kpis').innerHTML=
   `<div class="kpi"><b>${F.length.toLocaleString()}</b><span>분석 읍면동</span></div>
    <div class="kpi"><b>${avg}</b><span>평균 지수</span></div>
    <div class="kpi"><b>${gd.S||0}</b><span>S등급 · 상위 10%</span></div>
    <div class="kpi"><b style="color:var(--terra)">${bs}</b><span>종합 사각지대</span></div>`;
  const sd={};F.forEach(f=>{const s=f.properties.sido;(sd[s]=sd[s]||[]).push(nliW(f.properties)||0)});
  const sarr=Object.entries(sd).map(([k,v])=>[k,v.reduce((a,b)=>a+b,0)/v.length]).sort((a,b)=>b[1]-a[1]);
  document.getElementById('sidoBars').innerHTML=sarr.map(([k,v])=>`<div class="barrow"><span class="nm">${k}</span><span class="bar"><span style="width:${v}%;background:${color(v)}"></span></span><span class="v">${v.toFixed(0)}</span></div>`).join('');
  document.getElementById('gradeBars').innerHTML=['S','A','B','C','D'].map(g=>{const n=gd[g]||0,pc=100*n/F.length;return `<div class="barrow"><span class="nm">${g}등급</span><span class="bar"><span style="width:${pc}%;background:${GC[g]}"></span></span><span class="v">${n}</span></div>`}).join('');
  const sorted=F.slice().sort((a,b)=>nliW(b.properties)-nliW(a.properties));
  const card=p=>`<div class="place" onclick="goDetail('${p.adm_nm}')"><span>${fullN(p)}</span><span><b>${nliW(p)}</b> <span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></span></div>`;
  document.getElementById('homeTop').innerHTML=sorted.slice(0,5).map(f=>card(f.properties)).join('');
  document.getElementById('homeBot').innerHTML=sorted.slice(-5).reverse().map(f=>card(f.properties)).join('');
}

let map,layer,mMetric='NLI',mMode='basic',popmin=0;
function initMap(){
  map=L.map('map',{preferCanvas:true}).setView([36.3,127.8],7);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'&copy; OpenStreetMap &copy; CARTO',maxZoom:19}).addTo(map);
  layer=L.geoJSON(DATA,{style:mStyle,onEachFeature:(f,l)=>{f.properties._l=l;l.on('mouseover',()=>l.setStyle({weight:1.6,color:'#16232e'}));l.on('mouseout',()=>layer.resetStyle(l));l.on('click',()=>showDetail(f.properties))}}).addTo(map);
  const sel=document.getElementById('metric');for(const k in METRICS){let o=document.createElement('option');o.value=k;o.text=METRICS[k];sel.add(o)}
  sel.onchange=e=>{mMetric=e.target.value;mRedraw()};
  document.querySelectorAll('#modes button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#modes button').forEach(x=>x.classList.remove('on'));b.classList.add('on');mMode=b.dataset.m;mRedraw()});
  document.getElementById('popmin').oninput=e=>{popmin=+e.target.value;document.getElementById('popval').textContent=popmin?popmin.toLocaleString()+'+':'전체';layer.setStyle(mStyle)};
  mRedraw();initPoints();
}
const PT_TYPES={em:['응급의료','#c0392b'],cl:['의료기관','#3f8fa8'],ph:['약국','#2f6b4e'],sc:['학교','#5b6bd0'],pk:['공원','#6f9e86'],ev:['전기차','#d4a056']};
let ptOn={},ptLayer;const MINZ=12;
function initPoints(){
  ptLayer=L.layerGroup().addTo(map);
  document.getElementById('ptToggles').innerHTML=Object.entries(PT_TYPES).map(([t,v])=>`<label style="display:inline-flex;align-items:center;gap:5px;margin:3px 9px 3px 0;font-size:12px;cursor:pointer;color:var(--mid)"><input type="checkbox" data-t="${t}"><span style="width:9px;height:9px;border-radius:50%;background:${v[1]};display:inline-block"></span>${v[0]}</label>`).join('');
  document.querySelectorAll('#ptToggles input').forEach(c=>c.onchange=()=>{ptOn[c.dataset.t]=c.checked;drawPoints()});
  map.on('moveend zoomend',drawPoints);drawPoints();
}
function drawPoints(){
  if(!ptLayer)return;ptLayer.clearLayers();
  const hint=document.getElementById('ptHint');
  if(!Object.values(ptOn).some(Boolean)){hint.textContent='시설을 선택하면 지도에 표시됩니다.';return}
  if(map.getZoom()<MINZ){hint.textContent=`더 확대하세요 (레벨 ${MINZ}+ · 현재 ${map.getZoom()})`;return}
  const b=map.getBounds(),CAP=6000;let drawn=0,trunc=false;
  for(const t in PT_TYPES){if(!ptOn[t])continue;const arr=POINTS[t]||[],col=PT_TYPES[t][1];
    for(const p of arr){if(p[1]<b.getSouth()||p[1]>b.getNorth()||p[0]<b.getWest()||p[0]>b.getEast())continue;
      if(drawn>=CAP){trunc=true;break}
      L.circleMarker([p[1],p[0]],{radius:4,weight:.8,color:'#fff',fillColor:col,fillOpacity:.92}).addTo(ptLayer);drawn++;}
    if(trunc)break;}
  hint.textContent=`화면 내 ${drawn.toLocaleString()}개 표시`+(trunc?' · 더 확대하면 전부 보여요':'');
}
function mStyle(f){const p=f.properties,sc=metricVal(p,mMetric);
  if(popmin>0&&(p.pop_total||0)<popmin)return{fillColor:'#e3dccb',weight:.15,color:'#ccc',fillOpacity:.1};
  if(mMode==='blind'){const b=isBlind(p,mMetric);return{fillColor:b?'#bb3a24':'#e8e0d0',weight:b?.7:.15,color:b?'#6e1f10':'#d8cdb8',fillOpacity:b?.92:.3}}
  if(mMode==='pop')return{fillColor:color(sc),weight:.2,color:'#c9bda3',fillOpacity:.12+.8*popPct(p.pop_total||0)};
  return{fillColor:color(sc),weight:.3,color:'#cabd9f',fillOpacity:.82};}
function mRedraw(){if(!layer)return;layer.setStyle(mStyle);mLegend();
  const t={basic:'선택 지표를 백분위 색으로 표시',blind:'인구 '+BS_POP.toLocaleString()+'명↑ 인데 「'+METRICS[mMetric]+'」 하위 '+BS_SCORE+'% → 빨강',pop:'인구 많을수록 진하게, 빈 지역은 흐리게'};
  document.getElementById('modeDesc').textContent=t[mMode];}
function mLegend(){const el=document.getElementById('legend');
  if(mMode==='blind'){el.innerHTML='<div><i style="background:#bb3a24"></i>사각지대</div><div><i style="background:#e8e0d0"></i>해당 없음</div>';return}
  el.innerHTML=[[80,'상위 80–100'],[65,'65–80'],[50,'50–65'],[35,'35–50'],[20,'20–35'],[0,'하위 0–20']].map(b=>`<div><i style="background:${color(b[0])}"></i>${b[1]}</div>`).join('');}
function detailHTML(p){
  const isf=fav.includes(p.adm_nm);
  let h=`<span class="close" onclick="document.getElementById('detail').style.display='none'">✕</span>
   <h4>${fullN(p)} <span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span> <span class="heart" onclick="toggleFav('${p.adm_nm}')">${isf?'♥':'♡'}</span></h4>
   <div class="muted">${p.cohort} · 인구 ${(p.pop_total||0).toLocaleString()}명 ${isBlind(p,'NLI')?'· <span class="warn">사각지대</span>':''}</div>
   <div style="margin:10px 0"><b>종합 지수 ${nliW(p)}</b><div class="bar"><span style="width:${nliW(p)}%;background:${color(nliW(p))}"></span></div></div>`;
  for(const d in DOMFAC){let v=p['score_'+d];if(v==null)continue;
    h+=`<div class="dom"><div class="hd"><span>${METRICS[d]}</span><span style="color:${color(v)}">${v}</span></div><div class="bar"><span style="width:${v}%;background:${color(v)}"></span></div>`;
    for(const fac of DOMFAC[d]){let c=fac[0],label=fac[1],hn=fac[2],n=p[c+'_c'],near=p[c+'_n'];let cnt=(n===0)?'<span class="warn">0개 ⚠</span>':((n||0).toLocaleString()+'개');h+=`<div class="ev">· ${label} ${cnt}${hn?(' · 최근접 '+(n===0?'—':dist(near)+walk(near))):''}</div>`}
    h+=`</div>`}
  h+=`<div style="margin-top:14px"><button class="btn" onclick="addCmp('${p.adm_nm}')">⊕ 비교담기</button></div>`;
  return h;}
function showDetail(p){const d=document.getElementById('detail');d.innerHTML=detailHTML(p);d.style.display='block';if(p._l)map.fitBounds(p._l.getBounds())}
function goDetail(adm){const f=F.find(x=>x.properties.adm_nm===adm);if(!f)return;document.querySelector('nav .tab[data-v=map]').click();showDetail(f.properties)}

function renderRank(){
  const rm=document.getElementById('rankMetric');if(!rm.options.length){for(const k in METRICS){if(k==='grade')continue;let o=document.createElement('option');o.value=k;o.text=METRICS[k];rm.add(o)}rm.onchange=renderRank;}
  const rs=document.getElementById('rankSido');if(!rs.options.length){rs.innerHTML='<option value="">전국</option>'+[...new Set(F.map(f=>f.properties.sido))].sort().map(s=>`<option>${s}</option>`).join('');rs.onchange=renderRank;}
  document.getElementById('rankCohort').onchange=renderRank;
  const m=rm.value||'NLI',sido=rs.value,coh=document.getElementById('rankCohort').value;
  let arr=F.filter(f=>(!sido||f.properties.sido===sido)&&(!coh||f.properties.cohort===coh));
  arr.sort((a,b)=>(metricVal(b.properties,m)-metricVal(a.properties,m)));
  document.getElementById('rankCount').textContent=arr.length.toLocaleString()+'개';
  let rows=arr.slice(0,300).map((f,i)=>{const p=f.properties;
    return `<tr data-adm="${p.adm_nm}"><td class="n">${i+1}</td><td>${fullN(p)}</td><td><span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></td>
      <td class="n"><b>${metricVal(p,m)}</b></td>${DOMS.map(d=>`<td class="n" style="color:${color(p['score_'+d])}">${p['score_'+d]==null?'–':p['score_'+d]}</td>`).join('')}
      <td><span style="cursor:pointer" onclick="event.stopPropagation();addCmp('${p.adm_nm}')">⊕</span> <span class="heart" onclick="event.stopPropagation();toggleFav('${p.adm_nm}',1)">${fav.includes(p.adm_nm)?'♥':'♡'}</span></td></tr>`}).join('');
  document.getElementById('rankTable').innerHTML=`<thead><tr><th>#</th><th>지역</th><th>등급</th><th>${METRICS[m]}</th>${DOMS.map(d=>`<th>${METRICS[d].slice(0,2)}</th>`).join('')}<th></th></tr></thead><tbody>${rows}</tbody>`;
  document.querySelectorAll('#rankTable tbody tr').forEach(tr=>tr.onclick=()=>goDetail(tr.dataset.adm));
}

function addCmp(adm){if(cmp.includes(adm))return;if(cmp.length>=4){alert('최대 4곳까지 비교할 수 있어요');return}cmp.push(adm);document.querySelector('nav .tab[data-v=compare]').click();}
function renderCompare(){
  document.getElementById('cmpClear').onclick=()=>{cmp=[];renderCompare()};
  const b=document.getElementById('compareBody');
  if(!cmp.length){b.innerHTML='<div class="card muted">비교할 지역이 없습니다. 위 검색창이나 순위·지도에서 ⊕로 담으세요.</div>';return}
  const ps=cmp.map(a=>F.find(f=>f.properties.adm_nm===a).properties);
  const best=d=>Math.max(...ps.map(p=>d==='NLI'?nliW(p):p['score_'+d]));
  const rowHead=`<tr><th>항목</th>${ps.map(p=>`<th>${fullN(p)}<br><span class="muted">${p.cohort}·${(p.pop_total||0).toLocaleString()}명</span> <span style="cursor:pointer" onclick="cmp=cmp.filter(x=>x!=='${p.adm_nm}');renderCompare()">✕</span></th>`).join('')}</tr>`;
  const cell=(p,d)=>{const v=d==='NLI'?nliW(p):p['score_'+d];const bst=v===best(d);return `<td class="n" style="${bst?'background:#e4f0e8;font-weight:800':''}">${v==null?'–':v}</td>`};
  let rows=`<tr><td><b>종합 지수</b></td>${ps.map(p=>cell(p,'NLI')).join('')}</tr>`;
  rows+=`<tr><td>등급</td>${ps.map(p=>`<td><span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></td>`).join('')}</tr>`;
  DOMS.forEach(d=>rows+=`<tr><td>${METRICS[d]}</td>${ps.map(p=>cell(p,d)).join('')}</tr>`);
  [['ph','약국'],['cl','의료기관'],['st','상가'],['pk','공원'],['bs','버스'],['cc','CCTV']].forEach(fac=>rows+=`<tr><td class="muted">${fac[1]} 수</td>${ps.map(p=>`<td class="n">${(p[fac[0]+'_c']||0).toLocaleString()}</td>`).join('')}</tr>`);
  b.innerHTML=`<div class="card" style="padding:0;overflow:auto"><table>${rowHead}${rows}</table></div>`;
}

function renderPersona(){
  document.getElementById('presets').innerHTML=Object.keys(PRESETS).map(k=>`<button class="btn" onclick="setPreset('${k}')">${k}</button>`).join('');
  document.getElementById('sliders').innerHTML=DOMS.map((d,i)=>`<div class="rng"><label>${METRICS[d]}</label><input type="range" min="0" max="3" step="0.1" value="${W[i]}" oninput="W[${i}]=+this.value;this.nextElementSibling.textContent=(+this.value).toFixed(1);personaLive()"><b>${W[i].toFixed(1)}</b></div>`).join('');
  document.getElementById('resetW').onclick=()=>{W=[1,1,1,1,1,1,1];renderPersona();personaLive()};
  personaTop();
}
function setPreset(k){W=PRESETS[k].slice();renderPersona();personaLive()}
function personaTop(){recompRank();
  const sorted=F.slice().sort((a,b)=>nliW(b.properties)-nliW(a.properties)).slice(0,15);
  document.getElementById('personaTop').innerHTML=sorted.map((f,i)=>{const p=f.properties;return `<div class="place" onclick="goDetail('${p.adm_nm}')"><span>${i+1}. ${fullN(p)}</span><span><b>${nliW(p)}</b> <span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></span></div>`}).join('')}
function personaLive(){recompRank();personaTop();if(layer)layer.setStyle(mStyle)}

function toggleFav(adm,re){const i=fav.indexOf(adm);if(i<0)fav.push(adm);else fav.splice(i,1);localStorage.setItem('nli_fav',JSON.stringify(fav));
  if(document.getElementById('detail').style.display==='block'){const f=F.find(x=>x.properties.adm_nm===adm);if(f)document.getElementById('detail').innerHTML=detailHTML(f.properties)}if(re)renderRank();}
document.getElementById('foot1').textContent='데이터 · 공공데이터포털 표준데이터 / SGIS 경계·인구(2025 2Q) / 건강보험심사평가원 / 소상공인시장진흥공단   ·   방법 · 시설밀도(인구 1만명당)와 근접성의 백분위 혼합, 도농 코호트·인구가중 중심점 보정   ·   7개 도메인 MVP · 점수는 전국 상대평가로 참고용입니다';
recompRank();initMap();renderHome();
attachAC(document.getElementById('gsearch'),document.getElementById('gac'),goDetail);
attachAC(document.getElementById('cmpSearch'),document.getElementById('cmpac'),adm=>{addCmp(adm)});
</script></body></html>'''

html = TEMPLATE.replace("__GEOJSON__", geojson).replace("__POINTS__", points)
open("nli_map.html", "w", encoding="utf-8").write(html)
print("생성 nli_map.html |", round(os.path.getsize("nli_map.html")/1e6, 1), "MB")
