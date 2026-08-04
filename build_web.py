"""동네살기지수 NLI — 배포용 SPA 대시보드 빌더 (모던 디자인 + 자동완성).
입력: data/processed/nli_map.geojson · 출력: nli_map.html(경계 인라인) + nli_points.json(옆 파일, 지연로딩)
재생성: ./venv/bin/python build_web.py
"""
import os, shutil

geojson = open("data/processed/nli_map.geojson", encoding="utf-8").read()
# 시설포인트(11MB)는 인라인하지 않고 배포 산출물 옆에 두어 지연로딩(fetch). 초기 로딩 경량화.

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
 table.heat td,table.heat th{padding:5px 7px;border:2px solid #fff;font-size:11px;text-align:center}table.heat{border-collapse:separate}
 .g{display:inline-flex;align-items:center;justify-content:center;min-width:24px;height:24px;border-radius:7px;color:#fff;font-weight:700;font-size:12px;padding:0 5px}
 select,input[type=text]{padding:9px 12px;border:1px solid var(--line);border-radius:11px;font-size:13px;background:#fff;font-family:var(--sans);color:var(--ink);transition:.15s}
 select:focus,input:focus{outline:none;border-color:var(--sky)}
 button.btn{padding:8px 15px;border:1px solid var(--line);background:#fff;border-radius:999px;cursor:pointer;font-size:13px;font-family:var(--sans);color:var(--ink);font-weight:500;transition:.15s}
 button.btn:hover{border-color:var(--sage);color:var(--sage);background:#f4f8f5}
 button.btn.on{background:var(--ocean);color:#fff;border-color:var(--ocean);font-weight:600}
 aside{width:262px;background:#faf8f4;border-right:1px solid var(--line);overflow-y:auto;padding:11px 13px;flex-shrink:0}
 aside::-webkit-scrollbar{width:5px}
 aside .sec{margin-bottom:9px;padding-bottom:9px;border-bottom:1px solid var(--line)}
 aside .sec:last-child{border-bottom:0;margin-bottom:0;padding-bottom:0}
 aside h3{margin:0 0 6px;font-size:10.5px;letter-spacing:.07em;color:var(--terra);text-transform:uppercase;font-weight:700}
 aside select{width:100%;padding:6px 9px}
 .fld{font-size:11px;color:var(--mid);font-weight:600;margin-bottom:4px}
 .wpanel{background:#fff;border:1px solid var(--line);border-radius:10px;padding:8px 9px;margin-top:2px}
 .msliders{margin:6px 0 5px}
 .msliders .rng{margin:0;gap:7px}.msliders .rng label{width:50px;font-size:11px;color:var(--ink)}.msliders .rng input{flex:1;height:3px}.msliders .rng b{width:20px;font-size:10.5px}
 button.btn.ghost{width:100%;font-size:11.5px;padding:4px;color:var(--mid);border-radius:8px}
 .seg{display:flex;background:var(--line2);border-radius:10px;padding:3px;gap:2px}
 .seg button{flex:1;padding:6px 3px;border:0;background:transparent;border-radius:8px;font-size:12px;cursor:pointer;font-family:var(--sans);color:var(--mid);font-weight:500;transition:.15s}
 .seg button.on{background:#fff;color:var(--ocean);font-weight:700;box-shadow:var(--sh)}
 #map{flex:1}
 .legend{display:grid;grid-template-columns:1fr 1fr;gap:1px 8px}
 .legend i{width:10px;height:10px;display:inline-block;margin-right:6px;vertical-align:-1px;border-radius:3px}.legend div{font-size:10.5px;color:var(--mid);white-space:nowrap}
 .detail{position:absolute;top:18px;right:18px;z-index:900;width:320px;max-height:calc(100% - 36px);overflow:auto;background:#fff;border-radius:var(--r-lg);box-shadow:var(--sh2);padding:20px;font-size:13px;border:1px solid var(--line)}
 .detail h4{margin:0 0 4px;font-size:20px;color:var(--ink);font-weight:700;letter-spacing:-.02em;line-height:1.2}
 .muted{color:var(--mid);font-size:12px}
 .bar{height:8px;background:var(--line2);border-radius:5px;overflow:hidden;margin:4px 0}.bar>span{display:block;height:100%;border-radius:5px}
 .dom{margin-top:10px;padding-top:10px;border-top:1px solid var(--line2)}.dom .hd{display:flex;justify-content:space-between;font-weight:600;font-size:13px}
 .ev{font-size:12px;color:var(--mid);margin-top:2px}.warn{color:var(--terra);font-weight:700}
 .close{float:right;cursor:pointer;color:var(--light);font-size:18px;line-height:1}
 .rng{display:flex;align-items:center;gap:10px;margin:7px 0}.rng label{width:84px;font-size:12px;color:var(--mid)}.rng input{flex:1}.rng b{width:26px;text-align:right;font-size:12px;color:var(--ocean);font-weight:700}
 .heart{cursor:pointer;font-size:15px;color:var(--terra)}
 .ptchip{display:inline-flex;align-items:center;gap:5px;padding:4px 9px;margin:2px 3px 2px 0;border:1px solid var(--line);border-radius:999px;font-size:11.5px;cursor:pointer;color:var(--mid);background:#fff;transition:.13s;user-select:none}
 .ptchip:hover{border-color:var(--sage);color:var(--sage)}
 .ptchip.on{background:var(--ocean);color:#fff;border-color:var(--ocean);font-weight:600}
 .ptchip .dot{width:10px;height:10px;border-radius:50%;display:inline-block;flex-shrink:0}
 .foot{color:var(--light);font-size:11px;padding:20px 30px;text-align:center;border-top:1px solid var(--line);line-height:1.8}
 .flex{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
 input[type=range]{accent-color:var(--ocean);height:4px}
 ::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:#d9d1c3;border-radius:10px;border:2px solid var(--bg)}
 /* 커스텀 셀렉트 (네이티브 select 대체) */
 .csel{position:relative;display:inline-block;min-width:132px;vertical-align:middle}
 aside .csel,.wpanel .csel{display:block;width:100%;min-width:0}
 .csel-trig{width:100%;padding:8px 30px 8px 11px;border:1px solid var(--line);border-radius:9px;background:#fff;font-size:13px;cursor:pointer;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:border-color .15s,box-shadow .15s;font-family:var(--sans)}
 .csel-trig::after{content:'';position:absolute;right:13px;top:47%;width:7px;height:7px;border-right:1.6px solid var(--light);border-bottom:1.6px solid var(--light);transform:translateY(-50%) rotate(45deg);transition:transform .22s}
 .csel:hover .csel-trig{border-color:var(--sage)}
 .csel.open .csel-trig{border-color:var(--sky);box-shadow:0 0 0 3px rgba(63,143,168,.12)}
 .csel.open .csel-trig::after{transform:translateY(-20%) rotate(-135deg)}
 .csel-pan{position:absolute;top:calc(100% + 5px);left:0;right:0;min-width:100%;background:#fff;border:1px solid var(--line);border-radius:11px;box-shadow:var(--sh2);z-index:1500;max-height:300px;overflow:auto;padding:5px;opacity:0;transform:translateY(-8px) scale(.98);transform-origin:top;pointer-events:none;transition:opacity .17s ease,transform .17s cubic-bezier(.22,1,.36,1)}
 .csel.open .csel-pan{opacity:1;transform:none;pointer-events:auto}
 .csel-it{padding:8px 11px;border-radius:7px;font-size:13px;cursor:pointer;color:var(--ink);white-space:nowrap;transition:background .12s}
 .csel-it:hover{background:var(--line2)}.csel-it.on{background:var(--ocean);color:#fff;font-weight:600}
 .ac-none{padding:11px 13px;font-size:13px;color:var(--mid);text-align:center}
 .csel-it.on::before{content:'✓ '}
 /* 반응형 애니메이션 */
 @keyframes vin{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
 @keyframes pop{0%{transform:scale(1)}40%{transform:scale(1.35)}100%{transform:scale(1)}}
 .bar>span,.barrow .bar>span{transition:width .6s cubic-bezier(.22,1,.36,1),background .3s}
 .gbar{transition:height .6s cubic-bezier(.22,1,.36,1),width .6s cubic-bezier(.22,1,.36,1),background .3s}
 .rng b.bump{animation:pop .35s ease}
 .detail{animation:vin .22s cubic-bezier(.22,1,.36,1)}
 .kpi,.card{transition:box-shadow .2s,transform .2s}.card:hover{box-shadow:var(--sh2)}
 .place{transition:background .12s,transform .12s}.place:hover{transform:translateX(2px)}
 /* 통계 정렬(데스크탑 균형) */
 #scatter{text-align:center}
 #corrHeat{overflow-x:auto}
 .card>.flex{align-items:center}
 /* 반응형 */
 @media(max-width:960px){
   .grid2{grid-template-columns:1fr}
   .wrap{padding:22px 18px 46px}
   .hero-t{font-size:30px}h2{font-size:21px}
 }
 .asideToggle{display:none}
 @media(max-width:820px){
   .view.map{position:relative}
   aside{position:absolute;top:0;bottom:0;left:0;z-index:1200;width:84%;max-width:300px;transform:translateX(-102%);transition:transform .26s cubic-bezier(.22,1,.36,1);box-shadow:var(--sh2)}
   aside.open{transform:none}
   .asideToggle{display:inline-flex;align-items:center;gap:6px;position:absolute;top:12px;left:12px;z-index:1150;padding:8px 14px;border:1px solid var(--line);background:#fff;border-radius:999px;box-shadow:var(--sh);font-size:12.5px;font-weight:600;color:var(--ocean);cursor:pointer;font-family:var(--sans)}
   #asideBackdrop{position:absolute;inset:0;z-index:1180;background:rgba(30,26,20,.32);opacity:0;pointer-events:none;transition:opacity .26s}
   #asideBackdrop.on{opacity:1;pointer-events:auto}
 }
 @media(max-width:640px){
   .kpis{grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:20px}
   .kpi{padding:15px}.kpi b{font-size:26px}
   .card{padding:16px}
   .wrap{padding:18px 13px 40px}.hero-t{font-size:26px}
   nav{padding:0 10px;gap:1px;overflow-x:auto}
   nav::-webkit-scrollbar{display:none}
   nav .brand{font-size:15px;margin-right:6px}nav .brand small{display:none}
   nav .tab{padding:7px 9px;font-size:12.5px;flex-shrink:0}
   nav .gsearch{flex-shrink:0}nav .gsearch input{width:130px}nav .gsearch input:focus{width:150px}
 }
</style></head><body>
<div id="app">
 <nav>
   <div class="logo">🏘</div><div class="brand">동네살기지수<small>NLI</small></div>
   <div class="tab on" data-v="map">지도</div>
   <div class="tab" data-v="home">홈</div>
   <div class="tab" data-v="rank">순위</div>
   <div class="tab" data-v="compare">비교</div>
   <div class="tab" data-v="persona">맞춤설정</div>
   <div class="tab" data-v="stats">통계</div>
   <div class="gsearch"><input id="gsearch" placeholder="지역 검색 (예: 강남구 역삼)" autocomplete="off"><div class="ac" id="gac"></div></div>
   <button class="btn" id="shareBtn" title="현재 화면 링크 복사" style="margin-left:8px;flex-shrink:0">🔗 공유</button>
 </nav>

 <div class="view" id="v-home" style="display:none"><div class="wrap">
   <div class="hero-t">어디가 살기 좋은 동네일까</div>
   <div class="sub">공공데이터 표준 300종을 읍면동 단위로 융합한 살기좋은동네 지수 · 전국 3,553개 읍면동 · 8개 도메인</div>
   <div class="kpis" id="kpis"></div>
   <div class="grid2">
     <div class="card"><h3>시도별 평균 지수</h3><div id="sidoBars"></div></div>
     <div class="card"><h3>등급 분포</h3><div id="gradeBars"></div>
       <h3 style="margin-top:20px">전국 상위</h3><div id="homeTop"></div>
       <h3 style="margin-top:16px">전국 하위</h3><div id="homeBot"></div></div>
   </div>
 </div><div class="foot" id="foot1"></div></div>

 <div class="view map" id="v-map" style="display:flex">
   <button class="asideToggle" id="asideToggle" aria-label="필터 열기">☰ 지표·필터</button>
   <aside>
     <div class="sec"><h3>지표</h3>
       <select id="metric"></select>
       <div class="seg" id="modes" style="margin-top:8px">
         <button data-m="basic" class="on">기본</button><button data-m="blind">사각지대</button><button data-m="pop">인구대비</button></div>
       <div class="muted" id="modeDesc" style="margin-top:7px"></div></div>

     <div class="sec"><h3>가중치 · 페르소나</h3>
       <div class="wpanel">
         <select id="mpersona"></select>
         <div id="mSliders" class="msliders"></div>
         <button class="btn ghost" id="mReset">균등으로 초기화</button></div></div>

     <div class="sec"><h3>필터 · 레이어</h3>
       <div class="fld">인구 (최소)</div>
       <div class="flex"><input type="range" id="popmin" min="0" max="50000" step="1000" value="0" style="flex:1"><span id="popval" style="font-size:12px;width:52px;text-align:right;color:var(--mid)">전체</span></div>
       <div class="fld" style="margin-top:12px">시설 표시 <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0">— 확대 시</span></div>
       <div id="ptToggles"></div><div class="muted" id="ptHint" style="margin-top:5px"></div></div>

     <div class="sec"><h3>범례</h3><div class="legend" id="legend"></div></div>
   </aside>
   <div id="asideBackdrop"></div>
   <div id="map"></div>
   <div class="detail" id="detail" style="display:none"></div>
 </div>

 <div class="view" id="v-rank" style="display:none"><div class="wrap">
   <h2>지역 순위</h2><div class="sub">테마·시도·유형을 골라 정렬하세요. 행 클릭 → 상세, ⊕ → 비교담기, ♡ → 관심</div>
   <div class="flex" style="margin-bottom:10px">
     <select id="rankMetric"></select><select id="rankSido"></select>
     <select id="rankCohort"><option value="">전체 유형</option><option>도시</option><option>도농복합</option><option>농촌</option></select>
     <span class="muted" id="rankCount"></span></div>
   <div class="flex" style="margin-bottom:16px;position:relative;background:#faf8f4;border:1px solid var(--line);border-radius:12px;padding:9px 12px">
     <span style="font-size:12px;color:var(--terra);font-weight:700">🚇 통근 보정</span>
     <input type="text" id="rankBase" placeholder="기준지(출발지) 입력 (예: 역삼동)" style="width:230px" autocomplete="off"><div class="ac" id="rankbac" style="left:130px;top:46px;right:auto"></div>
     <span id="commuteInfo" class="muted"></span>
     <span id="commuteKmWrap" style="display:none;align-items:center;gap:7px;font-size:12px;color:var(--mid)">이내 <input type="range" id="commuteKm" min="2" max="40" step="1" value="10" style="width:120px"><b id="commuteKmV" style="color:var(--ocean);font-weight:700">10km</b>
     <button class="btn" id="commuteClear" style="padding:4px 12px">해제</button></span></div>
   <div class="card" style="padding:0;max-height:64vh;overflow:auto"><table id="rankTable"></table></div>
 </div></div>

 <div class="view" id="v-compare" style="display:none"><div class="wrap">
   <h2>지역 비교 <span class="muted" style="font-size:14px;font-weight:400">최대 4곳</span></h2>
   <div class="sub">검색으로 추가하거나 순위·지도에서 ⊕로 담으세요. 각 행에서 가장 좋은 값은 초록으로 강조됩니다.</div>
   <div class="flex" style="margin-bottom:16px;position:relative"><input type="text" id="cmpSearch" placeholder="지역 추가 (예: 노형동)" style="width:280px" autocomplete="off"><div class="ac" id="cmpac" style="left:0;top:44px;right:auto"></div><button class="btn" id="cmpClear">비우기</button></div>
   <div id="compareBody"></div>
 </div></div>

 <div class="view" id="v-stats" style="display:none"><div class="wrap">
   <h2>지역 통계·추론</h2><div class="sub">지역 특성(인구·밀도·연령)과 살기지수의 관계, 지역 유형별 격차 분석 (실시간 계산)</div>
   <div class="kpis" id="statKpi"></div>
   <div class="card"><h3>지역 특성 × 도메인 상관</h3>
     <div class="muted" style="margin-bottom:12px">인구·밀도·연령구조가 각 도메인 점수와 어떻게 연관되는지 · <b style="color:#2f6b4e">초록=정비례(+)</b> / <b style="color:#b0603f">주황=반비례(−)</b> · |r|≥0.3부터 뚜렷</div>
     <div id="regHeat"></div></div>
   <div class="grid2" style="margin-top:18px">
     <div class="card"><h3>도농 유형별 도메인 점수</h3>
       <div class="flex" style="justify-content:space-between;margin-bottom:10px"><span class="muted">도시·도농복합·농촌 평균 (막대 길수록 높음)</span>
         <div class="seg" style="width:210px"><button data-ck="cohort" class="on">행정동명 기준</button><button data-ck="cohort_d">인구밀도 기준</button></div></div>
       <div id="cohortBars"></div></div>
     <div class="card"><h3>시도별 종합지수 순위</h3><div class="muted" style="margin-bottom:12px">17개 시도 평균 종합지수</div><div id="sidoRank"></div></div>
   </div>
   <div class="card" style="margin-top:18px"><h3>산점도 · 회귀분석 <span class="muted" style="font-weight:400">— 지역 특성과 지표 관계</span></h3>
     <div class="flex" style="margin:10px 0 12px;font-size:13px;color:var(--mid)">X축 <select id="sx"></select> Y축 <select id="sy"></select> <span id="regInfo"></span></div>
     <div id="scatter"></div>
     <div id="scatterNote" style="margin-top:12px;text-align:center;font-size:13.5px;color:var(--ink)"></div></div>
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
let POINTS=null;   // 시설포인트(11MB)는 첫 토글 시 nli_points.json 지연로딩(초기 로딩 경량화)
const F=DATA.features;
const DOMS=['D1','D2','D3','D4','D5','D6','D7','D8'];
const METRICS={NLI:'종합 지수',D1:'의료·건강',D2:'교육·보육',D3:'생활편의·상업',D4:'문화·여가·체육',D5:'교통·이동',D6:'안전',D7:'환경·기후',D8:'복지·돌봄',grade:'등급'};
const DOMFAC={D1:[['ph','약국',1],['cl','의료기관',1],['em','응급의료기관',1]],D2:[['sc','학교',1],['cd','어린이집',1],['lb','도서관',1]],D3:[['st','상가',0],['bg','대규모점포',1],['gs','주유소',1]],D4:[['pk','공원',1],['sp','체육시설',1],['mu','박물관·미술관',1],['th','공연장',1],['cn','영화상영관',1]],D5:[['bs','버스정류장',1],['pg','주차장',1],['bk','자전거보관소',1]],D6:[['cc','CCTV',1],['cz','어린이보호구역',1],['sb','안전비상벨',1]],D7:[['ev','전기차충전소',1],['ht','무더위쉼터',1]],D8:[['wf','사회복지시설',1]]};
const GC={S:'#2f6b4e',A:'#6f9e86',B:'#d4a056',C:'#cf8a5c',D:'#b0603f'};
// 페르소나 프리셋 (D1의료 D2교육 D3생활편의 D4문화여가 D5교통 D6안전 D7환경 D8복지)
// 객관 가중(정보량/CRITIC)은 weight_analysis.py 산출값(균등=1.0 기준). 데이터 분산 기반이라 '참고용' 프리셋.
const PRESETS={
 '균등':[1,1,1,1,1,1,1,1],
 '정보량(엔트로피)':[1.40,0.89,0.78,0.67,0.77,0.61,0.72,2.16],
 'CRITIC(중복보정)':[1.02,0.89,0.98,0.70,0.86,0.93,0.98,1.64],
 '중요도(AHP)':[2.15,0.89,0.34,0.34,0.89,2.15,0.34,0.89],
 '영유아 양육':[1.4,2,1,1.3,1,1.6,1,1.2],
 '고령':[2,1,1.2,1.2,1.4,1.2,1.3,2],
 '1인 청년':[1,1,2,1.5,1.5,1,1,1],
 '반려동물':[1,1,1,2,1,1.2,1.3,1],
 '신혼·예비부모':[1.3,1.5,1.2,1,1.2,1.6,1.1,1],
 '학군·자녀교육':[1,2,1,1.3,1.1,1.5,1,1],
 '직장인 통근':[1,1,1.4,1.1,2,1,1,1],
 '건강·웰니스':[2,1,1,1.3,1,1,1.6,1.3],
 '문화·여가족':[1,1,1.4,2,1.3,1,1,1]};
// 연령구조 기반 동네 추천 페르소나 (전국평균: 영유아2.5%·유소년10.5%·고령19.5%)
function recPersona(p){if((p.r_inf!=null&&p.r_inf>=0.045)||(p.r_yth!=null&&p.r_yth>=0.16))return '영유아 양육';if(p.r_eld!=null&&p.r_eld>=0.40)return '고령';return null}
let W=[1,1,1,1,1,1,1,1];
let fav=JSON.parse(localStorage.getItem('nli_fav')||'[]');
let cmp=[];
let curDetail=null, applyingHash=false;   // 공유 딥링크: 현재 선택 동 / 복원 중 재기록 방지

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
    if(!ms.length){box.innerHTML='<div class="ac-none">검색 결과가 없습니다</div>';box.style.display='block';return}
    box.innerHTML=ms.map(p=>`<div class="ac-item" data-adm="${p.adm_nm}"><span>${p.full_nm}</span><span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></div>`).join('');
    box.style.display='block';
    box.querySelectorAll('.ac-item').forEach(it=>it.onclick=()=>{box.style.display='none';input.value='';onPick(it.dataset.adm)});});
  input.addEventListener('keydown',e=>{if(e.key==='Enter'){const first=box.querySelector('.ac-item[data-adm]');const q=input.value.trim();if(!q)return;const f=first?F.find(x=>x.properties.adm_nm===first.dataset.adm):F.find(x=>(x.properties.full_nm||'').includes(q));
    if(f){box.style.display='none';input.value='';onPick(f.properties.adm_nm)}
    else{box.innerHTML='<div class="ac-none">‘'+q+'’ 검색 결과가 없습니다</div>';box.style.display='block';}}
    if(e.key==='Escape')box.style.display='none';});
  document.addEventListener('click',e=>{if(!input.parentElement.contains(e.target))box.style.display='none'});
}

document.querySelectorAll('nav .tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('nav .tab').forEach(x=>x.classList.remove('on'));t.classList.add('on');
  const v=t.dataset.v;['home','map','rank','compare','persona','stats'].forEach(x=>document.getElementById('v-'+x).style.display=(x===v?(x==='map'?'flex':'block'):'none'));
  if(v!=='map'){const el=document.getElementById('v-'+v);el.style.animation='none';void el.offsetWidth;el.style.animation='vin .3s cubic-bezier(.22,1,.36,1)';}
  if(v==='map'&&map){setTimeout(()=>map.invalidateSize(),60);renderMapSliders();}
  if(v==='home')renderHome();if(v==='rank')renderRank();if(v==='compare')renderCompare();if(v==='persona')renderPersona();if(v==='stats')renderStats();
  writeHash();
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
  document.getElementById('sidoBars').innerHTML=sarr.map(([k,v])=>`<div class="barrow"><span class="nm">${k}</span><span class="bar"><span data-w="${v.toFixed(1)}" style="width:0;background:${color(v)}"></span></span><span class="v">${v.toFixed(0)}</span></div>`).join('');
  document.getElementById('gradeBars').innerHTML=['S','A','B','C','D'].map(g=>{const n=gd[g]||0,pc=100*n/F.length;return `<div class="barrow"><span class="nm">${g}등급</span><span class="bar"><span data-w="${pc.toFixed(1)}" style="width:0;background:${GC[g]}"></span></span><span class="v">${n}</span></div>`}).join('');
  const sorted=F.slice().sort((a,b)=>nliW(b.properties)-nliW(a.properties));
  const card=p=>`<div class="place" onclick="goDetail('${p.adm_nm}')"><span>${fullN(p)}</span><span><b>${nliW(p)}</b> <span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></span></div>`;
  document.getElementById('homeTop').innerHTML=sorted.slice(0,5).map(f=>card(f.properties)).join('');
  document.getElementById('homeBot').innerHTML=sorted.slice(-5).reverse().map(f=>card(f.properties)).join('');
  growBars();
}

let map,layer,mMetric='NLI',mMode='basic',popmin=0;
function initMap(){
  map=L.map('map',{preferCanvas:true,zoomSnap:0.25}).setView([36.55,127.75],7.6);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'&copy; OpenStreetMap &copy; CARTO',maxZoom:19}).addTo(map);
  layer=L.geoJSON(DATA,{style:mStyle,onEachFeature:(f,l)=>{f.properties._l=l;l.on('mouseover',()=>l.setStyle({weight:1.6,color:'#16232e'}));l.on('mouseout',()=>layer.resetStyle(l));l.on('click',()=>showDetail(f.properties))}}).addTo(map);
  const sel=document.getElementById('metric');for(const k in METRICS){let o=document.createElement('option');o.value=k;o.text=METRICS[k];sel.add(o)}
  sel.onchange=e=>{mMetric=e.target.value;mRedraw()};
  const mp=document.getElementById('mpersona');
  {let o=document.createElement('option');o.value='';o.text='직접 조정';mp.add(o);}
  for(const k in PRESETS){let o=document.createElement('option');o.value=k;o.text=k;mp.add(o)}
  mp.onchange=e=>{if(e.target.value){setPreset(e.target.value);mMetric='NLI';sel.value='NLI';mRedraw();}};
  document.getElementById('mReset').onclick=()=>{W=[1,1,1,1,1,1,1,1];mp.value='균등';renderMapSliders();mMetric='NLI';sel.value='NLI';recompRank();mRedraw();};
  renderMapSliders();
  document.querySelectorAll('#modes button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#modes button').forEach(x=>x.classList.remove('on'));b.classList.add('on');mMode=b.dataset.m;mRedraw()});
  document.getElementById('popmin').oninput=e=>{popmin=+e.target.value;document.getElementById('popval').textContent=popmin?popmin.toLocaleString()+'+':'전체';layer.setStyle(mStyle)};
  mRedraw();initPoints();
}
const PT_TYPES={em:['응급의료','#c0392b'],ph:['약국','#2f6b4e'],sc:['학교','#5b6bd0'],pk:['공원','#6f9e86'],ev:['전기차','#d4a056'],wf:['사회복지','#8e5db0']};
let ptOn={},ptLayer;const MINZ=12;
function initPoints(){
  ptLayer=L.layerGroup().addTo(map);
  document.getElementById('ptToggles').innerHTML=Object.entries(PT_TYPES).map(([t,v])=>`<span class="ptchip" data-t="${t}"><span class="dot" style="background:${v[1]}"></span>${v[0]}</span>`).join('');
  document.querySelectorAll('.ptchip').forEach(c=>c.onclick=async()=>{const t=c.dataset.t;ptOn[t]=!ptOn[t];c.classList.toggle('on',ptOn[t]);if(ptOn[t])await ensurePoints();drawPoints()});
  map.on('moveend zoomend',drawPoints);drawPoints();
}
function ensurePoints(){   // 시설포인트 지연로딩(첫 토글 시 1회). 실패 시(로컬 file://) 안내.
  if(POINTS)return Promise.resolve(true);
  const hint=document.getElementById('ptHint');if(hint)hint.textContent='시설 데이터 불러오는 중…';
  return fetch('nli_points.json').then(r=>{if(!r.ok)throw 0;return r.json()}).then(j=>{POINTS=j;return true})
    .catch(()=>{POINTS={};if(hint)hint.textContent='시설 데이터를 불러오지 못했습니다(로컬 미리보기는 http 서버 필요).';return false});
}
function drawPoints(){
  if(!ptLayer)return;ptLayer.clearLayers();
  const hint=document.getElementById('ptHint');
  if(!Object.values(ptOn).some(Boolean)){hint.textContent='시설을 선택하면 지도에 표시됩니다.';return}
  if(map.getZoom()<MINZ){hint.textContent=`더 확대하세요 (레벨 ${MINZ}+ · 현재 ${map.getZoom()})`;return}
  const b=map.getBounds(),CAP=6000;let drawn=0,trunc=false;
  for(const t in PT_TYPES){if(!ptOn[t])continue;const o=(POINTS&&POINTS[t])||{p:[],n:[]},col=PT_TYPES[t][1],tn=PT_TYPES[t][0];
    for(let i=0;i<o.p.length;i++){const p=o.p[i];
      if(p[1]<b.getSouth()||p[1]>b.getNorth()||p[0]<b.getWest()||p[0]>b.getEast())continue;
      if(drawn>=CAP){trunc=true;break}
      const nm=o.n[i]||'',ad=(o.a&&o.a[i])||'',tel=(o.t&&o.t[i])||'',cat=(o.c&&o.c[i])||'';
      L.circleMarker([p[1],p[0]],{radius:5,weight:1.2,color:'#fff',fillColor:col,fillOpacity:.95})
        .bindTooltip('<b>'+tn+'</b> · '+nm,{direction:'top',offset:[0,-4]})
        .bindPopup(`<div style="font-size:13px;min-width:150px"><b style="font-size:14px">${nm}</b><br>
          <span style="color:${col};font-weight:600">${tn}${cat?' · '+cat:''}</span>
          ${ad?'<br>📍 '+ad:''}${tel?'<br>☎ <a href="tel:'+tel+'">'+tel+'</a>':''}</div>`)
        .addTo(ptLayer);drawn++;}
    if(trunc)break;}
  hint.textContent=`화면 내 ${drawn.toLocaleString()}개 표시`+(trunc?' · 더 확대하면 전부 보여요':'');
}
function mStyle(f){const p=f.properties,sc=metricVal(p,mMetric);
  if(popmin>0&&(p.pop_total||0)<popmin)return{fillColor:'#e3dccb',weight:.15,color:'#ccc',fillOpacity:.06};
  if(mMode==='blind'){const b=isBlind(p,mMetric);return{fillColor:b?'#bb3a24':'#e8e0d0',weight:b?.6:.12,color:b?'#8a2a18':'#d8cdb8',fillOpacity:b?.72:.14}}
  if(mMode==='pop')return{fillColor:color(sc),weight:.2,color:'#c9bda3',fillOpacity:.06+.42*popPct(p.pop_total||0)};
  return{fillColor:color(sc),weight:.3,color:'#c3b79d',fillOpacity:.32};}
const SHORT={D1:'의료',D2:'교육',D3:'생활편의',D4:'문화여가',D5:'교통',D6:'안전',D7:'환경',D8:'복지'};
function renderMapSliders(){const el=document.getElementById('mSliders');if(!el)return;
  el.innerHTML=DOMS.map((d,i)=>`<div class="rng"><label>${SHORT[d]}</label><input type="range" min="0" max="3" step="0.1" value="${W[i]}" oninput="W[${i}]=+this.value;this.nextElementSibling.textContent=(+this.value).toFixed(1);onWeightChange()"><b>${W[i].toFixed(1)}</b></div>`).join('');
}
function onWeightChange(){   // 슬라이더 드래그 → 지도 실시간 재색칠
  const mp=document.getElementById('mpersona'); if(mp)mp.value='';   // 직접 조정 상태로
  mMetric='NLI'; const s=document.getElementById('metric'); if(s)s.value='NLI';
  recompRank(); if(layer)layer.setStyle(mStyle); mLegend(); writeHash();
}
function mRedraw(){if(!layer)return;layer.setStyle(mStyle);mLegend();
  const t={basic:'선택 지표를 백분위 색으로 표시',blind:'인구 '+BS_POP.toLocaleString()+'명↑ 인데 「'+METRICS[mMetric]+'」 하위 '+BS_SCORE+'% → 빨강',pop:'인구 많을수록 진하게, 빈 지역은 흐리게'};
  document.getElementById('modeDesc').textContent=t[mMode];writeHash();}
function mLegend(){const el=document.getElementById('legend');
  if(mMode==='blind'){el.innerHTML='<div><i style="background:#bb3a24"></i>사각지대</div><div><i style="background:#e8e0d0"></i>해당 없음</div>';return}
  el.innerHTML=[[80,'상위 80–100'],[65,'65–80'],[50,'50–65'],[35,'35–50'],[20,'20–35'],[0,'하위 0–20']].map(b=>`<div><i style="background:${color(b[0])}"></i>${b[1]}</div>`).join('');}
function detailHTML(p){
  const isf=fav.includes(p.adm_nm);
  let h=`<span class="close" onclick="document.getElementById('detail').style.display='none';curDetail=null;writeHash()">✕</span>
   <h4>${fullN(p)} <span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span> <span class="heart" onclick="toggleFav('${p.adm_nm}')">${isf?'♥':'♡'}</span></h4>
   <div class="muted">${p.cohort} · 인구 ${(p.pop_total||0).toLocaleString()}명 ${isBlind(p,'NLI')?'· <span class="warn">사각지대</span>':''}</div>
   ${(()=>{const rp=recPersona(p);return rp?`<div style="margin-top:5px;font-size:12px">👤 이 동네 추천: <b>${rp}</b> <span style="cursor:pointer;color:var(--sky);text-decoration:underline" onclick="setPreset('${rp}');document.querySelector('nav .tab[data-v=persona]').click()">적용</span></div>`:''})()}
   <div style="margin:10px 0"><b>종합 지수 ${nliW(p)}</b><div class="bar"><span data-w="${nliW(p)}" style="width:0;background:${color(nliW(p))}"></span></div></div>`;
  for(const d in DOMFAC){let v=p['score_'+d];if(v==null)continue;
    h+=`<div class="dom"><div class="hd"><span>${METRICS[d]}</span><span style="color:${color(v)}">${v}</span></div><div class="bar"><span data-w="${v}" style="width:0;background:${color(v)}"></span></div>`;
    for(const fac of DOMFAC[d]){let c=fac[0],label=fac[1],hn=fac[2],n=p[c+'_c'],near=p[c+'_n'];let cnt=(n===0)?'<span class="warn">0개 ⚠</span>':((n||0).toLocaleString()+'개');h+=`<div class="ev">· ${label} ${cnt}${hn?(' · 최근접 '+(n===0?'—':dist(near)+walk(near))):''}</div>`}
    h+=`</div>`}
  h+=`<div style="margin-top:14px"><button class="btn" onclick="addCmp('${p.adm_nm}')">⊕ 비교담기</button></div>`;
  return h;}
function showDetail(p){const d=document.getElementById('detail');d.innerHTML=detailHTML(p);d.style.display='block';growBars();curDetail=p.adm_nm;writeHash();
  if(p._l&&map){map.invalidateSize();const b=p._l.getBounds();if(b&&b.isValid())map.fitBounds(b,{maxZoom:13,padding:[24,24]});}}
function goDetail(adm){const f=F.find(x=>x.properties.adm_nm===adm);if(!f)return;document.querySelector('nav .tab[data-v=map]').click();showDetail(f.properties)}

// 통근 보정 — 기준지 중심점(clat/clon)에서 직선거리(도로 라우팅은 향후) 이내로 좁혀 NLI 순 제시
let commuteBase=null, commuteKm=10, cohortKey='cohort';
function hav(a,b,c,d){const R=6371,r=Math.PI/180,dLa=(c-a)*r,dLo=(d-b)*r;const s=Math.sin(dLa/2)**2+Math.cos(a*r)*Math.cos(c*r)*Math.sin(dLo/2)**2;return 2*R*Math.asin(Math.sqrt(s));}
function renderRank(){
  const rm=document.getElementById('rankMetric');if(!rm.options.length){for(const k in METRICS){if(k==='grade')continue;let o=document.createElement('option');o.value=k;o.text=METRICS[k];rm.add(o)}rm.onchange=renderRank;}
  const rs=document.getElementById('rankSido');if(!rs.options.length){rs.innerHTML='<option value="">전국</option>'+[...new Set(F.map(f=>f.properties.sido))].sort().map(s=>`<option>${s}</option>`).join('');rs.onchange=renderRank;}
  document.getElementById('rankCohort').onchange=renderRank;
  const m=rm.value||'NLI',sido=rs.value,coh=document.getElementById('rankCohort').value;
  let arr=F.filter(f=>(!sido||f.properties.sido===sido)&&(!coh||f.properties.cohort===coh));
  // 통근 보정: 기준지 반경 내로 필터 + 거리 부여
  const bf=commuteBase?F.find(f=>f.properties.adm_nm===commuteBase):null, cOn=!!(bf&&bf.properties.clat!=null);
  if(cOn){const bp=bf.properties;
    arr=arr.filter(f=>{const p=f.properties;if(p.clat==null)return false;p._km=hav(bp.clat,bp.clon,p.clat,p.clon);return p._km<=commuteKm;});}
  arr.sort((a,b)=>(metricVal(b.properties,m)-metricVal(a.properties,m)));
  document.getElementById('rankCount').textContent=arr.length.toLocaleString()+'개'+(cOn?` · ${commuteBase} 반경 ${commuteKm}km`:'');
  let rows=arr.slice(0,300).map((f,i)=>{const p=f.properties;
    return `<tr data-adm="${p.adm_nm}"><td class="n">${i+1}</td><td>${fullN(p)}</td>${cOn?`<td class="n" style="color:var(--terra);font-weight:700">${p._km.toFixed(1)}km</td>`:''}<td><span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></td>
      <td class="n"><b>${metricVal(p,m)}</b></td>${DOMS.map(d=>`<td class="n" style="color:${color(p['score_'+d])}">${p['score_'+d]==null?'–':p['score_'+d]}</td>`).join('')}
      <td><span style="cursor:pointer" onclick="event.stopPropagation();addCmp('${p.adm_nm}')">⊕</span> <span class="heart" onclick="event.stopPropagation();toggleFav('${p.adm_nm}',1)">${fav.includes(p.adm_nm)?'♥':'♡'}</span></td></tr>`}).join('');
  document.getElementById('rankTable').innerHTML=`<thead><tr><th>#</th><th>지역</th>${cOn?'<th>거리</th>':''}<th>등급</th><th>${METRICS[m]}</th>${DOMS.map(d=>`<th>${METRICS[d].slice(0,2)}</th>`).join('')}<th></th></tr></thead><tbody>${rows}</tbody>`;
  document.querySelectorAll('#rankTable tbody tr').forEach(tr=>tr.onclick=()=>goDetail(tr.dataset.adm));
}
function setCommuteBase(adm){commuteBase=adm;
  document.getElementById('commuteInfo').innerHTML=`<b style="color:var(--ocean)">${adm}</b> 기준 ·`;
  document.getElementById('commuteKmWrap').style.display='inline-flex';renderRank();writeHash();}

function addCmp(adm){if(cmp.includes(adm))return;if(cmp.length>=4){alert('최대 4곳까지 비교할 수 있어요');return}cmp.push(adm);document.querySelector('nav .tab[data-v=compare]').click();}
function renderCompare(){
  document.getElementById('cmpClear').onclick=()=>{cmp=[];renderCompare()};
  const b=document.getElementById('compareBody');
  if(!cmp.length){b.innerHTML='<div class="card muted">비교할 지역이 없습니다. 위 검색창이나 순위·지도에서 ⊕로 담으세요.</div>';writeHash();return}
  const ps=cmp.map(a=>F.find(f=>f.properties.adm_nm===a).properties);
  const best=d=>Math.max(...ps.map(p=>d==='NLI'?nliW(p):p['score_'+d]));
  const rowHead=`<tr><th>항목</th>${ps.map(p=>`<th>${fullN(p)}<br><span class="muted">${p.cohort}·${(p.pop_total||0).toLocaleString()}명</span> <span style="cursor:pointer" onclick="cmp=cmp.filter(x=>x!=='${p.adm_nm}');renderCompare()">✕</span></th>`).join('')}</tr>`;
  const cell=(p,d)=>{const v=d==='NLI'?nliW(p):p['score_'+d];const bst=v===best(d);return `<td class="n" style="${bst?'background:#e4f0e8;font-weight:800':''}">${v==null?'–':v}</td>`};
  let rows=`<tr><td><b>종합 지수</b></td>${ps.map(p=>cell(p,'NLI')).join('')}</tr>`;
  rows+=`<tr><td>등급</td>${ps.map(p=>`<td><span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></td>`).join('')}</tr>`;
  DOMS.forEach(d=>rows+=`<tr><td>${METRICS[d]}</td>${ps.map(p=>cell(p,d)).join('')}</tr>`);
  [['ph','약국'],['cl','의료기관'],['st','상가'],['pk','공원'],['bs','버스'],['cc','CCTV']].forEach(fac=>rows+=`<tr><td class="muted">${fac[1]} 수</td>${ps.map(p=>`<td class="n">${(p[fac[0]+'_c']||0).toLocaleString()}</td>`).join('')}</tr>`);
  b.innerHTML=`<div class="card" style="padding:0;overflow:auto"><table>${rowHead}${rows}</table></div>`;
  writeHash();
}

function renderPersona(){
  document.getElementById('presets').innerHTML=Object.keys(PRESETS).map(k=>`<button class="btn" onclick="setPreset('${k}')">${k}</button>`).join('');
  document.getElementById('sliders').innerHTML=DOMS.map((d,i)=>`<div class="rng"><label>${METRICS[d]}</label><input type="range" min="0" max="3" step="0.1" value="${W[i]}" oninput="W[${i}]=+this.value;this.nextElementSibling.textContent=(+this.value).toFixed(1);personaLive()"><b>${W[i].toFixed(1)}</b></div>`).join('');
  document.getElementById('resetW').onclick=()=>{W=[1,1,1,1,1,1,1,1];renderPersona();personaLive()};
  personaTop();
}
function setPreset(k){W=PRESETS[k].slice();const mp=document.getElementById('mpersona');if(mp&&PRESETS[k])mp.value=k;renderPersona();renderMapSliders();personaLive()}
function personaTop(){recompRank();
  const sorted=F.slice().sort((a,b)=>nliW(b.properties)-nliW(a.properties)).slice(0,15);
  document.getElementById('personaTop').innerHTML=sorted.map((f,i)=>{const p=f.properties;return `<div class="place" onclick="goDetail('${p.adm_nm}')"><span>${i+1}. ${fullN(p)}</span><span><b>${nliW(p)}</b> <span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span></span></div>`}).join('')}
function personaLive(){recompRank();personaTop();if(layer)layer.setStyle(mStyle);writeHash()}

/* ---------- 지역 통계 탭 (지역 특성 × 도메인 중심) ---------- */
const DKEYS=['D1','D2','D3','D4','D5','D6','D7','D8'];
const REG=[['dens','인구밀도'],['pop','인구'],['eld','고령비중'],['yth','유소년비중'],['apt','아파트비율'],['old','노후주택비율']];
const VARS={dens:'인구밀도(로그)',pop:'인구(로그)',eld:'고령비중%',yth:'유소년%',inf:'영유아%',apt:'아파트비율%',old:'노후주택비율%',NLI:'종합지수',D1:'의료',D2:'교육',D3:'생활편의',D4:'문화여가',D5:'교통',D6:'안전',D7:'환경',D8:'복지'};
const SP=F.map(f=>f.properties);
function sval(p,k){
  if(k==='NLI')return nliW(p);
  if(k==='dens')return p.dens!=null?Math.log10(1+p.dens):null;
  if(k==='pop')return p.pop_total!=null?Math.log10(1+p.pop_total):null;
  if(k==='eld')return p.r_eld!=null?p.r_eld*100:null;
  if(k==='yth')return p.r_yth!=null?p.r_yth*100:null;
  if(k==='inf')return p.r_inf!=null?p.r_inf*100:null;
  if(k==='apt')return p.r_apt!=null?p.r_apt*100:null;
  if(k==='old')return p.r_old!=null?p.r_old*100:null;
  return p['score_'+k];
}
function pearson(xs,ys){let n=0,sx=0,sy=0,sxx=0,syy=0,sxy=0;for(let i=0;i<xs.length;i++){const a=xs[i],b=ys[i];if(a==null||b==null||isNaN(a)||isNaN(b))continue;n++;sx+=a;sy+=b;sxx+=a*a;syy+=b*b;sxy+=a*b;}if(n<2)return NaN;const c=sxy-sx*sy/n;return c/Math.sqrt((sxx-sx*sx/n)*(syy-sy*sy/n));}
function ols(xs,ys){const px=[],py=[];for(let i=0;i<xs.length;i++){const a=xs[i],b=ys[i];if(a!=null&&b!=null&&!isNaN(a)&&!isNaN(b)){px.push(a);py.push(b);}}const n=px.length,sx=px.reduce((s,v)=>s+v,0),sy=py.reduce((s,v)=>s+v,0),sxx=px.reduce((s,v)=>s+v*v,0),sxy=px.reduce((s,v,i)=>s+v*py[i],0);const sl=(n*sxy-sx*sy)/(n*sxx-sx*sx),ic=(sy-sl*sx)/n,r=pearson(px,py);return{slope:sl,intercept:ic,r2:r*r,r,n};}
function corrColor(r){const a=Math.min(1,Math.abs(r)),c=r>=0?[47,107,78]:[176,96,63];return `rgba(${c[0]},${c[1]},${c[2]},${(.1+.85*a).toFixed(2)})`;}
function renderStats(){
  const cmean=(f,d)=>{const v=SP.filter(f).map(p=>p['score_'+d]).filter(x=>x!=null);return v.reduce((a,b)=>a+b,0)/(v.length||1)};
  const avgNLI=SP.reduce((s,p)=>s+(nliW(p)||0),0)/SP.length;
  const dkAll=[...DKEYS,'NLI'];
  const dvAll=dkAll.map(d=>d==='NLI'?SP.map(p=>nliW(p)):SP.map(p=>p['score_'+d]));
  const regV=REG.map(([rk])=>SP.map(p=>sval(p,rk)));
  const eldMed=pearson(regV[2],dvAll[0]);       // 고령 ↔ 의료
  const gap=cmean(p=>p.cohort==='도시','D1')/cmean(p=>p.cohort==='농촌','D1');
  // 최강 지역특성×도메인 상관
  let best=['',0];REG.forEach(([rk,rn],ri)=>dkAll.forEach((d,di)=>{const r=pearson(regV[ri],dvAll[di]);if(Math.abs(r)>Math.abs(best[1]))best=[rn+'↔'+VARS[d],r];}));
  document.getElementById('statKpi').innerHTML=
    `<div class="kpi"><b>${avgNLI.toFixed(1)}</b><span>평균 종합지수</span></div>
     <div class="kpi"><b style="color:#b0603f">${eldMed.toFixed(2)}</b><span>고령비중 ↔ 의료</span></div>
     <div class="kpi"><b>${gap.toFixed(1)}배</b><span>의료 도농격차(도시/농촌)</span></div>
     <div class="kpi"><b style="color:${best[1]>=0?'#2f6b4e':'#b0603f'}">${best[1]>=0?'+':''}${best[1].toFixed(2)}</b><span>최강 지역상관 · ${best[0]}</span></div>`;

  // 지역 특성 × 도메인 상관 히트맵
  let ht='<table class="heat"><tr><th></th>'+dkAll.map(d=>`<th>${VARS[d]}</th>`).join('')+'</tr>';
  REG.forEach(([rk,rn],ri)=>{ht+=`<tr><td style="font-weight:700;background:#f7f5f1;text-align:left;white-space:nowrap">${rn}</td>`+dvAll.map((dv,di)=>{const r=pearson(regV[ri],dv);return `<td style="background:${corrColor(r)};color:${Math.abs(r)>=.5?'#fff':'#1a2530'};${Math.abs(r)>=.3?'font-weight:700':''}">${r.toFixed(2)}</td>`}).join('')+'</tr>';});
  document.getElementById('regHeat').innerHTML=ht+'</table>';

  // 도농 유형별 도메인 점수 — 가로 그룹 막대(값 라벨). 코호트 기준 토글(행정동명/인구밀도, M6)
  const coh=[['도시','#6f9e86'],['도농복합','#d4a056'],['농촌','#cf8a5c']];
  const drawCohort=()=>{document.getElementById('cohortBars').innerHTML=DKEYS.map(d=>{
    const rows=coh.map(([c,col])=>{const m=cmean(p=>p[cohortKey]===c,d);return `<div style="display:flex;align-items:center;gap:6px;margin:1px 0"><span style="width:52px;font-size:10px;color:var(--mid);text-align:right">${c}</span><div style="flex:1;background:var(--line2);border-radius:3px;height:11px"><div class="gbar" data-w="${m.toFixed(0)}" style="width:0;height:100%;background:${col};border-radius:3px"></div></div><span style="width:22px;font-size:10.5px;font-weight:700;text-align:right">${m.toFixed(0)}</span></div>`}).join('');
    return `<div style="margin-bottom:10px"><div style="font-size:12px;font-weight:600;color:var(--ink);margin-bottom:3px">${VARS[d]}</div>${rows}</div>`;
  }).join('');growBars();};
  document.querySelectorAll('[data-ck]').forEach(b=>b.onclick=()=>{cohortKey=b.dataset.ck;document.querySelectorAll('[data-ck]').forEach(x=>x.classList.toggle('on',x===b));drawCohort();});
  drawCohort();

  // 시도별 종합지수 순위
  const sd={};SP.forEach(p=>{(sd[p.sido]=sd[p.sido]||[]).push(nliW(p)||0)});
  const sarr=Object.entries(sd).map(([k,v])=>[k,v.reduce((a,b)=>a+b,0)/v.length]).sort((a,b)=>b[1]-a[1]);
  document.getElementById('sidoRank').innerHTML=sarr.map(([k,v])=>`<div style="display:flex;align-items:center;gap:8px;font-size:12px;margin:3px 0"><span style="width:100px;text-align:right;color:var(--mid);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${k}</span><div style="flex:1;background:var(--line2);border-radius:4px;height:13px"><div class="gbar" data-w="${v.toFixed(0)}" style="width:0;height:100%;background:${color(v)};border-radius:4px"></div></div><span style="width:28px;font-weight:700">${v.toFixed(0)}</span></div>`).join('');

  const opts=['dens','pop','eld','yth','inf','apt','old','NLI',...DKEYS];
  const sx=document.getElementById('sx'),sy=document.getElementById('sy');
  if(!sx.options.length){opts.forEach(k=>{sx.add(new Option(VARS[k],k));sy.add(new Option(VARS[k],k));});sx.value='dens';sy.value='D1';sx.onchange=drawScatter;sy.onchange=drawScatter;}
  drawScatter();growBars();
}
function drawScatter(){
  const xk=document.getElementById('sx').value,yk=document.getElementById('sy').value;
  const pts=SP.map(p=>[sval(p,xk),sval(p,yk)]).filter(a=>a[0]!=null&&a[1]!=null&&!isNaN(a[0])&&!isNaN(a[1]));
  const xs=pts.map(a=>a[0]),ys=pts.map(a=>a[1]),r=ols(xs,ys);
  const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
  const W=560,H=280,pad=36,sxp=v=>pad+(v-xmin)/(xmax-xmin||1)*(W-2*pad),syp=v=>H-pad-(v-ymin)/(ymax-ymin||1)*(H-2*pad);
  const samp=pts.length>1500?pts.filter((_,i)=>i%Math.ceil(pts.length/1500)===0):pts;
  let svg=`<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" style="width:100%;max-width:760px;background:#fdfcfa;border-radius:8px">`;
  svg+=`<line x1="${pad}" y1="${H-pad}" x2="${W-pad}" y2="${H-pad}" stroke="#ddd"/><line x1="${pad}" y1="${pad}" x2="${pad}" y2="${H-pad}" stroke="#ddd"/>`;
  svg+=samp.map(a=>`<circle cx="${sxp(a[0]).toFixed(1)}" cy="${syp(a[1]).toFixed(1)}" r="1.7" fill="#2f6b4e" opacity=".3"/>`).join('');
  svg+=`<line x1="${sxp(xmin).toFixed(1)}" y1="${syp(r.intercept+r.slope*xmin).toFixed(1)}" x2="${sxp(xmax).toFixed(1)}" y2="${syp(r.intercept+r.slope*xmax).toFixed(1)}" stroke="#c0392b" stroke-width="2.2"/>`;
  svg+=`<text x="${W/2}" y="${H-9}" font-size="11" text-anchor="middle" fill="#5b6b77">${VARS[xk]} →</text>`;
  svg+=`<text x="13" y="${H/2}" font-size="11" fill="#5b6b77" text-anchor="middle" transform="rotate(-90 13 ${H/2})">↑ ${VARS[yk]}</text>`;
  document.getElementById('scatter').innerHTML=svg+'</svg>';
  document.getElementById('regInfo').innerHTML=`&nbsp; <b>R² ${r.r2.toFixed(2)}</b> · n=${r.n.toLocaleString()}`;
  const R=r.r||0,ar=Math.abs(R);
  const mag=ar<0.1?'뚜렷한 관계가 거의 없':ar<0.3?'약한 관계가 있':ar<0.5?'뚜렷한 관계가 있':'강한 관계가 있';
  const dir=R>=0?`높을수록 <b>${VARS[yk]}</b>도 높아지는`:`높을수록 <b>${VARS[yk]}</b>는 낮아지는`;
  document.getElementById('scatterNote').innerHTML=`<b>${VARS[xk]}</b>가 ${dir} ${mag}습니다 &nbsp;(r=${R.toFixed(2)})`;
  writeHash();
}

function toggleFav(adm,re){const i=fav.indexOf(adm);if(i<0)fav.push(adm);else fav.splice(i,1);localStorage.setItem('nli_fav',JSON.stringify(fav));
  if(document.getElementById('detail').style.display==='block'){const f=F.find(x=>x.properties.adm_nm===adm);if(f)document.getElementById('detail').innerHTML=detailHTML(f.properties)}if(re)renderRank();}
/* 커스텀 셀렉트: 네이티브 select를 감싸 숨기고 스타일 드롭다운으로 대체(옵션은 실시간 반영) */
function customSelect(sel){
  if(sel._cs)return; sel._cs=1;
  const wrap=document.createElement('div');wrap.className='csel';
  sel.parentNode.insertBefore(wrap,sel);wrap.appendChild(sel);sel.style.display='none';
  const trig=document.createElement('div');trig.className='csel-trig';wrap.appendChild(trig);
  const pan=document.createElement('div');pan.className='csel-pan';wrap.appendChild(pan);
  const sync=()=>{trig.textContent=(sel.options[sel.selectedIndex]||{}).text||'';};
  const build=()=>{pan.innerHTML='';[...sel.options].forEach(o=>{const it=document.createElement('div');it.className='csel-it'+(o.value===sel.value?' on':'');it.textContent=o.text;it.onclick=e=>{e.stopPropagation();sel.value=o.value;sync();wrap.classList.remove('open');sel.dispatchEvent(new Event('change'));};pan.appendChild(it);});};
  trig.onclick=e=>{e.stopPropagation();const op=wrap.classList.contains('open');document.querySelectorAll('.csel.open').forEach(x=>x.classList.remove('open'));if(!op){build();wrap.classList.add('open');}};
  new MutationObserver(sync).observe(sel,{childList:true});
  sel.addEventListener('change',sync);sync();
}
document.addEventListener('click',()=>document.querySelectorAll('.csel.open').forEach(x=>x.classList.remove('open')));
/* 막대 성장 애니메이션: data-w(%너비)/data-h(%높이) → 다음 프레임에 목표값 적용 */
function growBars(){requestAnimationFrame(()=>{document.querySelectorAll('[data-w]').forEach(e=>{e.style.width=e.dataset.w+'%';e.removeAttribute('data-w');});document.querySelectorAll('[data-h]').forEach(e=>{e.style.height=e.dataset.h+'%';e.removeAttribute('data-h');});});}
document.getElementById('foot1').textContent='데이터 · 공공데이터포털 표준데이터 / SGIS 경계·인구(2025 2Q) / 건강보험심사평가원 / 소상공인시장진흥공단   ·   방법 · 시설밀도(인구 1만명당)와 근접성의 백분위 혼합, 도농 코호트·인구가중 중심점 보정   ·   8개 도메인 읍면동 정밀(복지는 지오코딩 85% 커버) · 점수는 전국 상대평가로 참고용입니다';
/* ---------- 공유 딥링크: 현재 상태 ↔ location.hash ---------- */
function curTab(){const t=document.querySelector('nav .tab.on');return t?t.dataset.v:'map';}
function writeHash(){if(applyingHash)return;
  const q=[],v=curTab();if(v!=='map')q.push('v='+v);
  if(curDetail)q.push('d='+encodeURIComponent(curDetail));
  if(W.some(x=>Math.abs(x-1)>1e-6))q.push('w='+W.map(x=>+(+x).toFixed(2)).join(','));
  if(mMetric&&mMetric!=='NLI')q.push('m='+mMetric);
  if(mMode&&mMode!=='basic')q.push('md='+mMode);
  if(commuteBase){q.push('cb='+encodeURIComponent(commuteBase));q.push('ck='+commuteKm);}
  const sx=document.getElementById('sx'),sy=document.getElementById('sy');
  if(sx&&sy&&sx.value&&!(sx.value==='dens'&&sy.value==='D1')){q.push('sx='+sx.value);q.push('sy='+sy.value);}
  if(cmp.length)q.push('c='+cmp.map(encodeURIComponent).join('~'));
  const h=q.join('&');
  try{history.replaceState(null,'',h?('#'+h):(location.pathname+location.search));}catch(e){}
}
function applyHash(){
  const raw=(location.hash||'').replace(/^#/,'');if(!raw)return;
  const P={};raw.split('&').forEach(kv=>{const i=kv.indexOf('=');if(i>0){try{P[kv.slice(0,i)]=decodeURIComponent(kv.slice(i+1));}catch(e){}}});
  applyingHash=true;
  try{
    if(P.w){const a=P.w.split(',').map(Number);if(a.length===8&&a.every(x=>!isNaN(x))){for(let i=0;i<8;i++)W[i]=a[i];recompRank();}}
    if(P.m)mMetric=P.m;
    if(P.md)mMode=P.md;
    if(P.cb){commuteBase=P.cb;commuteKm=+P.ck||10;}
    if(P.c)cmp=P.c.split('~').filter(Boolean).slice(0,4);
    const v=P.d?'map':(P.v||'map');
    const tb=document.querySelector('nav .tab[data-v='+v+']');if(tb)tb.click();
    if(P.md)document.querySelectorAll('#modes button').forEach(x=>x.classList.toggle('on',x.dataset.m===P.md));
    const ms=document.getElementById('metric');if(ms){ms.value=mMetric;ms.dispatchEvent(new Event('change'));}
    if(P.cb){const ci=document.getElementById('commuteInfo');if(ci){ci.innerHTML='<b style="color:var(--ocean)">'+P.cb+'</b> 기준 ·';document.getElementById('commuteKmWrap').style.display='inline-flex';document.getElementById('commuteKm').value=commuteKm;document.getElementById('commuteKmV').textContent=commuteKm+'km';}if(v==='rank')renderRank();}
    if(P.sx){const sx=document.getElementById('sx'),sy=document.getElementById('sy');if(sx&&sx.onchange){sx.value=P.sx;if(P.sy&&sy)sy.value=P.sy;sx.dispatchEvent(new Event('change'));}}
    if(P.d){const f=F.find(x=>x.properties.adm_nm===P.d);if(f)showDetail(f.properties);}
  }catch(e){}
  applyingHash=false;
  if(typeof mRedraw==='function')mRedraw();
  writeHash();
}
recompRank();initMap();renderHome();
attachAC(document.getElementById('gsearch'),document.getElementById('gac'),goDetail);
attachAC(document.getElementById('cmpSearch'),document.getElementById('cmpac'),adm=>{addCmp(adm)});
attachAC(document.getElementById('rankBase'),document.getElementById('rankbac'),setCommuteBase);
document.getElementById('commuteKm').oninput=function(){commuteKm=+this.value;document.getElementById('commuteKmV').textContent=commuteKm+'km';renderRank();writeHash();};
document.getElementById('commuteClear').onclick=()=>{commuteBase=null;document.getElementById('commuteInfo').innerHTML='';document.getElementById('commuteKmWrap').style.display='none';document.getElementById('rankBase').value='';renderRank();writeHash();};
document.querySelectorAll('select').forEach(customSelect);
// 모바일 사이드바 접이식
(function(){const as=document.querySelector('#v-map aside'),bd=document.getElementById('asideBackdrop'),tg=document.getElementById('asideToggle');
  const close=()=>{as.classList.remove('open');bd.classList.remove('on')};
  tg.onclick=()=>{const o=as.classList.toggle('open');bd.classList.toggle('on',o)};bd.onclick=close;
  as.addEventListener('change',()=>{if(window.innerWidth<=820)close()});})();
// 공유 버튼: 현재 상태 링크 복사
document.getElementById('shareBtn').onclick=function(){writeHash();const btn=this,u=location.href;
  const ok=()=>{const o=btn.textContent;btn.textContent='✓ 복사됨';setTimeout(()=>btn.textContent=o,1400);};
  if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(u).then(ok,()=>prompt('링크 복사',u));
  else prompt('링크 복사',u);};
applyHash();   // 딥링크로 진입 시 상태 복원
growBars();
setTimeout(()=>{if(map)map.invalidateSize();},120);
</script></body></html>'''

html = TEMPLATE.replace("__GEOJSON__", geojson)
open("nli_map.html", "w", encoding="utf-8").write(html)
# 시설포인트를 산출물 옆(리포 루트)에 복사 → index.html이 fetch('nli_points.json')로 지연로딩
shutil.copy("data/processed/nli_points.json", "nli_points.json")
print("생성 nli_map.html |", round(os.path.getsize("nli_map.html")/1e6, 1), "MB",
      "| nli_points.json", round(os.path.getsize("nli_points.json")/1e6, 1), "MB (지연로딩)")
