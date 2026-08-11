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
<meta name="description" content="공공데이터로 전국 3,559개 읍면동을 9개 생활 도메인 32개 지표로 정량화 · 아파트 실거래가까지 결합한 '살기지수 × 가격' 대시보드">
<meta property="og:type" content="website">
<meta property="og:title" content="동네살기지수 NLI — 어디가 살기 좋은 동네인가">
<meta property="og:description" content="전국 3,559개 읍면동 · 9도메인 30지표 + 아파트 실거래가. 가성비 좋은 동네를 찾아보세요.">
<meta property="og:site_name" content="동네살기지수 NLI">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="동네살기지수 NLI">
<meta name="twitter:description" content="전국 읍면동 살기지수 × 아파트값 · 가성비 동네 찾기">
<meta name="theme-color" content="#173a4b">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ctext y='26' font-size='26'%3E%F0%9F%8F%98%3C/text%3E%3C/svg%3E">

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
 .tabs{display:flex;align-items:center;gap:2px}
 .iseg{display:flex;gap:6px;padding:9px 16px;background:#fff;border-bottom:1px solid var(--line);flex-shrink:0;z-index:90}
 .iseg button{padding:8px 16px;border:1px solid var(--line);background:#fff;border-radius:999px;cursor:pointer;font-size:13px;font-family:var(--sans);color:var(--mid);font-weight:600;transition:.15s}
 .iseg button.on{background:var(--ocean);color:#fff;border-color:var(--ocean)}
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
 .sub{color:var(--mid);font-size:14.5px;margin-bottom:26px;max-width:640px;word-break:keep-all}
 .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:30px}
 .kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--r-lg);padding:20px;box-shadow:var(--sh);position:relative;overflow:hidden}
 .kpi::before{content:"";position:absolute;left:0;top:0;width:100%;height:3px;background:var(--grad);opacity:.85}
 .kpi b{display:block;font-size:36px;font-weight:800;color:var(--ocean);line-height:1.05;letter-spacing:-.02em}
 .kpi span{color:var(--mid);font-size:12.5px;font-weight:500}
 .dkpi{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:16px}
 .recgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
 .grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:var(--r-lg);padding:24px;box-shadow:var(--sh);transition:.2s}
 .domcard{margin-bottom:0}
 .domgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
 .domcell{border:1px solid var(--line);border-radius:14px;padding:14px 15px;cursor:pointer;transition:.16s;background:linear-gradient(180deg,#fff,#fcfbf8)}
 .domcell:hover{border-color:var(--sage);box-shadow:var(--sh2);transform:translateY(-2px)}
 .domhd{display:flex;align-items:center;gap:11px;margin-bottom:9px}
 .domic{width:38px;height:38px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0}
 .domhd b{font-size:14.5px;color:var(--ink);display:block;line-height:1.2}
 .domn{font-size:11.5px;color:var(--mid);font-weight:600}
 .domtags{display:flex;flex-wrap:wrap;gap:5px}
 .domtags span{font-size:11px;color:var(--mid);background:var(--line2);border-radius:6px;padding:3px 8px;white-space:nowrap}
 @media(max-width:820px){.domgrid{grid-template-columns:repeat(2,1fr)}}
 @media(max-width:560px){.domgrid{grid-template-columns:1fr}}
 .valgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
 .valcell{display:flex;justify-content:space-between;align-items:center;border:1px solid var(--line);border-radius:11px;padding:10px 12px;cursor:pointer;transition:.14s;background:linear-gradient(180deg,#fff,#fbfcfb)}
 .valcell:hover{border-color:var(--sage);box-shadow:var(--sh2);transform:translateY(-2px)}
 .valnm{font-size:13px;color:var(--ink)}.valnm span{display:block;font-size:10.5px;color:var(--light);margin-top:1px}
 .valv{text-align:right;font-size:13px;white-space:nowrap}.valv b{color:var(--ocean)}.valv i{display:block;font-style:normal;font-size:11px;color:var(--terra);font-weight:700;margin-top:1px}
 @media(max-width:820px){.valgrid{grid-template-columns:repeat(2,1fr)}}
 @media(max-width:560px){.valgrid,.recgrid{grid-template-columns:1fr}
 #recHouseSeg{flex-wrap:wrap}#recHouseSeg button{flex:1 1 28%;padding:8px 3px}
 .valcell{flex-wrap:wrap;gap:4px}.valcell .valv{margin-left:auto}}
 /* 경로 모달 */
 .rmodal{position:fixed;inset:0;z-index:3000;background:rgba(20,26,20,.42);display:flex;align-items:center;justify-content:center;padding:20px;animation:vin .18s}
 .rmbox{background:#fff;border-radius:var(--r-lg);box-shadow:var(--sh2);width:420px;max-width:100%;max-height:82vh;overflow:auto;padding:20px}
 .rmhd{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
 .rmhd b{font-size:16px;color:var(--ink)}.rmclose{cursor:pointer;color:var(--light);font-size:20px;line-height:1}
 .rmsum{background:var(--line2);border-radius:11px;padding:11px 13px;font-size:13.5px;margin-bottom:14px}
 .rmsum b{color:var(--ocean);font-size:16px}
 .rmleg{display:flex;gap:11px;padding:9px 0;border-bottom:1px solid var(--line2)}
 .rmleg:last-child{border-bottom:0}
 .rmic{width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}
 .rmleg .rmt{font-size:13px;font-weight:600;color:var(--ink)}
 .rmst{font-size:11.5px;color:var(--mid);margin-top:2px}.rmst span{color:var(--light)}
 .rmfoot{font-size:10.5px;color:var(--light);margin-top:12px;text-align:center}
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
 select,input[type=text],input[type=number]{padding:9px 12px;border:1px solid var(--line);border-radius:11px;font-size:13px;background:#fff;font-family:var(--sans);color:var(--ink);transition:.15s}
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
 .maptitle{position:absolute;top:12px;left:50%;transform:translateX(-50%);z-index:500;background:rgba(255,255,255,.95);border:1px solid var(--line);border-radius:999px;padding:6px 15px;font-size:12.5px;font-weight:700;color:var(--ink);box-shadow:0 2px 8px rgba(20,30,40,.1);pointer-events:none;white-space:nowrap}
 .legend i{width:10px;height:10px;display:inline-block;margin-right:6px;vertical-align:-1px;border-radius:3px}.legend div{font-size:10.5px;color:var(--mid);white-space:nowrap}
 .detail{position:absolute;top:18px;right:18px;z-index:900;width:320px;max-height:calc(100% - 36px);overflow:auto;background:#fff;border-radius:var(--r-lg);box-shadow:var(--sh2);padding:20px;font-size:13px;border:1px solid var(--line)}
 .detail h4{margin:0 0 4px;font-size:20px;color:var(--ink);font-weight:700;letter-spacing:-.02em;line-height:1.2}
 .muted{color:var(--mid);font-size:12px}
 .bar{height:8px;background:var(--line2);border-radius:5px;overflow:hidden;margin:4px 0}.bar>span{display:block;height:100%;border-radius:5px}
 .dom{margin-top:10px;padding-top:10px;border-top:1px solid var(--line2)}.dom .hd{display:flex;justify-content:space-between;font-weight:600;font-size:13px}
 .ev{font-size:12px;color:var(--mid);margin-top:2px}.warn{color:var(--terra);font-weight:700}
 .swrap{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0 4px;padding:11px;background:var(--line2);border-radius:12px}
 .slbl{font-size:10.5px;font-weight:700;color:var(--mid);margin-bottom:6px;letter-spacing:.03em}
 .dchip{display:inline-flex;align-items:center;gap:3px;font-size:11px;background:#fff;border:1px solid var(--line);border-radius:8px;padding:3px 7px;margin:0 4px 4px 0;cursor:pointer;transition:.14s;color:var(--ink)}
 .dchip:hover{border-color:var(--sage);transform:translateY(-1px)}.dchip b{font-size:12px}.dchip i{font-style:normal;font-weight:800;margin-left:1px}
 .dsecs{margin-top:6px}
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
 #regHeat,#domCorr,#sidoDom{overflow-x:auto}
 .card>.flex{align-items:center}
 /* 분석(stats) 대시보드 — 2열 그리드로 스크롤 최소화 */
 .statwrap{max-width:1340px}
 .statdash{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start;margin-top:4px}
 .statdash .card{margin:0}
 .statdash .card h3{margin:0 0 6px}
 .statdash .mini{font-size:11.5px;color:var(--mid);margin-bottom:9px;line-height:1.5}
 .statdash table.heat td,.statdash table.heat th{padding:4px 5px;font-size:10.5px}
 @media(max-width:1080px){.statdash{grid-template-columns:1fr}}
 .inswrap{max-width:1560px;padding-left:26px;padding-right:26px}
 .statwrap.inswrap{max-width:1560px}
 /* 진단 무스크롤 대시보드: 좌 리포트 · 우 순위표(각자 내부 스크롤) */
 .diagdash{display:grid;grid-template-columns:1fr minmax(0,440px);gap:16px;align-items:stretch}
 .diagdash>.card{height:68vh;overflow:auto}
 @media(max-width:900px){.diagdash{grid-template-columns:1fr}.diagdash>.card{height:auto}.diagdash>.card:first-child{max-height:56vh}}
 /* 통계 모달 대시보드 그리드 */
 .statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px;margin-top:16px;align-items:start}
 .statgrid .sc{background:#faf8f4;border:1px solid var(--line);border-radius:14px;padding:15px 16px;min-width:0;overflow:auto}
 .statgrid .sc.span2{grid-column:1/-1}
 .statgrid td[title],.statgrid circle[onclick]{cursor:pointer}
 .statgrid .sc h4{margin:0 0 10px;font-size:13.5px;color:var(--ink);font-weight:800;display:flex;align-items:baseline;gap:6px;flex-wrap:wrap}
 .statgrid .sc h4 span{font-weight:400;font-size:11.5px;color:var(--mid)}
 @media(max-width:760px){.statgrid{grid-template-columns:1fr}}
 .statdash,.statdash>.card{min-width:0}
 #regHeat,#domCorr,#sidoDom{max-width:100%}
 /* 데스크톱 전용 도구(복사·CSV·인쇄·공유) — 모바일 숨김(간단 조회/열람만) */
 .mobile-only{display:none}
 @media(max-width:640px){
   .dltools{display:none!important}
   .statdash .sd-heavy{display:none}   /* 무거운 히트맵은 모바일 숨김 → 서사 카드 위주 */
   .mobile-only{display:block}
 }
 /* 내 동네 추천 폼 — 통일 그리드 */
 .recgridfld{display:grid;grid-template-columns:1fr 1fr;gap:16px}
 .recgridfld input[type=number],.recgridfld input[type=text]{width:100%}
 @media(max-width:640px){.recgridfld{grid-template-columns:1fr}}
 /* 다이나믹 find: 둘러보기 리스트 + 검색/추천 */
 .findlist{display:flex;flex-direction:column;gap:6px;max-height:360px;overflow:auto}
 .findlist .valcell{cursor:pointer}
 #findResult{animation:vin .3s cubic-bezier(.22,1,.36,1)}
 /* 지역 비교 슬라이드 패널(레이더 스탯 비교) */
 #cmpBackdrop{position:fixed;inset:0;z-index:2900;background:rgba(20,26,20,.28);opacity:0;pointer-events:none;transition:.25s}
 #cmpBackdrop.on{opacity:1;pointer-events:auto}
 #cmpPanel{position:fixed;top:0;right:0;bottom:0;width:430px;max-width:92vw;background:#fff;z-index:2950;box-shadow:-10px 0 34px -10px rgba(20,30,40,.28);transform:translateX(103%);transition:transform .28s cubic-bezier(.22,1,.36,1);display:flex;flex-direction:column;overflow:auto}
 #cmpPanel.on{transform:none}
 .cmphd{display:flex;align-items:center;gap:8px;padding:15px 16px;border-bottom:1px solid var(--line);position:sticky;top:0;background:#fff;z-index:2}
 .cmphd b{font-size:16px}
 .cmpclose{cursor:pointer;color:var(--light);font-size:20px;line-height:1;padding:0 4px}
 #cmpRadar{padding:12px 12px 4px;text-align:center}
 #cmpBody{padding:4px 16px 24px}
 #cmpBody table{width:100%}#cmpBody td,#cmpBody th{padding:6px 8px}
 @media(max-width:640px){.findlist{max-height:260px}}
 .bhd{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
 .bhd h3{margin:0}
 .findlist .valcell{gap:8px}
 .findlist .valnm{flex:1;min-width:0}
 .findlist .valv{flex-shrink:0}
 @media(max-width:640px){.inswrap{padding-left:13px;padding-right:13px}.findlist .valnm{font-size:12.5px}}
 @media(max-width:640px){.bhd{gap:6px}.bhd .csel,.bhd select{min-width:0}.bhd>*:not(h3){margin-left:auto}}
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
   .asideToggle{display:inline-flex;align-items:center;gap:6px;position:absolute;top:12px;right:12px;z-index:1150;padding:8px 14px;border:1px solid var(--line);background:#fff;border-radius:999px;box-shadow:var(--sh);font-size:12.5px;font-weight:600;color:var(--ocean);cursor:pointer;font-family:var(--sans)}
   #asideBackdrop{position:absolute;inset:0;z-index:1180;background:rgba(30,26,20,.32);opacity:0;pointer-events:none;transition:opacity .26s}
   #asideBackdrop.on{opacity:1;pointer-events:auto}
 }
 @media(max-width:640px){
   .kpis{grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:20px}
   .kpi{padding:15px}.kpi b{font-size:26px}
   .card{padding:16px}
   .wrap{padding:18px 13px 40px}.hero-t{font-size:26px}
   /* 모바일 네비: 2줄 — 1줄(로고·검색·공유) 항상 보임 / 2줄 탭 가로스크롤 */
   nav{height:auto;min-height:0;padding:8px 10px 6px;gap:8px;flex-wrap:wrap;row-gap:7px}
   nav .logo{width:27px;height:27px;font-size:14px;order:0}
   nav .brand{font-size:15px;margin:0 0 0 8px;order:0}nav .brand small{display:none}
   .gsearch{order:1;margin-left:auto;flex:1 1 120px;min-width:110px}
   .gsearch input{width:100%}.gsearch input:focus{width:100%}
   .gsearch .ac{top:40px;left:0;right:0;width:auto}
   #shareBtn{order:1;flex-shrink:0;padding:7px 11px;font-size:12px}
   .tabs{order:2;flex:0 0 100%;min-width:0;overflow-x:auto;gap:2px;scrollbar-width:none}
   .tabs::-webkit-scrollbar{display:none}
   nav .tab{padding:7px 13px;font-size:13px;flex-shrink:0}
   .detail{width:auto;left:10px;right:10px;top:auto;bottom:10px;max-height:68%}
   .swrap{grid-template-columns:1fr}
   .hero-t{font-size:24px}.sub{font-size:13px}
   #rankTable td,#rankTable th{white-space:nowrap;padding:9px 10px}   /* 지역명 세로쫙 방지→가로스크롤 */
   .domgrid,.valgrid{grid-template-columns:1fr}
   h2{font-size:20px}
 }
</style></head><body>
<div id="app">
 <nav>
   <div class="logo">🏘</div><div class="brand">동네살기지수<small>NLI</small></div>
   <div class="tabs">
     <div class="tab on" data-v="map">지도</div>
     <div class="tab" data-v="find">내 동네 찾기</div>
     <div class="tab" data-v="insight">인사이트</div>
   </div>
 </nav>
 <div id="routeModal" class="rmodal" style="display:none" onclick="if(event.target===this)closeRoute()"><div class="rmbox">
   <div class="rmhd"><b id="rmTitle"></b><span class="rmclose" onclick="closeRoute()">✕</span></div>
   <div id="rmSummary" class="rmsum"></div>
   <div id="rmLegs" class="rmlegs"></div>
   <div class="rmfoot">대중교통 door-to-door · 오전 9시 출발 기준 · 지도에 경로 표시됨</div>
 </div></div>

 <div id="cmpBackdrop" onclick="closeCmpPanel()"></div>
 <div id="cmpPanel">
   <div class="cmphd"><b>지역 비교 <span id="cmpCount" class="muted" style="font-weight:400"></span></b>
     <span style="margin-left:auto;display:flex;gap:6px;align-items:center"><button class="btn" id="cmpClear">비우기</button><span class="cmpclose" onclick="closeCmpPanel()">✕</span></span></div>
   <div style="position:relative;padding:12px 16px 4px"><input type="text" id="cmpSearch" placeholder="지역 추가 (예: 노형동)" style="width:100%" autocomplete="off"><div class="ac" id="cmpac" style="left:16px;right:16px;top:52px;width:auto"></div></div>
   <div id="cmpRadar"></div>
   <div id="cmpBody"></div>
 </div>

 <div id="diagStatModal" class="rmodal" style="display:none" onclick="if(event.target===this)closeDiagStat()"><div class="rmbox" style="width:97vw;max-width:1600px;max-height:94vh">
   <div class="rmhd"><b>통계 분석</b><span class="rmclose" onclick="closeDiagStat()">✕</span></div>
   <div id="diagStatBody"></div>
 </div></div>

 <div class="view map" id="v-map" style="display:flex">
   <button class="asideToggle" id="asideToggle" aria-label="필터 열기">☰ 지표·필터</button>
   <aside>
     <div class="sec"><h3>지역 검색</h3>
       <div style="position:relative"><input type="text" id="gsearch" placeholder="예: 강남구 역삼" autocomplete="off" style="width:100%"><div class="ac" id="gac" style="left:0;right:0;top:40px;width:auto"></div></div></div>
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
   <div id="mapTitle" class="maptitle"></div>
   <div class="detail" id="detail" style="display:none"></div>
 </div>

 <div class="view" id="v-rec" style="display:none"><div class="wrap inswrap">
   <div id="findLanding">
     <h2>내 동네 찾기</h2>
     <div class="sub">순위를 둘러보고, <b>동네를 검색</b>하거나 <b>조건으로 맞춤 추천</b>을 받아보세요.</div>
     <div class="grid2" style="gap:16px;margin-bottom:16px">
       <div class="card"><div class="bhd"><h3 style="margin:0">가성비 동네</h3>
           <div class="flex" style="gap:6px;flex-shrink:0"><select id="valSido"></select><button class="btn dltools" onclick="shareValue(this)">공유</button></div></div>
         <div class="muted" style="margin:6px 0 10px">살기지수 높고 아파트값 낮은 · 클릭 → 상세</div>
         <div id="valueRank" class="findlist"></div></div>
       <div class="card"><div class="bhd"><h3 style="margin:0">지역 순위</h3>
           <button class="btn" onclick="findShowRank()">전체 순위 →</button></div>
         <div class="muted" style="margin:6px 0 10px">종합 살기지수 상위 · 클릭 → 상세</div>
         <div id="findRankTop" class="findlist"></div></div>
     </div>
     <div class="card findsearch">
       <h3 style="margin:0 0 4px">동네 검색 · 맞춤 추천</h3>
       <div class="muted" style="margin-bottom:8px">동네 이름으로 찾거나, 조건을 넣어 나에게 맞는 동네를 추천받으세요.</div>
       <div style="position:relative"><input type="text" id="findSearch" placeholder="동네 이름 검색 (예: 역삼동, 노형동)" autocomplete="off" style="width:100%"><div class="ac" id="findsac" style="left:0;right:0;top:42px;width:auto"></div></div>
       <div class="fld" style="margin-top:18px">조건으로 맞춤 추천 <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0">— 가구유형 가중치</span></div>
       <div class="seg" id="recHouseSeg" style="margin:7px 0 14px"><button data-h="일반" class="on">일반</button><button data-h="육아">육아</button><button data-h="1인">1인가구</button><button data-h="고령">고령</button><button data-h="반려">반려동물</button></div>
       <div class="recgridfld">
         <div><div class="fld">예산 — 평당가 상한 <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0">(만원, 비우면 전체)</span></div>
           <input type="number" id="recBudget" placeholder="예: 3000" style="width:100%;margin-top:6px" oninput="recBudget=+this.value||null"></div>
         <div><div class="fld">통근 기준지 <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0">(선택)</span></div>
           <span style="position:relative;display:block;margin-top:6px"><input type="text" id="recBase" placeholder="예: 역삼동" autocomplete="off" style="width:100%"><div class="ac" id="recbac" style="left:0;top:42px;right:auto;width:260px"></div></span>
           <span id="recBaseLabel" class="muted" style="font-size:12px"></span>
           <div id="recKmWrap" style="display:none;align-items:center;gap:7px;margin-top:8px;font-size:12px;color:var(--mid)">반경 <input type="range" id="recKm" min="2" max="40" step="1" value="10" style="width:130px" oninput="recKm=+this.value;document.getElementById('recKmV').textContent=recKm+'km'"><b id="recKmV" style="color:var(--ocean);font-weight:700">10km</b></div></div>
       </div>
       <button class="btn on" style="margin-top:16px;padding:11px 26px;width:100%;font-size:15px" onclick="recRun()">맞춤 동네 추천받기</button>
     </div>
   </div>
   <div id="findResult" style="display:none">
     <button class="btn" onclick="findBack()" style="margin-bottom:16px">← 돌아가기</button>
     <div id="findDongCard" style="display:none"></div>
     <div id="recResults" style="display:none"></div>
     <div id="rankPanel" style="display:none">
       <h2 style="margin-bottom:4px">지역 순위</h2><div class="sub">테마·시도·유형으로 정렬 · 행 클릭 → 상세 · ⊕ 비교담기 · ♡ 관심</div>
       <div class="flex" style="margin-bottom:10px"><select id="rankMetric"></select><select id="rankSido"></select>
         <select id="rankCohort"><option value="">전체 유형</option><option>도시</option><option>도농복합</option><option>농촌</option></select>
         <span class="muted" id="rankCount"></span></div>
       <div class="flex" style="margin-bottom:16px;position:relative;background:#faf8f4;border:1px solid var(--line);border-radius:12px;padding:9px 12px">
         <span style="font-size:12px;color:var(--terra);font-weight:700">통근 보정</span>
         <span style="position:relative;display:inline-block"><input type="text" id="rankBase" placeholder="기준지(출발지) 입력 (예: 역삼동)" style="width:230px" autocomplete="off"><div class="ac" id="rankbac" style="left:0;top:42px;right:auto;width:280px"></div></span>
         <span id="commuteInfo" class="muted"></span>
         <span id="commuteKmWrap" style="display:none;align-items:center;gap:7px;font-size:12px;color:var(--mid)">이내 <input type="range" id="commuteKm" min="2" max="40" step="1" value="10" style="width:120px"><b id="commuteKmV" style="color:var(--ocean);font-weight:700">10km</b>
         <button class="btn" id="commuteClear" style="padding:4px 12px">해제</button></span></div>
       <div class="card" style="padding:0;max-height:64vh;overflow:auto"><table id="rankTable"></table></div>
     </div>
   </div>
 </div></div>

 <div class="view" id="v-diag" style="display:none"><div class="wrap inswrap">
   <h2>지역 생활여건 진단 <span class="muted" style="font-size:14px;font-weight:400">— 지자체 229곳</span></h2>
   <div class="sub" style="margin-bottom:12px">시군구 단위 <b>취약 도메인</b>·<b>사각지대 동</b>(인구 1만+ 하위 20%) 진단 · <b>좌측 표에서 지자체를 클릭하면 우측 리포트가 갱신</b>되고 선택에 담깁니다. 여러 곳을 담고 <b>통계 분석</b>으로 한눈에 비교하세요.</div>
   <div class="flex" style="margin-bottom:12px">
     <input type="text" id="diagSearch" placeholder="지자체·동 검색 (예: 강남, 역삼)" style="width:230px" autocomplete="off">
     <select id="diagSido"></select>
     <select id="diagSort"><option value="nli">취약(평균지수 낮은) 순</option><option value="nli_desc">우수(평균지수 높은) 순</option><option value="blind">사각지대 많은 순</option><option value="blind_asc">사각지대 적은 순</option><option value="pop">인구 많은 순</option><option value="dongs">관할 동 많은 순</option></select><button class="btn on" onclick="openDiagStat()">통계 분석</button><span id="diagSelInfo" class="muted"></span>
     <span class="muted" id="diagCount"></span></div>
   <div id="diagCmp" style="display:none;margin-bottom:12px"></div>
   <div class="diagdash">
     <div class="card" style="padding:0;overflow:auto"><table id="diagTable"></table></div>
     <div id="diagCard" class="card"></div>
   </div>
 </div></div>

 <div class="foot" id="foot1" style="order:9"></div>
</div>
<script>
let _boot=(location.hash||'');   // 최초 딥링크 해시 캡처(showTab('map')의 writeHash가 지우기 전에)
const DATA=__GEOJSON__;
let POINTS=null;   // 시설포인트(11MB)는 첫 토글 시 nli_points.json 지연로딩(초기 로딩 경량화)
const F=DATA.features;
const DOMS=['D1','D2','D3','D4','D5','D6','D7','D8','D9'];
const METRICS={NLI:'종합 지수',D1:'의료·건강',D2:'교육·보육',D3:'생활편의·상업',D4:'문화·여가·체육',D5:'교통·이동',D6:'안전',D7:'환경·기후',D8:'복지·돌봄',D9:'반려·동물',grade:'등급'};
const DOMFAC={D1:[['ph','약국',1],['cl','의료기관',1],['em','응급의료기관',1]],D2:[['sc','학교',1],['cd','어린이집',1],['lb','도서관',1]],D3:[['st','상가',0],['bg','대규모점포',1],['gs','주유소',1],['wi','무료와이파이',1]],D4:[['pk','공원',1],['sp','체육시설',1],['mu','박물관·미술관',1],['th','공연장',1],['cn','영화상영관',1]],D5:[['bs','버스정류장',1],['pg','주차장',1],['bk','자전거보관소',1],['sw','지하철역',1],['br','자전거대여소',1]],D6:[['cc','CCTV',1],['cz','어린이보호구역',1],['sb','안전비상벨',1],['cs','민방위대피',1]],D7:[['ev','전기차충전소',1],['ht','무더위쉼터',1],['tr','보호수',1]],D8:[['wf','사회복지시설',1],['sr','경로당·마을회관',1]],D9:[['vh','동물병원',1]]};
const GC={S:'#2f6b4e',A:'#6f9e86',B:'#d4a056',C:'#cf8a5c',D:'#b0603f'};
// 홈 도메인 쇼케이스 (아이콘·지표 목록, DATASETS 기준 실제 30지표)
const DOMINFO={
 D1:['🏥','의료·건강',['약국','의료기관','응급의료'],'#c0392b'],
 D2:['🎓','교육·보육',['초중등학교','학원','어린이집','도서관'],'#5b6bd0'],
 D3:['🛒','생활편의·상업',['생활편의상가','대규모점포','주유소','무료와이파이'],'#d4a056'],
 D4:['🎭','문화·여가·체육',['여가상가','도시공원','체육시설','박물관·미술관','공연장','영화상영관'],'#8e5db0'],
 D5:['🚌','교통·이동',['버스정류소','주차장','자전거보관소'],'#3f8fa8'],
 D6:['🛡️','안전',['CCTV','어린이보호구역','안전비상벨','민방위대피'],'#6f9e86'],
 D7:['🌿','환경·기후',['전기차충전소','무더위쉼터','보호수'],'#2f6b4e'],
 D8:['🤝','복지·돌봄',['사회복지시설','경로당·마을회관'],'#c47c52'],
 D9:['🐾','반려·동물',['동물병원'],'#cf8a5c']};
// 페르소나 프리셋 (D1의료 D2교육 D3생활편의 D4문화여가 D5교통 D6안전 D7환경 D8복지)
// 객관 가중(정보량/CRITIC)은 weight_analysis.py 산출값(균등=1.0 기준). 데이터 분산 기반이라 '참고용' 프리셋.
const PRESETS={
 '균등':[1,1,1,1,1,1,1,1,1],
 '정보량(엔트로피)':[1.31,1.05,0.75,0.72,0.70,0.95,0.51,1.01,2.00],
 'CRITIC(중복보정)':[0.91,0.91,0.80,0.70,0.76,0.85,1.08,1.47,1.52],
 '중요도(AHP)':[2.02,0.88,0.33,0.33,0.88,2.02,0.33,0.88,0.33],
 '영유아 양육':[1.4,2,1,1.3,1,1.6,1,1.2,1],
 '고령':[2,1,1.2,1.2,1.4,1.2,1.3,2,1.2],
 '1인 청년':[1,1,2,1.5,1.5,1,1,1,1.5],
 '반려동물':[1,1,1,1.3,1,1.2,1.3,1,2.5],
 '신혼·예비부모':[1.3,1.5,1.2,1,1.2,1.6,1.1,1,1],
 '학군·자녀교육':[1,2,1,1.3,1.1,1.5,1,1,1],
 '직장인 통근':[1,1,1.4,1.1,2,1,1,1,1],
 '건강·웰니스':[2,1,1,1.3,1,1,1.6,1.3,1],
 '문화·여가족':[1,1,1.4,2,1.3,1,1,1,1]};
// 연령구조 기반 동네 추천 페르소나 (전국평균: 영유아2.5%·유소년10.5%·고령19.5%)
function recPersona(p){if((p.r_inf!=null&&p.r_inf>=0.045)||(p.r_yth!=null&&p.r_yth>=0.16))return '영유아 양육';if(p.r_eld!=null&&p.r_eld>=0.40)return '고령';return null}
let W=[1,1,1,1,1,1,1,1,1];
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

// 3탭 IA: map / find(추천+순위) / insight(비교·진단·분석 한 페이지)
function renderInsight(){renderDiag();}
function showTab(v){
  if(!['map','find','insight'].includes(v))v='map';
  document.querySelectorAll('nav .tab').forEach(x=>x.classList.toggle('on',x.dataset.v===v));
  const show = v==='map'?['map'] : v==='find'?['rec'] : ['diag'];
  document.getElementById('app').style.overflowY=(v==='map'?'hidden':'auto');
  ['map','rec','rank','compare','stats','diag'].forEach(x=>{const el=document.getElementById('v-'+x);if(!el)return;
    const on=show.includes(x);
    el.style.display=on?(x==='map'?'flex':'block'):'none';
    if(on&&x!=='map'){el.style.flex='0 0 auto';el.style.overflow='visible';el.style.animation='none';void el.offsetWidth;el.style.animation='vin .3s cubic-bezier(.22,1,.36,1)';}});
  document.getElementById('foot1').style.display=(v==='map'?'none':'block');
  if(v==='map'&&map){setTimeout(()=>map.invalidateSize(),60);renderMapSliders();}
  else if(v==='find'){renderFind();}
  else if(v==='insight')renderInsight();
  writeHash();
}
document.querySelectorAll('nav .tab').forEach(t=>t.onclick=()=>showTab(t.dataset.v));


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
  document.getElementById('mReset').onclick=()=>{W=[1,1,1,1,1,1,1,1,1];mp.value='균등';renderMapSliders();mMetric='NLI';sel.value='NLI';recompRank();mRedraw();};
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
const SHORT={D1:'의료',D2:'교육',D3:'생활편의',D4:'문화여가',D5:'교통',D6:'안전',D7:'환경',D8:'복지',D9:'반려'};
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
  document.getElementById('modeDesc').textContent=t[mMode];
  const mt=document.getElementById('mapTitle');if(mt){const md={basic:'',blind:' · 사각지대',pop:' · 인구대비'};mt.textContent=METRICS[mMetric]+(md[mMode]||'');}
  writeHash();}
function mLegend(){const el=document.getElementById('legend');
  if(mMode==='blind'){el.innerHTML='<div><i style="background:#bb3a24"></i>사각지대</div><div><i style="background:#e8e0d0"></i>해당 없음</div>';return}
  el.innerHTML=[[80,'상위 80–100'],[65,'65–80'],[50,'50–65'],[35,'35–50'],[20,'20–35'],[0,'하위 0–20']].map(b=>`<div><i style="background:${color(b[0])}"></i>${b[1]}</div>`).join('');}
function detailHTML(p){
  const isf=fav.includes(p.adm_nm);
  let h=`<span class="close" onclick="document.getElementById('detail').style.display='none';curDetail=null;writeHash()">✕</span>
   <h4>${fullN(p)} <span class="g" style="background:${GC[gradeOf(p)]}">${gradeOf(p)}</span> <span class="heart" onclick="toggleFav('${p.adm_nm}')">${isf?'♥':'♡'}</span></h4>
   <div class="muted">${p.cohort} · 인구 ${(p.pop_total||0).toLocaleString()}명 ${isBlind(p,'NLI')?'· <span class="warn">사각지대</span>':''}</div>
   ${p.price!=null?`<div class="muted" style="margin-top:3px">아파트 실거래 <b style="color:var(--terra)">평당 ${Math.round(p.price*3.3058).toLocaleString()}만원</b> <span style="font-size:10.5px">(㎡당 ${p.price.toLocaleString()}만)</span></div>`:''}
   ${commuteBase?`<div id="transitInfo" class="muted" style="margin-top:4px">🚇 대중교통 계산 중…</div>`:''}
   ${(()=>{const rp=recPersona(p);return rp?`<div style="margin-top:5px;font-size:12px">이 동네 추천: <b>${rp}</b> <span style="cursor:pointer;color:var(--sky);text-decoration:underline" onclick="setPreset('${rp}');document.querySelector('nav .tab[data-v=map]').click()">가중치 적용</span></div>`:''})()}
   <div style="margin:10px 0"><b>종합 지수 ${nliW(p)}</b><div class="bar"><span data-w="${nliW(p)}" style="width:0;background:${color(nliW(p))}"></span></div></div>`;
  // 강점/약점 요약 (도메인 점수 정렬)
  const ds=DOMS.map(d=>[d,p['score_'+d]]).filter(x=>x[1]!=null).sort((a,b)=>b[1]-a[1]);
  const chip=([d,v])=>`<span class="dchip" style="border-color:${color(v)}55" onclick="showDom('${d}')"><b>${DOMINFO[d][0]}</b>${SHORT[d]} <i style="color:${color(v)}">${Math.round(v)}</i></span>`;
  if(ds.length>=4)h+=`<div class="swrap"><div><div class="slbl">강점</div>${ds.slice(0,3).map(chip).join('')}</div><div><div class="slbl">약점</div>${ds.slice(-3).reverse().map(chip).join('')}</div></div>`;
  h+=`<div class="dsecs">`;
  for(const d in DOMFAC){let v=p['score_'+d];if(v==null)continue;const ic=DOMINFO[d]?DOMINFO[d][0]:'';
    h+=`<div class="dom"><div class="hd"><span>${ic} ${METRICS[d]}</span><span style="color:${color(v)};font-weight:700">${v}</span></div><div class="bar"><span data-w="${v}" style="width:0;background:${color(v)}"></span></div>`;
    for(const fac of DOMFAC[d]){let c=fac[0],label=fac[1],hn=fac[2],n=p[c+'_c'],near=p[c+'_n'];let cnt=(n===0)?'<span class="warn">0개 ⚠</span>':((n||0).toLocaleString()+'개');h+=`<div class="ev">· ${label} ${cnt}${hn?(' · 최근접 '+(n===0?'—':dist(near)+walk(near))):''}</div>`}
    h+=`</div>`}
  h+=`</div><div class="flex" style="margin-top:14px;gap:6px"><button class="btn" onclick="addCmp('${p.adm_nm}')">⊕ 비교담기</button><button class="btn" onclick="shareDong('${p.adm_nm}',this)">이 동네 공유</button></div>`;
  return h;}
// daero 대중교통 door-to-door 소요시간(통근 기준지 설정 시 상세패널에 표시)
function fillTransit(p){
  if(!commuteBase)return;const bf=F.find(f=>f.properties.adm_nm===commuteBase);
  const el=document.getElementById('transitInfo');if(!el||!bf)return;
  const b=bf.properties;if(b.clat==null||p.clat==null){el.textContent='';return;}
  if(p.adm_nm===commuteBase){el.innerHTML='🚇 기준지 본인';return;}
  const u=`https://daero.duckdns.org/api/plan/coords?fromLat=${b.clat}&fromLon=${b.clon}&toLat=${p.clat}&toLon=${p.clon}&time=09:00`;
  fetch(u).then(r=>r.json()).then(j=>{const e=document.getElementById('transitInfo');if(!e)return;
    if(j&&j.found&&j.durationMin!=null){window._route={j,from:commuteBase,to:p.adm_nm};
      e.innerHTML=`🚇 <b>${commuteBase}</b>→여기 <b style="color:var(--ocean)">약 ${j.durationMin}분</b>`+(j.transfers?` · 환승 ${j.transfers}`:'')+` <a onclick="openRoute()" style="color:var(--sky);cursor:pointer;text-decoration:underline;font-weight:700">경로 보기 →</a>`;}
    else e.innerHTML='🚇 <span style="font-size:11px">대중교통 경로 없음(원거리·비운영)</span>';
  }).catch(()=>{const e=document.getElementById('transitInfo');if(e)e.innerHTML='🚇 <span style="font-size:11px">조회 실패</span>';});
}
let routeLayer=null;
function openRoute(){const R=window._route;if(!R)return;const j=R.j;
  document.getElementById('rmTitle').textContent=`${R.from} → ${R.to}`;
  document.getElementById('rmSummary').innerHTML=`총 <b>${j.durationMin}분</b> · 환승 ${j.transfers||0}회 · ₩${(j.estimatedFareKrw||0).toLocaleString()} <span style="color:var(--mid)">(${j.departure||''}~${j.arrival||''})</span>`;
  const ic={WALK:['🚶','#9aa7b2'],BUS:['🚌','#4a9d6f'],SUBWAY:['🚇','#c47c52'],METRO:['🚇','#c47c52'],RAIL:['🚆','#5b6bd0'],TRAIN:['🚆','#5b6bd0']};
  document.getElementById('rmLegs').innerHTML=(j.legs||[]).map(l=>{const [ico,col]=ic[l.mode]||['🚏','#5b6b77'];
    const label=l.mode==='WALK'?'도보':((l.route?l.route+' ':'')+(l.mode==='BUS'?'버스':(l.mode==='SUBWAY'||l.mode==='METRO')?'지하철':l.mode));
    return `<div class="rmleg"><span class="rmic" style="background:${col}22;color:${col}">${ico}</span><div><div class="rmt">${label} · ${l.min}분</div><div class="rmst">${l.from||''} → ${l.to||''} <span>${l.depart||''}~${l.arrive||''}</span></div></div></div>`}).join('');
  document.getElementById('routeModal').style.display='flex';
  if(map){if(routeLayer)routeLayer.remove();routeLayer=L.layerGroup();
    (j.legs||[]).forEach(l=>{if(l.path&&l.path.length>1){const w=l.mode==='WALK';L.polyline(l.path,{color:w?'#8a94a0':'#2f6b8f',weight:w?3:5,opacity:.9,dashArray:w?'3 6':null}).addTo(routeLayer);}});
    routeLayer.addTo(map);try{map.fitBounds(routeLayer.getBounds(),{padding:[50,50]});}catch(e){}}
}
function closeRoute(){document.getElementById('routeModal').style.display='none';}
function showDetail(p,focus){const d=document.getElementById('detail');d.innerHTML=detailHTML(p);d.style.display='block';growBars();curDetail=p.adm_nm;writeHash();fillTransit(p);
  // focus=true(검색·순위·딥링크로 진입)일 때만 지도 리프레이밍. 지도 직접클릭은 현재 위치 유지(확대상태 축소 방지)
  if(focus&&p._l&&map){map.invalidateSize();const b=p._l.getBounds();if(b&&b.isValid())map.fitBounds(b,{maxZoom:13,padding:[24,24]});}}
function goDetail(adm){const f=F.find(x=>x.properties.adm_nm===adm);if(!f)return;document.querySelector('nav .tab[data-v=map]').click();showDetail(f.properties,true)}
// B2C 공유: 카톡 등에 바로 붙일 자동 문구 + 동네 딥링크 (모바일=네이티브 공유시트, 데스크톱=클립보드)
function shareDong(adm,btn){
  const f=F.find(x=>x.properties.adm_nm===adm);if(!f)return;const p=f.properties;
  const r=nliRank.get(adm),pct=r==null?null:Math.max(1,Math.round((1-r)*100));
  const ds=DOMS.map(d=>[d,p['score_'+d]]).filter(x=>x[1]!=null).sort((a,b)=>b[1]-a[1]);
  const top=ds.slice(0,2).map(x=>SHORT[x[0]]).join('·');
  const url=location.origin+location.pathname+'#d='+encodeURIComponent(adm);
  const msg='🏘 '+fullN(p)+' · 동네살기지수 '+nliW(p)+(pct?' (전국 상위 '+pct+'%)':'')+' · 종합 '+gradeOf(p)+'등급\n💪 강점 '+top+(p.price!=null?' · 아파트 평당 '+Math.round(p.price*3.3058).toLocaleString()+'만':'')+'\n👉 '+url;
  if(navigator.share){navigator.share({title:fullN(p)+' 동네살기지수',text:msg}).catch(()=>{});return;}
  const ok=()=>{if(!btn)return;const o=btn.textContent;btn.textContent='✓ 복사됨';setTimeout(()=>btn.textContent=o,1400);};
  if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(msg).then(ok,()=>prompt('공유 문구 복사',msg));
  else prompt('공유 문구 복사',msg);
}
// B2C 내 동네 추천 마법사 — 가구유형(페르소나 가중치)·예산·통근으로 맞춤 Top10 (기존 PRESETS·hav·nliWith 재사용)
const REC_MAP={'일반':'균등','육아':'영유아 양육','1인':'1인 청년','고령':'고령','반려':'반려동물'};
let recHouse='일반',recBudget=null,recBase=null,recKm=10;
function nliWith(p,ww){let s=0,w=0;DOMS.forEach((d,i)=>{const v=p['score_'+d];if(v!=null&&!isNaN(v)){s+=ww[i]*v;w+=ww[i]}});return w?s/w:null}
function recSetHouse(h,btn){recHouse=h;document.querySelectorAll('#recHouseSeg button').forEach(x=>x.classList.toggle('on',x===btn));}
function recPickBase(adm){recBase=adm;const f=F.find(x=>x.properties.adm_nm===adm),el=document.getElementById('recBaseLabel');if(el)el.innerHTML=f?'✓ <b>'+f.properties.full_nm+'</b> <span onclick="recClearBase()" style="cursor:pointer;color:var(--terra);font-weight:700">✕</span>':'';document.getElementById('recKmWrap').style.display='flex';}
function recClearBase(){recBase=null;const el=document.getElementById('recBaseLabel');if(el)el.textContent='';document.getElementById('recKmWrap').style.display='none';}
function recCard(p,rank,score){
  const ds=DOMS.map(d=>[d,p['score_'+d]]).filter(x=>x[1]!=null).sort((a,b)=>b[1]-a[1]);
  const chips=ds.slice(0,2).map(x=>'<span class="dchip" style="border-color:'+color(x[1])+'55" onclick="showDom(\''+x[0]+'\')"><b>'+DOMINFO[x[0]][0]+'</b>'+SHORT[x[0]]+' <i style="color:'+color(x[1])+'">'+Math.round(x[1])+'</i></span>').join('');
  return '<div class="card" style="padding:15px">'
    +'<div class="flex" style="justify-content:space-between;align-items:baseline;gap:8px"><b style="font-size:13.5px">'+rank+'. '+fullN(p)+'</b><span style="color:'+color(score)+';font-weight:800;font-size:18px">'+score.toFixed(1)+'</span></div>'
    +'<div class="muted" style="margin:5px 0 9px;font-size:11.5px">'+(p.price!=null?'평당 '+Math.round(p.price*3.3058).toLocaleString()+'만':'가격정보 없음')+(p._km!=null?' · 🚇 '+p._km.toFixed(1)+'km(직선)':'')+'</div>'
    +'<div style="margin-bottom:10px">'+chips+'</div>'
    +'<div class="flex" style="gap:6px"><button class="btn" onclick="goDetail(\''+p.adm_nm+'\')">상세</button><button class="btn" onclick="shareDong(\''+p.adm_nm+'\',this)">공유</button></div></div>';
}
// 가성비 동네(종합지수 백분위 − 가격 백분위) — 통계 탭에서 추천 탭으로 이동
function renderValueRank(){
  const el=document.getElementById('valueRank');if(!el)return;
  const sf=document.getElementById('valSido');
  if(sf&&!sf.options.length){sf.innerHTML='<option value="">전국</option>'+[...new Set(SP.map(p=>p.sido).filter(Boolean))].sort().map(s=>'<option>'+s+'</option>').join('');sf.onchange=renderValueRank;customSelect(sf);}
  const fs=sf?sf.value:'';
  const pr=SP.filter(p=>p.price!=null&&(p.pop_total||0)>=3000);   // 백분위는 전국 기준(진짜 가성비)
  const nS=pr.map(p=>nliW(p)).sort((a,b)=>a-b),pS=pr.map(p=>p.price).sort((a,b)=>a-b);
  const pctl=(arr,v)=>{let lo=0,hi=arr.length;while(lo<hi){let m=(lo+hi)>>1;if(arr[m]<v)lo=m+1;else hi=m}return lo/arr.length};
  let val=pr.map(p=>({p:p,g:pctl(nS,nliW(p))-pctl(pS,p.price)})).sort((a,b)=>b.g-a.g);
  if(fs)val=val.filter(x=>x.p.sido===fs);
  window._valTop=val.slice(0,12);
  el.innerHTML=val.length?val.slice(0,12).map((x,i)=>{const p=x.p;return '<div class="valcell" onclick="findShowDong(\''+p.adm_nm+'\')"><div class="valnm"><b>'+(i+1)+'.</b> '+p.adm_nm+'<span>'+p.sido+'</span></div><div class="valv"><span class="g" style="background:'+GC[gradeOf(p)]+'">'+gradeOf(p)+'</span> <b>'+nliW(p)+'</b><i>'+Math.round(p.price*3.3058).toLocaleString()+'만/평</i></div></div>'}).join(''):'<div class="muted">해당 지역에 실거래 데이터가 있는 동이 없습니다.</div>';
}
function shareValue(btn){
  const top=(window._valTop||[]).slice(0,5);if(!top.length)return;
  const sf=document.getElementById('valSido'),region=(sf&&sf.value)?sf.value:'전국';
  const lines=top.map((x,i)=>(i+1)+'. '+x.p.adm_nm+' ('+nliW(x.p)+'점·평당 '+Math.round(x.p.price*3.3058).toLocaleString()+'만)');
  const url=location.origin+location.pathname+'#v=rec';
  const msg='💎 '+region+' 가성비 동네 TOP5 — 살기지수 높고 아파트값 낮은\n'+lines.join('\n')+'\n👉 '+url;
  if(navigator.share){navigator.share({title:region+' 가성비 동네',text:msg}).catch(()=>{});return;}
  const ok=()=>{const o=btn.textContent;btn.textContent='✓ 복사됨';setTimeout(()=>btn.textContent=o,1400);};
  if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(msg).then(ok,()=>prompt('공유 문구',msg));
  else prompt('공유 문구',msg);
}
function renderFind(){renderValueRank();renderFindRankTop();document.getElementById('findLanding').style.display='block';document.getElementById('findResult').style.display='none';}
function renderFindRankTop(){const el=document.getElementById('findRankTop');if(!el)return;
  const arr=F.map(f=>f.properties).filter(p=>(p.pop_total||0)>0).sort((a,b)=>nliW(b)-nliW(a)).slice(0,8);
  el.innerHTML=arr.map((p,i)=>'<div class="valcell" onclick="findShowDong(\''+p.adm_nm+'\')"><div class="valnm"><b>'+(i+1)+'.</b> '+p.adm_nm+'<span>'+(p.sido||'')+'</span></div><div class="valv"><span class="g" style="background:'+GC[gradeOf(p)]+'">'+gradeOf(p)+'</span> <b>'+nliW(p)+'</b></div></div>').join('');}
function findOpen(mode){document.getElementById('findLanding').style.display='none';const r=document.getElementById('findResult');r.style.display='block';
  ['findDongCard','recResults','rankPanel'].forEach(id=>{const e=document.getElementById(id);if(e)e.style.display=(id===mode?'block':'none')});
  r.style.animation='none';void r.offsetWidth;r.style.animation='vin .3s cubic-bezier(.22,1,.36,1)';const app=document.getElementById('app');if(app)app.scrollTop=0;}
function findBack(){document.getElementById('findResult').style.display='none';document.getElementById('findLanding').style.display='block';const app=document.getElementById('app');if(app)app.scrollTop=0;}
function findShowDong(adm){const f=F.find(x=>x.properties.adm_nm===adm);if(!f)return;document.getElementById('findDongCard').innerHTML=findDongHTML(f.properties);findOpen('findDongCard');}
function findShowRank(){findOpen('rankPanel');renderRank();}
function findDongHTML(p){const doms=DOMS.map(d=>[d,p['score_'+d]]).filter(x=>x[1]!=null).sort((a,b)=>b[1]-a[1]);
  const strong=doms.slice(0,3),weak=doms.slice(-3).reverse();
  const chip=(x,col)=>'<span class="dchip" style="border-color:'+col+'55;cursor:default"><b>'+DOMINFO[x[0]][0]+'</b>'+SHORT[x[0]]+' <i style="color:'+col+'">'+Math.round(x[1])+'</i></span>';
  const pr=p.price!=null?Math.round(p.price*3.3058).toLocaleString()+'만/평':'실거래 없음';
  const _r=nliRank.get(p.adm_nm),pct=_r==null?null:Math.max(1,Math.round((1-_r)*100));
  return '<div class="card"><div class="flex" style="justify-content:space-between;align-items:flex-start;gap:12px">'
    +'<div style="min-width:0"><h2 style="margin:0">'+fullN(p)+'</h2><div class="muted" style="margin-top:4px">'+(p.cohort||'')+' · 인구 '+(p.pop_total||0).toLocaleString()+'명 · 평당 '+pr+'</div>'
    +(pct?'<div style="margin-top:8px;display:inline-block;background:rgba(180,124,82,.12);color:var(--terra);font-weight:800;font-size:13px;border-radius:999px;padding:5px 14px">전국 상위 '+pct+'%</div>':'')+'</div>'
    +'<div style="text-align:right;flex-shrink:0"><span class="g" style="background:'+GC[gradeOf(p)]+';font-size:15px;padding:3px 10px">'+gradeOf(p)+'</span><div style="font-size:30px;font-weight:800;color:var(--ocean);line-height:1.15">'+nliW(p)+'</div><div class="muted" style="font-size:11px">종합 살기지수</div></div></div>'
    +'<div style="margin-top:16px"><div class="fld">강점 도메인</div><div style="margin-top:6px">'+strong.map(x=>chip(x,'#2f6b4e')).join('')+'</div></div>'
    +'<div style="margin-top:12px"><div class="fld">약한 도메인</div><div style="margin-top:6px">'+weak.map(x=>chip(x,'#b0603f')).join('')+'</div></div>'
    +'<div class="flex" style="margin-top:18px;gap:8px"><button class="btn on" onclick="goDetail(\''+p.adm_nm+'\')">지도에서 자세히</button><button class="btn" onclick="addCmp(\''+p.adm_nm+'\')">⊕ 비교에 담기</button></div></div>';}
function recRun(){
  const ww=PRESETS[REC_MAP[recHouse]]||PRESETS['균등'];
  let arr=SP.filter(p=>(p.pop_total||0)>0);
  if(recBudget)arr=arr.filter(p=>p.price!=null&&p.price*3.3058<=recBudget);
  if(recBase){const bf=F.find(f=>f.properties.adm_nm===recBase),bp=bf&&bf.properties;
    if(bp&&bp.clat!=null)arr=arr.filter(p=>{if(p.clat==null)return false;p._km=hav(bp.clat,bp.clon,p.clat,p.clon);return p._km<=recKm;});}
  const top=arr.map(p=>({p:p,s:nliWith(p,ww)})).filter(x=>x.s!=null).sort((a,b)=>b.s-a.s).slice(0,10);
  const el=document.getElementById('recResults');findOpen('recResults');
  if(!top.length){el.innerHTML='<div class="card muted">조건에 맞는 동네가 없습니다. 예산을 높이거나 통근 반경을 넓혀보세요.</div>';return;}
  const cond=[REC_MAP[recHouse]!=='균등'?recHouse+' 가중치':'균등 가중치'];
  if(recBudget)cond.push('평당 ≤'+recBudget.toLocaleString()+'만');
  if(recBase){const bf=F.find(f=>f.properties.adm_nm===recBase);cond.push((bf?bf.properties.adm_nm:recBase)+' '+recKm+'km 이내');}
  el.innerHTML='<h2 style="margin:0 0 4px">맞춤 동네 Top '+top.length+'</h2><div class="muted" style="margin-bottom:14px">조건: '+cond.join(' · ')+' · 클릭 → 지도 상세</div><div class="recgrid">'+top.map((x,i)=>recCard(x.p,i+1,x.s)).join('')+'</div>';
}
function showDom(d){mMode='basic';document.querySelectorAll('#modes button').forEach(x=>x.classList.toggle('on',x.dataset.m==='basic'));document.querySelector('nav .tab[data-v=map]').click();const s=document.getElementById('metric');if(s){s.value=d;s.dispatchEvent(new Event('change'));}}

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
  document.getElementById('commuteInfo').innerHTML=`<b style="color:var(--ocean)">${adm}</b> 기준 · <span style="font-size:11px">동 클릭 시 🚇대중교통 시간</span> ·`;
  document.getElementById('commuteKmWrap').style.display='inline-flex';renderRank();writeHash();}

function addCmp(adm){if(cmp.includes(adm)){openCmpPanel();return;}if(cmp.length>=4){alert('최대 4곳까지 비교할 수 있어요');return;}cmp.push(adm);openCmpPanel();renderCmpPanel();}
function openCmpPanel(){document.getElementById('cmpPanel').classList.add('on');document.getElementById('cmpBackdrop').classList.add('on');}
function closeCmpPanel(){document.getElementById('cmpPanel').classList.remove('on');document.getElementById('cmpBackdrop').classList.remove('on');}
const CMPCOL=['#2f6b4e','#c47c52','#3f8fa8','#d4a056'];
function radarSVG(ps){
  const N=DOMS.length,cx=155,cy=150,R=106,ang=i=>(-90+i*360/N)*Math.PI/180,pt=(i,r)=>[cx+r*Math.cos(ang(i)),cy+r*Math.sin(ang(i))];
  let g='';
  [0.25,0.5,0.75,1].forEach(t=>{g+='<polygon points="'+DOMS.map((_,i)=>pt(i,R*t).map(v=>v.toFixed(1)).join(',')).join(' ')+'" fill="none" stroke="#e7e1d5" stroke-width="1"/>';});
  DOMS.forEach((d,i)=>{const a=pt(i,R);g+='<line x1="'+cx+'" y1="'+cy+'" x2="'+a[0].toFixed(1)+'" y2="'+a[1].toFixed(1)+'" stroke="#eee"/>';const l=pt(i,R+15);g+='<text x="'+l[0].toFixed(1)+'" y="'+l[1].toFixed(1)+'" font-size="12" text-anchor="middle" dominant-baseline="middle">'+DOMINFO[d][0]+'</text>';});
  ps.forEach((p,k)=>{const col=CMPCOL[k%4],pts=DOMS.map((d,i)=>pt(i,R*((p['score_'+d]||0)/100)).map(x=>x.toFixed(1)).join(',')).join(' ');
    g+='<polygon points="'+pts+'" fill="'+col+'26" stroke="'+col+'" stroke-width="2"/>';});
  return '<svg viewBox="0 0 310 300" style="width:100%;max-width:340px">'+g+'</svg>';
}
function renderCmpPanel(){
  const cnt=document.getElementById('cmpCount'),rad=document.getElementById('cmpRadar'),b=document.getElementById('cmpBody');
  if(cnt)cnt.textContent=cmp.length?'· '+cmp.length+'곳':'';
  if(!cmp.length){rad.innerHTML='';b.innerHTML='<div class="muted" style="padding:26px 6px;text-align:center;line-height:1.7">비교할 지역이 없습니다.<br>검색하거나, 순위·지도·추천에서 <b>⊕</b>로 담으세요.</div>';writeHash();return;}
  const ps=cmp.map(a=>{const ff=F.find(x=>x.properties.adm_nm===a);return ff&&ff.properties;}).filter(Boolean);
  rad.innerHTML=radarSVG(ps)+'<div style="display:flex;flex-direction:column;gap:5px;margin-top:8px;align-items:flex-start;padding:0 6px">'+ps.map((p,k)=>'<span style="font-size:12.5px;display:inline-flex;align-items:center;gap:6px"><i style="width:11px;height:11px;border-radius:3px;background:'+CMPCOL[k%4]+';display:inline-block;flex-shrink:0"></i><b>'+p.adm_nm+'</b> <span class="muted">'+(p.sido||'')+'</span> <span style="color:var(--ocean);font-weight:800">'+nliW(p)+'</span> <span style="cursor:pointer;color:var(--light)" onclick="cmp=cmp.filter(x=>x!==\''+p.adm_nm+'\');renderCmpPanel()">✕</span></span>').join('')+'</div>';
  const best=d=>Math.max.apply(null,ps.map(p=>p['score_'+d]==null?-1:p['score_'+d]));
  let rows='<tr><td><b>종합 지수</b></td>'+ps.map(p=>'<td class="n"><b style="color:var(--ocean)">'+nliW(p)+'</b></td>').join('')+'</tr>';
  DOMS.forEach(d=>{rows+='<tr><td>'+DOMINFO[d][0]+' '+SHORT[d]+'</td>'+ps.map(p=>{const v=p['score_'+d];return '<td class="n" style="'+(v!=null&&v===best(d)?'background:#e4f0e8;font-weight:800':'')+'">'+(v==null?'–':v)+'</td>';}).join('')+'</tr>';});
  b.innerHTML='<div style="overflow:auto"><table style="font-size:12.5px"><tr><th></th>'+ps.map((p,k)=>'<th style="font-size:11px;color:'+CMPCOL[k%4]+'">'+p.adm_nm+'</th>').join('')+'</tr>'+rows+'</table></div><div class="muted" style="font-size:11px;margin-top:8px">각 행 최고값 초록 강조 · 점수는 전국 백분위</div>';
  writeHash();
}


// 페르소나 프리셋 적용(가중치 W 설정 → 지도 사이드바 슬라이더·지도·순위 즉시 반영). 맞춤설정 탭은 지도 사이드바로 통합됨.
function setPreset(k){W=PRESETS[k].slice();const mp=document.getElementById('mpersona');if(mp&&PRESETS[k])mp.value=k;renderMapSliders();recompRank();if(layer)layer.setStyle(mStyle);writeHash()}

/* ---------- 지역 통계 탭 (지역 특성 × 도메인 중심) ---------- */
const DKEYS=['D1','D2','D3','D4','D5','D6','D7','D8','D9'];
const REG=[['dens','인구밀도'],['pop','인구'],['eld','고령비중'],['yth','유소년비중'],['apt','아파트비율'],['old','노후주택비율'],['price','아파트값']];
const VARS={dens:'인구밀도(로그)',pop:'인구(로그)',eld:'고령비중%',yth:'유소년%',inf:'영유아%',apt:'아파트비율%',old:'노후주택비율%',price:'아파트 평당가(만원)',NLI:'종합지수',D1:'의료',D2:'교육',D3:'생활편의',D4:'문화여가',D5:'교통',D6:'안전',D7:'환경',D8:'복지',D9:'반려'};
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
  if(k==='price')return p.price!=null?p.price*3.3058:null;   // ㎡당 만원 → 평당 만원
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
  // 아파트값 ↔ 종합지수 상관
  const prV=SP.map(p=>sval(p,'price')), priceNli=pearson(prV,SP.map(p=>nliW(p)));
  // 서사: 계산된 상관을 평문 문장으로(핵심 인사이트를 앞세움)
  const _sgn=v=>v>=0?'+':'', _strg=v=>{const a=Math.abs(v);return a<.15?'거의 무관':a<.3?'약한 관계':a<.5?'뚜렷한 관계':'강한 관계';};
  const _sn=document.getElementById('statNarr');
  if(_sn)_sn.innerHTML='<div class="card" style="background:linear-gradient(135deg,#eef4f1,#eaf1f4);border:0;margin-bottom:16px">'
    +'<div style="font-size:12px;font-weight:800;color:var(--sky);letter-spacing:.08em">이 데이터가 말하는 것</div>'
    +'<div style="font-size:14.5px;line-height:1.85;margin-top:6px;max-width:900px;word-break:keep-all">'
    +'· <b>아파트값 ↔ 살기지수</b>는 '+_strg(priceNli)+'('+_sgn(priceNli)+priceNli.toFixed(2)+') — 비싼 동네가 꼭 살기 좋은 건 아닙니다.<br>'
    +'· 가장 뚜렷한 관계는 <b>'+best[0]+'</b>('+_sgn(best[1])+best[1].toFixed(2)+') — 지역 특성이 생활여건을 크게 좌우합니다.<br>'
    +'· <b>고령 비중 ↔ 의료</b>는 '+_strg(eldMed)+'('+_sgn(eldMed)+eldMed.toFixed(2)+'), <b>의료 접근성</b>은 도시가 농촌의 <b>'+gap.toFixed(1)+'배</b> — 정책이 필요한 지점입니다.'
    +'</div></div>';
  document.getElementById('statKpi').innerHTML=
    `<div class="kpi"><b>${avgNLI.toFixed(1)}</b><span>평균 종합지수</span></div>
     <div class="kpi"><b style="color:${priceNli>=0?'#2f6b4e':'#b0603f'}">${priceNli>=0?'+':''}${priceNli.toFixed(2)}</b><span>아파트값 ↔ 살기지수</span></div>
     <div class="kpi"><b>${gap.toFixed(1)}배</b><span>의료 도농격차(도시/농촌)</span></div>
     <div class="kpi"><b style="color:${best[1]>=0?'#2f6b4e':'#b0603f'}">${best[1]>=0?'+':''}${best[1].toFixed(2)}</b><span>최강 지역상관 · ${best[0]}</span></div>`;


  // 지역 특성 × 도메인 상관 히트맵
  let ht='<table class="heat"><tr><th></th>'+dkAll.map(d=>`<th title="${VARS[d]}">${d==='NLI'?'종합':DOMINFO[d][0]}</th>`).join('')+'</tr>';
  REG.forEach(([rk,rn],ri)=>{ht+=`<tr><td style="font-weight:700;background:#f7f5f1;text-align:left;white-space:nowrap">${rn}</td>`+dvAll.map((dv,di)=>{const r=pearson(regV[ri],dv);return `<td style="background:${corrColor(r)};color:${Math.abs(r)>=.5?'#fff':'#1a2530'};${Math.abs(r)>=.3?'font-weight:700':''}">${r.toFixed(2)}</td>`}).join('')+'</tr>';});
  document.getElementById('regHeat').innerHTML=ht+'</table>';

  // 도메인 간 상관 (9×9): 어떤 인프라가 함께 몰리나
  const dv9=DKEYS.map(d=>SP.map(p=>p['score_'+d]));
  let hc='<table class="heat"><tr><th></th>'+DKEYS.map(d=>`<th>${DOMINFO[d][0]}</th>`).join('')+'</tr>';
  DKEYS.forEach((d,i)=>{hc+=`<tr><td style="font-weight:700;background:#f7f5f1;text-align:left;white-space:nowrap">${DOMINFO[d][0]} ${SHORT[d]}</td>`+DKEYS.map((d2,j)=>{if(i===j)return '<td style="background:#f0ede7;color:#c9beac">·</td>';const r=pearson(dv9[i],dv9[j]);return `<td style="background:${corrColor(r)};color:${Math.abs(r)>=.5?'#fff':'#1a2530'};${Math.abs(r)>=.3?'font-weight:700':''}">${r.toFixed(2)}</td>`}).join('')+'</tr>';});
  document.getElementById('domCorr').innerHTML=hc+'</table>';

  // 시도 × 도메인 프로파일: 각 도메인 열에서 상대강점(열 정규화 색)
  const sidos=[...new Set(SP.map(p=>p.sido))];
  const sm={};sidos.forEach(s=>{sm[s]={};const sub=SP.filter(p=>p.sido===s);DKEYS.forEach(d=>{const v=sub.map(p=>p['score_'+d]).filter(x=>x!=null);sm[s][d]=v.reduce((a,b)=>a+b,0)/(v.length||1);});sm[s]._nli=sub.reduce((a,p)=>a+(nliW(p)||0),0)/(sub.length||1);});
  sidos.sort((a,b)=>sm[b]._nli-sm[a]._nli);
  const dmm={};DKEYS.forEach(d=>{const vs=sidos.map(s=>sm[s][d]);dmm[d]=[Math.min(...vs),Math.max(...vs)];});
  let hsd='<table class="heat"><tr><th></th>'+DKEYS.map(d=>`<th>${DOMINFO[d][0]}<br><span style="font-weight:400;font-size:9px">${SHORT[d]}</span></th>`).join('')+'</tr>';
  sidos.forEach(s=>{hsd+=`<tr><td style="font-weight:700;background:#f7f5f1;text-align:left;white-space:nowrap;font-size:10.5px">${s.replace('특별자치도','').replace('특별자치시','').replace('광역시','').replace('특별시','')}</td>`+DKEYS.map(d=>{const v=sm[s][d],[mn,mx]=dmm[d],t=(v-mn)/((mx-mn)||1);return `<td style="background:rgba(47,107,78,${(.08+.82*t).toFixed(2)});color:${t>.5?'#fff':'#1a2530'}">${Math.round(v)}</td>`}).join('')+'</tr>';});
  document.getElementById('sidoDom').innerHTML=hsd+'</table>';

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

  const opts=['dens','pop','eld','yth','inf','apt','old','price','NLI',...DKEYS];
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
document.getElementById('foot1').innerHTML='데이터 출처 · 공공데이터포털 표준데이터 · SGIS 경계·인구(2025 2분기) · 건강보험심사평가원(2026.6) · 소상공인시장진흥공단 · 국토교통부 아파트 실거래가 · safetydata.go.kr · VWorld 지오코딩   ·   방법 · 시설밀도(인구 1만명당·면적 ㎢당 혼합)와 근접성의 백분위 결합 → 도메인 가중평균, 도농 코호트·인구가중 중심점 보정   ·   9개 도메인 32개 지표 읍면동 정밀(복지는 지오코딩 약 89% 커버) · 점수는 전국 읍면동 상대평가(백분위)로 참고용입니다<br><a href="mailto:lucestdail@kakao.com?subject=%5B%EB%8F%99%EB%84%A4%EC%82%B4%EA%B8%B0%EC%A7%80%EC%88%98%5D%20%EB%8F%84%EC%9E%85%C2%B7%EC%A0%9C%ED%9C%B4%20%EB%AC%B8%EC%9D%98&body=%EA%B8%B0%EA%B4%80/%EB%8B%B4%EB%8B%B9%EC%9E%90%3A%0A%EA%B4%80%EC%8B%AC%20%EC%A7%80%EC%97%AD/%EB%82%B4%EC%9A%A9%3A%0A%EC%97%B0%EB%9D%BD%EC%B2%98%3A%0A" style="display:inline-block;margin-top:9px;color:var(--ocean);font-weight:700;text-decoration:none">지자체·기관 도입·제휴 문의</a>';
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
  const raw=((location.hash&&location.hash.length>1)?location.hash:(_boot||'')).replace(/^#/,'');_boot='';if(!raw)return;
  const P={};raw.split('&').forEach(kv=>{const i=kv.indexOf('=');if(i>0){try{P[kv.slice(0,i)]=decodeURIComponent(kv.slice(i+1));}catch(e){}}});
  applyingHash=true;
  try{
    if(P.w){const a=P.w.split(',').map(Number);if(a.length===W.length&&a.every(x=>!isNaN(x))){for(let i=0;i<W.length;i++)W[i]=a[i];recompRank();}}
    if(P.m)mMetric=P.m;
    if(P.md)mMode=P.md;
    if(P.cb){commuteBase=P.cb;commuteKm=+P.ck||10;}
    if(P.c)cmp=P.c.split('~').filter(Boolean).slice(0,4);
    let v=P.d?'map':(P.v||'map');
    const alias={home:'map',rec:'find',rank:'find',compare:'insight',stats:'insight',diag:'insight'};
    if(alias[v])v=alias[v];
    showTab(v);
    if(P.md)document.querySelectorAll('#modes button').forEach(x=>x.classList.toggle('on',x.dataset.m===P.md));
    const ms=document.getElementById('metric');if(ms){ms.value=mMetric;ms.dispatchEvent(new Event('change'));}
    if(P.cb){const ci=document.getElementById('commuteInfo');if(ci){ci.innerHTML='<b style="color:var(--ocean)">'+P.cb+'</b> 기준 ·';document.getElementById('commuteKmWrap').style.display='inline-flex';document.getElementById('commuteKm').value=commuteKm;document.getElementById('commuteKmV').textContent=commuteKm+'km';}if(v==='find')renderRank();}
    if(P.sx){const sx=document.getElementById('sx'),sy=document.getElementById('sy');if(sx&&sx.onchange){sx.value=P.sx;if(P.sy&&sy)sy.value=P.sy;sx.dispatchEvent(new Event('change'));}}
    if(P.d){const f=F.find(x=>x.properties.adm_nm===P.d);if(f)showDetail(f.properties,true);}
    if(cmp.length){renderCmpPanel();openCmpPanel();}
  }catch(e){}
  applyingHash=false;
  if(typeof mRedraw==='function')mRedraw();
  writeHash();
}
/* ── 지역 생활여건 진단 (B2G) ── 지자체=full_nm.split[1] (자치구 분리·일반구는 시로 병합) */
let diagSel=null,diagSort='nli',diagCur=null,diagCmp=[];
function diagData(){
  const G={};
  SP.forEach(p=>{if((p.pop_total||0)<=0)return;const ps=(p.full_nm||'').split(' ');if(ps.length<2)return;
    const key=ps[0]+' '+ps[1];(G[key]=G[key]||{key:key,sido:ps[0],sgg:ps[1],dongs:[]}).dongs.push(p);});
  const nat={};DKEYS.forEach(d=>{const vs=SP.filter(p=>(p.pop_total||0)>0&&p['score_'+d]!=null).map(p=>p['score_'+d]);nat[d]=vs.reduce((a,b)=>a+b,0)/(vs.length||1);});
  const rows=Object.values(G).map(g=>{
    const nv=g.dongs.map(nliW).filter(v=>v!=null);g.nli=nv.reduce((a,b)=>a+b,0)/(nv.length||1);
    g.dom={};DKEYS.forEach(d=>{const vs=g.dongs.map(p=>p['score_'+d]).filter(v=>v!=null);g.dom[d]=vs.reduce((a,b)=>a+b,0)/(vs.length||1);});
    g.rankDom=DKEYS.map(d=>[d,g.dom[d]-nat[d]]).sort((a,b)=>a[1]-b[1]);
    g.blind=[];g.dongs.forEach(p=>DKEYS.forEach(d=>{if(isBlind(p,d))g.blind.push({p:p,d:d,v:p['score_'+d]})}));
    g.blind.sort((a,b)=>(b.p.pop_total||0)-(a.p.pop_total||0));g.blindN=g.blind.length;
    g.pop=g.dongs.reduce((a,p)=>a+(p.pop_total||0),0);return g;});
  return {rows:rows,nat:nat};
}
function diagCardHTML(g,rankOf,total){
  const gc=g.dongs.reduce((m,p)=>{const gr=gradeOf(p);m[gr]=(m[gr]||0)+1;return m},{});
  const gdist=['S','A','B','C','D'].filter(x=>gc[x]).map(x=>`<span style="color:${GC[x]};font-weight:700">${x}</span> ${gc[x]}`).join(' · ');
  const weak=g.rankDom.slice(0,3),strong=g.rankDom.slice(-2).reverse();
  const chip=(d,dv,neg)=>`<span class="dchip" style="border-color:${neg?'#b0603f':'#2f6b4e'}55" onclick="showDom('${d}')"><b>${DOMINFO[d][0]}</b>${SHORT[d]} <i style="color:${dv>=0?'#2f6b4e':'#b0603f'}">${dv>=0?'+':''}${Math.round(dv)}</i></span>`;
  const bl=g.blind.slice(0,9).map(b=>`<div class="valcell" onclick="goDetail('${b.p.adm_nm}')"><div class="valnm">${b.p.adm_nm}<span>${(b.p.pop_total||0).toLocaleString()}명</span></div><div class="valv"><span class="dchip" style="border-color:#b0603f55;margin:0"><b>${DOMINFO[b.d][0]}</b>${SHORT[b.d]}</span> <b style="color:#b0603f">${Math.round(b.v)}</b></div></div>`).join('');
  return `<div class="flex" style="justify-content:space-between;align-items:flex-start;gap:12px">
    <div style="min-width:0"><h3 style="margin:0 0 4px">${g.sido} ${g.sgg}</h3>
      <div class="muted">전국 취약순위 <b style="color:var(--terra)">${rankOf.get(g.key)}</b>/${total} · 인구 ${g.pop.toLocaleString()}명 · ${g.dongs.length}개 동 · 등급 ${gdist||'—'}</div></div>
    <a href="javascript:void 0" onclick="diagToMap();return false" style="flex-shrink:0;font-size:13px;color:var(--ocean);white-space:nowrap;align-self:flex-start;margin-top:5px">지도에서 보기 →</a></div>
   <div class="dkpi">
     <div class="kpi"><b style="color:${color(g.nli)}">${g.nli.toFixed(1)}</b><span>평균 종합지수 · 전국 백분위</span></div>
     <div class="kpi"><b style="color:var(--terra)">${g.blindN}</b><span>사각지대 · 동 × 도메인</span></div></div>
   <div class="grid2" style="margin-top:16px;gap:16px">
     <div><div class="fld" style="color:#b0603f;font-size:11.5px">취약 도메인 <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0">전국 평균 대비</span></div>
       <div style="margin-top:8px">${weak.map(w=>chip(w[0],w[1],true)).join('')}</div></div>
     <div><div class="fld" style="color:#2f6b4e;font-size:11.5px">상대 강점 <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0">전국 평균 대비</span></div>
       <div style="margin-top:8px">${strong.map(w=>chip(w[0],w[1],false)).join('')}</div></div></div>
   <div style="margin-top:18px"><div class="fld" style="font-size:11.5px">사각지대 동 <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0">인구 많은 순 · 클릭 → 지도 상세</span></div>
     ${g.blindN?`<div class="valgrid" style="margin-top:8px">${bl}</div>`+(g.blindN>9?`<div class="muted" style="margin-top:8px">외 ${g.blindN-9}건</div>`:''):'<div class="muted" style="margin-top:8px">사각지대 없음 — 인구 1만+ 동에서 하위 20% 도메인 없음</div>'}</div>`;
}
function renderDiag(){
  const dd=diagData(),rows=dd.rows;
  const sf=document.getElementById('diagSido');
  if(!sf.options.length){sf.innerHTML='<option value="">전국</option>'+[...new Set(rows.map(r=>r.sido))].sort().map(s=>`<option>${s}</option>`).join('');sf.onchange=()=>{diagSel=null;renderDiag();};customSelect(sf);}
  const dso=document.getElementById('diagSort');if(dso){if(!dso._w){dso._w=1;dso.value=diagSort;dso.onchange=()=>{diagSort=dso.value;renderDiag();};customSelect(dso);}}
  const dsr=document.getElementById('diagSearch');if(dsr&&!dsr._w){dsr._w=1;dsr.oninput=()=>{diagSel=null;renderDiag();};}
  const natRank=[...rows].sort((a,b)=>a.nli-b.nli),rankOf=new Map();natRank.forEach((r,i)=>rankOf.set(r.key,i+1));
  const fsido=sf.value;let list=rows.filter(r=>!fsido||r.sido===fsido);
  const dq=((document.getElementById('diagSearch')||{}).value||'').trim();if(dq)list=list.filter(r=>(r.sgg+' '+r.sido).includes(dq)||r.dongs.some(p=>(p.adm_nm||'').includes(dq)));
  const SORTERS={nli:(a,b)=>a.nli-b.nli,nli_desc:(a,b)=>b.nli-a.nli,blind:(a,b)=>b.blindN-a.blindN||a.nli-b.nli,blind_asc:(a,b)=>a.blindN-b.blindN||b.nli-a.nli,pop:(a,b)=>b.pop-a.pop,dongs:(a,b)=>b.dongs.length-a.dongs.length};
  list.sort(SORTERS[diagSort]||SORTERS.nli);
  document.getElementById('diagCount').textContent=list.length+'개 지자체';
  const dsi2=document.getElementById('diagSelInfo');if(dsi2)dsi2.innerHTML=diagCmp.length?(' · <b style="color:var(--ocean)">'+diagCmp.length+'곳 선택</b> <span style="cursor:pointer;color:var(--terra)" onclick="diagCmp=[];renderDiag()">비우기</span>'):'';
  if(!diagSel||!rows.find(r=>r.key===diagSel))diagSel=list[0]?list[0].key:null;
  const sel=rows.find(r=>r.key===diagSel);
  diagCur=sel?{g:sel,rank:rankOf.get(sel.key),total:rows.length}:null;
  document.getElementById('diagCard').innerHTML=sel?diagCardHTML(sel,rankOf,rows.length):'';
  renderDiagCmp(rows);
  let h='<tr><th>비교</th><th>취약<br>순위</th><th>지자체</th><th>평균<br>지수</th><th>최약 도메인</th><th>사각<br>지대</th><th>동</th></tr>';
  list.forEach(r=>{const w=r.rankDom[0],inc=diagCmp.includes(r.key);
    h+=`<tr onclick="pickDiag('${r.key}')" style="cursor:pointer${r.key===diagSel?';background:#e4f0e8;box-shadow:inset 3px 0 0 var(--ocean)':''}">
      <td style="text-align:center"><span onclick="event.stopPropagation();toggleDiagCmp('${r.key}')" title="비교 담기" style="cursor:pointer;font-weight:800;font-size:15px;color:${inc?'#2f6b4e':'#c9beac'}">${inc?'✓':'⊕'}</span></td>
      <td style="text-align:center;color:var(--mid)">${rankOf.get(r.key)}</td>
      <td style="text-align:left"><b>${r.sgg}</b> <span class="muted">${r.sido.replace('특별자치도','').replace('특별자치시','').replace('광역시','').replace('특별시','').replace('자치도','')}</span></td>
      <td style="text-align:center"><b style="color:${color(r.nli)}">${r.nli.toFixed(1)}</b></td>
      <td style="text-align:left"><span style="color:#b0603f">${DOMINFO[w[0]][0]} ${SHORT[w[0]]}</span> <span class="muted">${w[1]>=0?'+':''}${Math.round(w[1])}</span></td>
      <td style="text-align:center;color:var(--terra);font-weight:700">${r.blindN||''}</td>
      <td style="text-align:center;color:var(--mid)">${r.dongs.length}</td></tr>`;});
  document.getElementById('diagTable').innerHTML=h;
}
function selectDiag(k){diagSel=k;renderDiag();}
function pickDiag(k){diagSel=k;if(!diagCmp.includes(k))diagCmp.push(k);renderDiag();}
function closeDiagStat(){document.getElementById('diagStatModal').style.display='none';}
let _dstat=null;
function corrCol(r){if(r==null||isNaN(r))return '#f0ede7';const a=Math.min(1,Math.abs(r)),c=r>=0?[47,107,78]:[176,96,63];return 'rgba('+c[0]+','+c[1]+','+c[2]+','+(0.1+0.78*a).toFixed(2)+')';}
function openDiagStat(){
  const dd=diagData(),rows=dd.rows,nf=n=>(n||0).toLocaleString(),SD=s=>s.replace('특별자치도','').replace('특별자치시','').replace('광역시','').replace('특별시','').replace('자치도','');
  const dcol=k=>k<4?CMPCOL[k]:'hsl('+((k*67)%360)+',55%,45%)';
  let keys=diagCmp.length?diagCmp.slice():(diagSel?[diagSel]:[]);
  const gs=keys.map(k=>rows.find(r=>r.key===k)).filter(Boolean);
  if(!gs.length){alert('표에서 지자체를 클릭해 담으세요.');return;}
  const dongs=[];gs.forEach((g,k)=>g.dongs.forEach(p=>dongs.push({p:p,k:k})));
  _dstat={gs:gs,dongs:dongs,dcol:dcol};
  const natRank=[...rows].sort((a,b)=>a.nli-b.nli),rankOf=new Map();natRank.forEach((r,i)=>rankOf.set(r.key,i+1));
  const single=gs.length===1;
  // 레이더(선only, 꼭짓점 툴팁)
  const N=DOMS.length,cx=150,cy=148,R=104,ang=i=>(-90+i*360/N)*Math.PI/180,pt=(i,r)=>[cx+r*Math.cos(ang(i)),cy+r*Math.sin(ang(i))];
  let rg='';[0.25,0.5,0.75,1].forEach(t=>{rg+='<polygon points="'+DOMS.map((_,i)=>pt(i,R*t).map(v=>v.toFixed(1)).join(',')).join(' ')+'" fill="none" stroke="#e7e1d5" stroke-width="1"/>';});
  DOMS.forEach((d,i)=>{const a=pt(i,R);rg+='<line x1="'+cx+'" y1="'+cy+'" x2="'+a[0].toFixed(1)+'" y2="'+a[1].toFixed(1)+'" stroke="#eee"/>';const l=pt(i,R+14);rg+='<text x="'+l[0].toFixed(1)+'" y="'+l[1].toFixed(1)+'" font-size="12" text-anchor="middle" dominant-baseline="middle">'+DOMINFO[d][0]+'</text>';});
  gs.forEach((g,k)=>{const col=dcol(k),ptsA=DOMS.map((d,i)=>pt(i,R*((g.dom[d]||0)/100)));rg+='<polygon points="'+ptsA.map(a=>a.map(x=>x.toFixed(1)).join(',')).join(' ')+'" fill="'+(single?col+'22':'none')+'" stroke="'+col+'" stroke-width="2.2" stroke-linejoin="round"/>';ptsA.forEach((a,i)=>{rg+='<circle cx="'+a[0].toFixed(1)+'" cy="'+a[1].toFixed(1)+'" r="3" fill="'+col+'"><title>'+g.sgg+' · '+SHORT[DOMS[i]]+' '+Math.round(g.dom[DOMS[i]])+'점</title></circle>';});});
  const radar='<svg viewBox="0 0 300 296" style="width:100%;max-width:320px">'+rg+'</svg>';
  const legend='<div style="display:flex;flex-direction:column;gap:5px;margin-top:8px;align-items:flex-start">'+gs.map((g,k)=>'<span style="font-size:12.5px;display:inline-flex;align-items:center;gap:6px"><i style="width:11px;height:11px;border-radius:3px;background:'+dcol(k)+';display:inline-block;flex-shrink:0"></i><b>'+g.sgg+'</b> <span class="muted">'+SD(g.sido)+'</span> <span style="color:'+color(g.nli)+';font-weight:800">'+g.nli.toFixed(1)+'</span></span>').join('')+'</div>';
  // 바
  const bar=(g,k,val,w,col,tip)=>'<div style="display:flex;align-items:center;gap:8px;margin:5px 0;font-size:12.5px" title="'+tip+'"><span style="width:66px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis"><i style="width:8px;height:8px;border-radius:2px;background:'+dcol(k)+';display:inline-block;margin-right:3px"></i>'+g.sgg+'</span><div style="flex:1;background:var(--line2);border-radius:5px;height:15px"><div style="height:100%;border-radius:5px;background:'+col+';width:'+w+'%"></div></div><b style="width:34px;color:'+col+'">'+val+'</b></div>';
  const nliBars=gs.map((g,k)=>bar(g,k,g.nli.toFixed(1),g.nli,color(g.nli),g.sgg+' 평균 종합지수 '+g.nli.toFixed(1))).join('');
  const maxBl=Math.max(1,Math.max.apply(null,gs.map(g=>g.blindN)));
  const blBars=gs.map((g,k)=>bar(g,k,g.blindN,g.blindN/maxBl*100,'#b0603f',g.sgg+' 사각지대 '+g.blindN+'건')).join('');
  // 지자체 × 도메인 히트맵(셀 툴팁)
  let hm='<table class="heat" style="font-size:11px;width:auto"><tr><th></th>'+DKEYS.map(d=>'<th title="'+VARS[d]+'">'+DOMINFO[d][0]+'</th>').join('')+'<th>종합</th></tr>';
  gs.forEach(g=>{hm+='<tr><td style="text-align:left;font-weight:700;white-space:nowrap;background:#f2efe9">'+g.sgg+'</td>'+DKEYS.map(d=>{const v=g.dom[d];return '<td style="background:'+color(v)+';color:'+(v>=50?'#fff':'#1a2530')+'" title="'+g.sgg+' · '+VARS[d]+' '+Math.round(v)+'점">'+Math.round(v)+'</td>';}).join('')+'<td style="background:'+color(g.nli)+';color:'+(g.nli>=50?'#fff':'#1a2530')+';font-weight:800">'+g.nli.toFixed(0)+'</td></tr>';});
  hm+='</table>';
  // 도메인 간 상관 히트맵(선택 동 기준)
  const dv9=DKEYS.map(d=>dongs.map(o=>o.p['score_'+d]));
  let dc='<table class="heat" style="font-size:10.5px;width:auto"><tr><th></th>'+DKEYS.map(d=>'<th title="'+VARS[d]+'">'+DOMINFO[d][0]+'</th>').join('')+'</tr>';
  DKEYS.forEach((d,i)=>{dc+='<tr><td style="text-align:left;font-weight:700;white-space:nowrap;background:#f2efe9">'+DOMINFO[d][0]+' '+SHORT[d]+'</td>'+DKEYS.map((d2,j)=>{if(i===j)return '<td style="background:#f0ede7;color:#c9beac">·</td>';const r=pearson(dv9[i],dv9[j]);return '<td style="background:'+corrCol(r)+';color:'+(Math.abs(r)>=.5?'#fff':'#1a2530')+'" title="'+SHORT[d]+'↔'+SHORT[d2]+' r='+r.toFixed(2)+'">'+r.toFixed(2)+'</td>';}).join('')+'</tr>';});
  dc+='</table>';
  // 지역특성 × 도메인 상관
  const regV=REG.map(rr=>dongs.map(o=>sval(o.p,rr[0]))),dvA=[...DKEYS.map(d=>dongs.map(o=>o.p['score_'+d])),dongs.map(o=>nliW(o.p))],dkA=[...DKEYS,'NLI'];
  let rh='<table class="heat" style="font-size:10.5px;width:auto"><tr><th></th>'+dkA.map(d=>'<th title="'+VARS[d]+'">'+(d==='NLI'?'종합':DOMINFO[d][0])+'</th>').join('')+'</tr>';
  REG.forEach((rr,ri)=>{rh+='<tr><td style="text-align:left;font-weight:700;white-space:nowrap;background:#f2efe9">'+rr[1]+'</td>'+dvA.map((dv,di)=>{const r=pearson(regV[ri],dv);return '<td style="background:'+corrCol(r)+';color:'+(Math.abs(r)>=.5?'#fff':'#1a2530')+'" title="'+rr[1]+'↔'+VARS[dkA[di]]+' r='+(isNaN(r)?'-':r.toFixed(2))+'">'+(isNaN(r)?'–':r.toFixed(2))+'</td>';}).join('')+'</tr>';});
  rh+='</table>';
  // 편차 표
  const bestHi=d=>Math.max.apply(null,gs.map(g=>(g.rankDom.find(x=>x[0]===d)||[0,-99])[1]));
  let t='<div style="overflow:auto"><table style="font-size:12.5px"><tr><th style="text-align:left"></th>'+gs.map((g,k)=>'<th style="color:'+dcol(k)+'">'+g.sgg+'</th>').join('')+'</tr>';
  t+='<tr><td style="text-align:left"><b>평균 종합지수</b></td>'+gs.map(g=>'<td class="n"><b style="color:'+color(g.nli)+'">'+g.nli.toFixed(1)+'</b></td>').join('')+'</tr>';
  t+='<tr><td style="text-align:left">전국 취약순위</td>'+gs.map(g=>'<td class="n">'+rankOf.get(g.key)+'/'+rows.length+'</td>').join('')+'</tr>';
  t+='<tr><td style="text-align:left">사각지대 / 관할동 / 인구</td>'+gs.map(g=>'<td class="n">'+g.blindN+' / '+g.dongs.length+' / '+nf(g.pop)+'</td>').join('')+'</tr>';
  DKEYS.forEach(function(d){const hi=Math.round(bestHi(d));t+='<tr><td style="text-align:left">'+DOMINFO[d][0]+' '+SHORT[d]+'</td>'+gs.map(function(g){const dv=Math.round((g.rankDom.find(x=>x[0]===d)||[0,0])[1]);return '<td class="n" style="color:'+(dv<0?'#b0603f':'#2f6b4e')+';'+(dv===hi?'background:#e4f0e8;font-weight:800':'')+'">'+(dv>=0?'+':'')+dv+'</td>';}).join('')+'</tr>';});
  t+='</table></div>';
  let bl='';gs.filter(g=>g.blindN).forEach(function(g){bl+='<div style="margin-top:10px"><div class="fld" style="font-size:11.5px">'+g.sgg+' <span class="muted" style="font-weight:400;text-transform:none;letter-spacing:0">'+g.blindN+'건 · 상위 5</span></div><div style="overflow:auto"><table style="font-size:12px;margin-top:4px"><tr><th style="text-align:left">동</th><th>인구</th><th style="text-align:left">취약</th><th>점수</th></tr>'+g.blind.slice(0,5).map(b=>'<tr onclick="goDetail(\''+b.p.adm_nm+'\')" style="cursor:pointer"><td style="text-align:left">'+b.p.adm_nm+'</td><td class="n">'+nf(b.p.pop_total)+'</td><td style="text-align:left">'+METRICS[b.d]+'</td><td class="n" style="color:#b0603f;font-weight:700">'+Math.round(b.v)+'</td></tr>').join('')+'</table></div></div>';});
  // 산점도 축 옵션
  const xo=['dens','price','eld','yth','apt','old','pop'],yo=['NLI'].concat(DKEYS);
  const sel=(id,opts,def)=>'<select id="'+id+'" onchange="renderDStatScatter()" style="font-size:12px;padding:4px 8px">'+opts.map(k=>'<option value="'+k+'"'+(k===def?' selected':'')+'>'+VARS[k]+'</option>').join('')+'</select>';
  document.getElementById('diagStatBody').innerHTML=
    '<div class="flex" style="justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap"><h2 style="margin:0">'+(single?gs[0].sido+' '+gs[0].sgg:gs.length+'개 지자체 비교 분석')+'</h2><div class="muted">관할 동 '+dongs.length+'개 · 표 편차=전국 지자체 평균 대비 · 셀·점 호버 시 상세, 동 클릭 시 지도</div></div>'
    +'<div class="statgrid">'
    +'<div class="sc"><h4>도메인 프로파일 <span>레이더 · 평균 점수(백분위)</span></h4><div style="text-align:center">'+radar+'</div>'+legend+'</div>'
    +'<div class="sc"><h4>종합지수 · 사각지대</h4><div class="fld" style="font-size:11px">평균 종합지수</div>'+nliBars+'<div class="fld" style="font-size:11px;margin-top:12px">사각지대(동×도메인)</div>'+blBars+'</div>'
    +'<div class="sc"><h4>함께 갖춰지는 도메인 <span>관할 동 기준 · 두 도메인이 같이 좋은 정도(초록=동반)</span></h4><div style="overflow:auto">'+dc+'</div></div>'
    +'<div class="sc"><h4>지역 특성 ↔ 생활여건 <span>인구밀도·고령 등이 도메인과 연관되는 정도(초록=정비례)</span></h4><div style="overflow:auto">'+rh+'</div></div>'
    +'<div class="sc"><h4>지자체 × 도메인 점수 <span>평균 점수 · 초록 높음</span></h4><div style="overflow:auto">'+hm+'</div></div>'
    +'<div class="sc span2"><h4>⣿ 관할 동 산점도 <span>축 선택 · 점=동(호버·클릭) · 색=지자체</span></h4><div class="flex" style="gap:8px;margin-bottom:8px;font-size:12px">X '+sel('dsX',xo,'dens')+' Y '+sel('dsY',yo,'NLI')+' <span id="dsReg" class="muted"></span></div><div id="dsScatterBox"></div></div>'
    +'<div class="sc"><h4>도메인 편차 표 <span>전국 지자체 평균 대비 · 행별 최고 초록</span></h4>'+t+'</div>'
    +(bl?'<div class="sc"><h4>사각지대 동 <span>클릭 → 지도 상세</span></h4>'+bl+'</div>':'')
    +'</div>';
  document.getElementById('diagStatModal').style.display='flex';
  renderDStatScatter();
}
function renderDStatScatter(){
  if(!_dstat)return;const box=document.getElementById('dsScatterBox');if(!box)return;
  const xk=document.getElementById('dsX').value,yk=document.getElementById('dsY').value;
  const pts=_dstat.dongs.map(o=>({x:sval(o.p,xk),y:sval(o.p,yk),k:o.k,adm:o.p.adm_nm,nm:o.p.full_nm||o.p.adm_nm})).filter(a=>a.x!=null&&a.y!=null&&!isNaN(a.x)&&!isNaN(a.y));
  if(pts.length<3){box.innerHTML='<div class="muted" style="font-size:12px">표시할 동 데이터가 부족합니다.</div>';document.getElementById('dsReg').textContent='';return;}
  const xs=pts.map(a=>a.x),ys=pts.map(a=>a.y),r=ols(xs,ys),xmin=Math.min.apply(null,xs),xmax=Math.max.apply(null,xs),ymin=Math.min.apply(null,ys),ymax=Math.max.apply(null,ys);
  const W=880,H=320,pd=44,sx=v=>pd+(v-xmin)/((xmax-xmin)||1)*(W-2*pd),sy=v=>H-pd-(v-ymin)/((ymax-ymin)||1)*(H-2*pd);
  let g='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="xMidYMid meet" style="width:100%;max-height:440px;display:block"><line x1="'+pd+'" y1="'+(H-pd)+'" x2="'+(W-pd)+'" y2="'+(H-pd)+'" stroke="#ddd"/><line x1="'+pd+'" y1="'+pd+'" x2="'+pd+'" y2="'+(H-pd)+'" stroke="#ddd"/>';
  g+=pts.map(a=>'<circle cx="'+sx(a.x).toFixed(1)+'" cy="'+sy(a.y).toFixed(1)+'" r="3.6" fill="'+_dstat.dcol(a.k)+'" opacity=".72" style="cursor:pointer" onclick="goDetail(\''+a.adm+'\')"><title>'+a.nm+' · '+VARS[xk]+' '+a.x.toFixed(1)+' · '+VARS[yk]+' '+a.y.toFixed(1)+'</title></circle>').join('');
  if(!isNaN(r.slope))g+='<line x1="'+sx(xmin).toFixed(1)+'" y1="'+sy(r.intercept+r.slope*xmin).toFixed(1)+'" x2="'+sx(xmax).toFixed(1)+'" y2="'+sy(r.intercept+r.slope*xmax).toFixed(1)+'" stroke="#c0392b" stroke-width="2"/>';
  g+='<text x="'+(W/2)+'" y="'+(H-8)+'" font-size="12" text-anchor="middle" fill="#5b6b77">'+VARS[xk]+' →</text><text x="14" y="'+(H/2)+'" font-size="12" fill="#5b6b77" text-anchor="middle" transform="rotate(-90 14 '+(H/2)+')">↑ '+VARS[yk]+'</text></svg>';
  box.innerHTML=g;
  const R=r.r||0;document.getElementById('dsReg').innerHTML='· <b>R² '+r.r2.toFixed(2)+'</b> · r '+R.toFixed(2)+' · n='+r.n;
}
function toggleDiagCmp(k){const i=diagCmp.indexOf(k);if(i>=0)diagCmp.splice(i,1);else diagCmp.push(k);renderDiag();}
function renderDiagCmp(){const el=document.getElementById('diagCmp');if(el){el.style.display='none';el.innerHTML='';}}
function diagToMap(){
  if(!diagCur||!map)return;const g=diagCur.g,dom=g.rankDom[0][0];
  mMode=g.blindN?'blind':'basic';
  document.querySelectorAll('#modes button').forEach(x=>x.classList.toggle('on',x.dataset.m===mMode));
  document.querySelector('nav .tab[data-v=map]').click();
  const s=document.getElementById('metric');if(s){s.value=dom;s.dispatchEvent(new Event('change'));}
  map.invalidateSize();
  const b=L.latLngBounds([]);g.dongs.forEach(p=>{if(p._l){const lb=p._l.getBounds();if(lb&&lb.isValid())b.extend(lb);}});
  if(b.isValid())map.fitBounds(b,{padding:[30,30]});
}
recompRank();initMap();showTab('map');
attachAC(document.getElementById('gsearch'),document.getElementById('gac'),goDetail);
attachAC(document.getElementById('findSearch'),document.getElementById('findsac'),findShowDong);
attachAC(document.getElementById('cmpSearch'),document.getElementById('cmpac'),adm=>{addCmp(adm)});
document.getElementById('cmpClear').onclick=()=>{cmp=[];renderCmpPanel();};
attachAC(document.getElementById('rankBase'),document.getElementById('rankbac'),setCommuteBase);
document.querySelectorAll('#recHouseSeg button').forEach(b=>b.onclick=()=>recSetHouse(b.dataset.h,b));
attachAC(document.getElementById('recBase'),document.getElementById('recbac'),recPickBase);
document.getElementById('commuteKm').oninput=function(){commuteKm=+this.value;document.getElementById('commuteKmV').textContent=commuteKm+'km';renderRank();writeHash();};
document.getElementById('commuteClear').onclick=()=>{commuteBase=null;document.getElementById('commuteInfo').innerHTML='';document.getElementById('commuteKmWrap').style.display='none';document.getElementById('rankBase').value='';renderRank();writeHash();};
document.querySelectorAll('select').forEach(customSelect);
// 모바일 사이드바 접이식
(function(){const as=document.querySelector('#v-map aside'),bd=document.getElementById('asideBackdrop'),tg=document.getElementById('asideToggle');
  const close=()=>{as.classList.remove('open');bd.classList.remove('on')};
  tg.onclick=()=>{const o=as.classList.toggle('open');bd.classList.toggle('on',o)};bd.onclick=close;
  as.addEventListener('change',()=>{if(window.innerWidth<=820)close()});})();
applyHash();   // 딥링크로 진입 시 상태 복원(_boot 폴백으로 최초 해시 확보)
window.addEventListener('hashchange',applyHash);   // 해시 변경(딥링크 재진입) 대응
growBars();
setTimeout(()=>{if(map)map.invalidateSize();},120);
</script></body></html>'''

html = TEMPLATE.replace("__GEOJSON__", geojson)
open("nli_map.html", "w", encoding="utf-8").write(html)
# 시설포인트를 산출물 옆(리포 루트)에 복사 → index.html이 fetch('nli_points.json')로 지연로딩
shutil.copy("data/processed/nli_points.json", "nli_points.json")
print("생성 nli_map.html |", round(os.path.getsize("nli_map.html")/1e6, 1), "MB",
      "| nli_points.json", round(os.path.getsize("nli_points.json")/1e6, 1), "MB (지연로딩)")
