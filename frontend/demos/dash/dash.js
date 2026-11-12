/* ===== PROTON-NEWS DASH v2 — shared runtime ===== */
(function(){
  const Themes=[
    {id:"green",  name:"P1 GREEN",   hex:"#00cc00"},
    {id:"amber",  name:"P3 AMBER",   hex:"#ffb000"},
    {id:"ice",    name:"ICE BLUE",   hex:"#5fd7ff"},
    {id:"mono",   name:"PAPER WHITE",hex:"#e8e8e8"},
    {id:"magenta",name:"MAGENTA",    hex:"#ff4fd8"},
    {id:"violet", name:"ULTRAVIOLET",hex:"#a48cff"}
  ];
  const THEME_KEY="pn_dash_theme_v2";
  const PAGES=[
    ["index.html","DASHBOARD"],["news.html","NEWS"],["finance.html","FINANCE"],
    ["sports.html","SPORTS"],["weather.html","WEATHER"],["world.html","WORLD"],
    ["planes.html","PLANES"],["customize.html","CUSTOMIZE"]
  ];

  function current(){return localStorage.getItem(THEME_KEY)||"mono";}
  function themeById(id){return Themes.find(t=>t.id===id)||Themes[0];}

  function applyTheme(id,silent){
    const t=themeById(id);
    document.documentElement.dataset.theme=t.id;
    localStorage.setItem(THEME_KEY,t.id);
    const btn=document.getElementById("theme-btn");
    if(btn) btn.textContent="[ ◐ "+t.name+" ]";
    document.querySelectorAll("[data-theme-pick]").forEach(n=>
      n.classList.toggle("act",n.dataset.themePick===t.id));
    if(!silent) toast("theme: "+t.name);
  }

  function themePanel(){
    if(document.getElementById("theme-panel"))return;
    const p=document.createElement("div");
    p.id="theme-panel";
    p.innerHTML="<h4>phosphor / palette</h4>"+Themes.map(t=>
      `<button class="th-row" data-theme-pick="${t.id}">
         <span class="sw" style="background:${t.hex}"></span>
         <span class="nm">${t.name}</span><span class="ck">${t.hex}</span>
       </button>`).join("")+
      `<div class="hint">saved to this browser · applies to every dash page · CRT scanlines stay on</div>`;
    document.body.appendChild(p);
    p.querySelectorAll("[data-theme-pick]").forEach(b=>b.onclick=()=>{
      applyTheme(b.dataset.themePick);
      p.classList.remove("open");
    });
    document.addEventListener("click",e=>{
      if(!p.classList.contains("open"))return;
      if(!p.contains(e.target)&&e.target.id!=="theme-btn")p.classList.remove("open");
    });
  }

  function mountHeader(active){
    const host=document.getElementById("top");
    if(!host)return;
    host.className="top";
    host.innerHTML=`
      <a class="brand" href="index.html"><b>&gt; PROTON</b>-NEWS<small>DASHBOARD v2 // DEMO</small></a>
      <nav class="crumbs">${PAGES.map(([h,l])=>
        `<a href="${h}" class="${h===active?"act":""}">[ ${l} ]</a>`).join("")}</nav>
      <div class="hright"><span id="clocks"></span><button id="theme-btn">[ ◐ PAPER WHITE ]</button></div>`;
    document.getElementById("theme-btn").onclick=e=>{
      e.stopPropagation();
      themePanel();
      document.getElementById("theme-panel").classList.toggle("open");
    };
    themePanel();
    applyTheme(current(),true);
    clocks();
  }

  const tz=(z)=>{try{return new Intl.DateTimeFormat("en-GB",{timeZone:z,hour:"2-digit",minute:"2-digit",hour12:false}).format(new Date())}catch(e){return "--:--"}};
  function clocks(){
    const el=document.getElementById("clocks");
    if(!el)return;
    el.textContent="NYC "+tz("America/New_York")+" · LDN "+tz("Europe/London")+" · TYO "+tz("Asia/Tokyo")+" · SYD "+tz("Australia/Sydney");
  }

  function ago(ts){
    if(!ts)return "";
    const s=Math.max(0,Date.now()/1000-ts);
    if(s<60)return "just now";
    if(s<3600)return Math.floor(s/60)+"m ago";
    if(s<86400)return Math.floor(s/3600)+"h ago";
    return Math.floor(s/86400)+"d ago";
  }
  function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
  function fmtPct(v){const n=Number(v);if(!isFinite(n))return "—";return (n>=0?"+":"")+n.toFixed(2)+"%";}
  function fmtNum(v,d){const n=Number(v);if(!isFinite(n))return "—";return n.toLocaleString(undefined,{maximumFractionDigits:d==null?2:d});}

  async function fetchJSON(url,ms){
    const ctrl=new AbortController();
    const t=setTimeout(()=>ctrl.abort(),ms||14000);
    try{
      const r=await fetch(url,{signal:ctrl.signal});
      if(!r.ok)throw new Error("HTTP "+r.status);
      return await r.json();
    }finally{clearTimeout(t);}
  }

  const MOCK=[
    {category:"NORTH AMERICA",country:"United States of America",sector:"POLITICS",source:"npr.org",title:"Senate advances stopgap funding bill hours before deadline",summary:"The measure keeps agencies funded through mid-January while negotiators continue talks on a full-year package.",ts:Date.now()/1000-420,link:"https://www.npr.org/"},
    {category:"WESTERN EUROPE",country:"Germany",sector:"ENERGY",source:"dw.com",title:"Grid operator warns winter reserve margins are thinner than last year",summary:"Cold-weather demand plus two offline reactors leave utilities leaning on imports from neighbours.",ts:Date.now()/1000-1500,link:"https://www.dw.com/"},
    {category:"EAST ASIA",country:"Japan",sector:"TECH",source:"nhk.or.jp",title:"Chipmakers agree joint pilot line for 2nm process",summary:"Three suppliers will share a test fab in Kumamoto, targeting risk production by late 2027.",ts:Date.now()/1000-2600,link:"https://www3.nhk.or.jp/"},
    {category:"MIDDLE EAST",country:"Saudi Arabia",sector:"FINANCE",source:"arabnews.com",title:"Sovereign fund trims overseas property exposure",summary:"Allocation shifts toward domestic logistics and grid infrastructure, according to the quarterly filing.",ts:Date.now()/1000-3900,link:"https://www.arabnews.com/"},
    {category:"SE ASIA / OCEANIA",country:"Australia",sector:"CLIMATE",source:"abc.net.au",title:"Bureau confirms third consecutive La Nina pattern",summary:"Forecasters expect above-average rainfall across the east coast through February.",ts:Date.now()/1000-5400,link:"https://www.abc.net.au/news/"},
    {category:"NORTH AMERICA",country:"Canada",sector:"GENERAL",source:"cbc.ca",title:"Rail corridor reopens after derailment cleanup",summary:"Freight traffic resumes on one track while investigators examine the second.",ts:Date.now()/1000-7200,link:"https://www.cbc.ca/"},
    {category:"UK & IRELAND",country:"United Kingdom",sector:"FINANCE",source:"ft.com",title:"Gilt yields slip as inflation prints below consensus",summary:"Markets now price two cuts before spring, up from one at the start of the week.",ts:Date.now()/1000-9300,link:"https://www.ft.com/"},
    {category:"LATIN AMERICA",country:"Brazil",sector:"ENERGY",source:"folha.uol.com.br",title:"Hydro reservoirs recover to 68% after heavy rains",summary:"Regulators say no emergency tariff flag is expected before the new year.",ts:Date.now()/1000-11500,link:"https://www1.folha.uol.com.br/"},
    {category:"SOUTH ASIA",country:"India",sector:"TECH",source:"thehindu.com",title:"Payment network clears 14bn transactions in October",summary:"Volume growth is fastest in tier-2 cities, driven by merchant QR adoption.",ts:Date.now()/1000-14000,link:"https://www.thehindu.com/"},
    {category:"EAST ASIA",country:"China",sector:"FINANCE",source:"scmp.com",title:"Property developer completes offshore restructuring",summary:"Creditors approved the plan with 92% support, ending an 18-month negotiation.",ts:Date.now()/1000-17200,link:"https://www.scmp.com/"},
    {category:"NORTHERN EUROPE",country:"Sweden",sector:"TECH",source:"thelocal.se",title:"Battery plant expansion adds 1,200 roles",summary:"The second phase doubles cathode output for European automakers.",ts:Date.now()/1000-20000,link:"https://www.thelocal.se/"},
    {category:"AFRICA",country:"Nigeria",sector:"ENERGY",source:"punchng.com",title:"Refinery ramps to 60% as crude supply stabilises",summary:"Domestic fuel queues shorten for the first time in six weeks.",ts:Date.now()/1000-24000,link:"https://punchng.com/"}
  ];

  async function loadStories(){
    try{
      const d=await fetchJSON("/news/quick?limit=60",16000);
      if(Array.isArray(d)&&d.length)return d;
    }catch(e){}
    try{
      const d=await fetchJSON("/news?limit=24",16000);
      if(Array.isArray(d)&&d.length)return d;
    }catch(e){}
    return MOCK;
  }

  const mockMarkets=[
    {s:"SPX",p:"6,842.10",c:0.62},{s:"NDX",p:"24,118.40",c:1.08},
    {s:"DJI",p:"47,905.32",c:-0.21},{s:"BTC",p:"104,882",c:2.34},
    {s:"ETH",p:"3,942",c:1.71},{s:"WTI",p:"71.44",c:-1.12}
  ];
  const mockMatches=[
    {league:"NBA",a:"NYK",b:"BOS",sa:104,sb:109,q:"Q4 02:11",live:true},
    {league:"NFL",a:"DET",b:"CHI",sa:21,sb:17,q:"Q3 08:40",live:true},
    {league:"EPL",a:"ARS",b:"LIV",sa:1,sb:1,q:"FT",live:false},
    {league:"NHL",a:"TOR",b:"MTL",sa:3,sb:2,q:"2ND 14:02",live:true},
    {league:"UCL",a:"RMA",b:"MCI",sa:2,sb:2,q:"FT",live:false},
    {league:"MLB",a:"LAD",b:"SD",sa:4,sb:1,q:"FINAL",live:false}
  ];

  let toastTimer;
  function toast(msg){
    let t=document.getElementById("toast");
    if(!t){t=document.createElement("div");t.id="toast";document.body.appendChild(t);}
    t.textContent=msg;t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer=setTimeout(()=>t.classList.remove("show"),2000);
  }

  window.PN={
    Themes,applyTheme,current,themeById,mountHeader,esc,ago,fmtPct,fmtNum,fetchJSON,
    loadStories,mockMarkets,mockMatches,toast,MOCK
  };

  document.addEventListener("DOMContentLoaded",()=>{
    clocks();setInterval(clocks,1000);
  });
})();
