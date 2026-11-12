/* shared mock data + helpers for the UI demos */
window.MOCK = [
  {category:"NORTH AMERICA",country:"United States of America",sector:"POLITICS",source:"npr.org",title:"Senate advances stopgap funding bill hours before deadline",summary:"The measure keeps agencies funded through mid-January while negotiators continue talks on a full-year package.",ts:Date.now()/1000-420},
  {category:"WESTERN EUROPE",country:"Germany",sector:"ENERGY",source:"dw.com",title:"Grid operator warns winter reserve margins are thinner than last year",summary:"Cold-weather demand plus two offline reactors leave utilities leaning on imports from neighbours.",ts:Date.now()/1000-1500},
  {category:"EAST ASIA",country:"Japan",sector:"TECH",source:"nhk.or.jp",title:"Chipmakers agree joint pilot line for 2nm process",summary:"Three suppliers will share a test fab in Kumamoto, targeting risk production by late 2027.",ts:Date.now()/1000-2600},
  {category:"MIDDLE EAST",country:"Saudi Arabia",sector:"FINANCE",source:"arabnews.com",title:"Sovereign fund trims overseas property exposure",summary:"Allocation shifts toward domestic logistics and grid infrastructure, according to the quarterly filing.",ts:Date.now()/1000-3900},
  {category:"SE ASIA / OCEANIA",country:"Australia",sector:"CLIMATE",source:"abc.net.au",title:"Bureau confirms third consecutive La Nina pattern",summary:"Forecasters expect above-average rainfall across the east coast through February.",ts:Date.now()/1000-5400},
  {category:"NORTH AMERICA",country:"Canada",sector:"GENERAL",source:"cbc.ca",title:"Rail corridor reopens after derailment cleanup",summary:"Freight traffic resumes on one track while investigators examine the second.",ts:Date.now()/1000-7200},
  {category:"UK & IRELAND",country:"United Kingdom",sector:"FINANCE",source:"ft.com",title:"Gilt yields slip as inflation prints below consensus",summary:"Markets now price two cuts before spring, up from one at the start of the week.",ts:Date.now()/1000-9300},
  {category:"LATIN AMERICA",country:"Brazil",sector:"ENERGY",source:"folha.uol.com.br",title:"Hydro reservoirs recover to 68% after heavy rains",summary:"Regulators say no emergency tariff flag is expected before the new year.",ts:Date.now()/1000-11500},
  {category:"SOUTH ASIA",country:"India",sector:"TECH",source:"thehindu.com",title:"Payment network clears 14bn transactions in October",summary:"Volume growth is fastest in tier-2 cities, driven by merchant QR adoption.",ts:Date.now()/1000-14000},
  {category:"EAST ASIA",country:"China",sector:"FINANCE",source:"scmp.com",title:"Property developer completes offshore restructuring",summary:"Creditors approved the plan with 92% support, ending an 18-month negotiation.",ts:Date.now()/1000-17200},
  {category:"NORTHERN EUROPE",country:"Sweden",sector:"TECH",source:"thelocal.se",title:"Battery plant expansion adds 1,200 roles",summary:"The second phase doubles cathode output for European automakers.",ts:Date.now()/1000-20000},
  {category:"AFRICA",country:"Nigeria",sector:"ENERGY",source:"punchng.com",title:"Refinery ramps to 60% as crude supply stabilises",summary:"Domestic fuel queues shorten for the first time in six weeks.",ts:Date.now()/1000-24000}
];

window.ago = function(ts){
  if(!ts) return "";
  const s = Math.max(0, Date.now()/1000 - ts);
  if (s < 60) return "just now";
  if (s < 3600) return Math.floor(s/60) + "m ago";
  if (s < 86400) return Math.floor(s/3600) + "h ago";
  return Math.floor(s/86400) + "d ago";
};

window.loadStories = async function(n){
  try {
    const r = await fetch('/news?limit=' + (n || 20));
    if (!r.ok) throw new Error('http');
    const d = await r.json();
    if (!Array.isArray(d) || !d.length) throw new Error('empty');
    return d;
  } catch (e) {
    return window.MOCK;
  }
};

window.mockMatches = [
  {league:"NBA",a:"NYK",b:"BOS",sa:104,sb:109,q:"Q4 02:11",live:true},
  {league:"NFL",a:"DET",b:"CHI",sa:21,sb:17,q:"Q3 08:40",live:true},
  {league:"EPL",a:"ARS",b:"LIV",sa:1,sb:1,q:"FT",live:false},
  {league:"NHL",a:"TOR",b:"MTL",sa:3,sb:2,q:"2ND 14:02",live:true},
  {league:"UCL",a:"RMA",b:"MCI",sa:2,sb:2,q:"FT",live:false},
  {league:"MLB",a:"LAD",b:"SD",sa:4,sb:1,q:"FINAL",live:false}
];

window.mockMarkets = [
  {s:"SPX",p:"6,842.10",c:0.62},{s:"NDX",p:"24,118.40",c:1.08},
  {s:"DJI",p:"47,905.32",c:-0.21},{s:"BTC",p:"104,882",c:2.34},
  {s:"ETH",p:"3,942",c:1.71},{s:"OIL",p:"71.44",c:-1.12}
];
