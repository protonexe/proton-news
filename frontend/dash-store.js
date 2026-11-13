/* ===== PROTON-NEWS DASH — article store (IndexedDB) =====
   Keeps every extracted body on the user's machine so saved stories read
   offline, reopening is instant, and body search works without the network. */
(function(){
  const DB="pn_dash_articles", VER=1, STORE="articles";
  let dbp=null;

  function open(){
    if(dbp) return dbp;
    dbp=new Promise((res,rej)=>{
      try{
        if(!window.indexedDB) throw new Error("indexeddb unavailable");
        const r=indexedDB.open(DB,VER);
        r.onupgradeneeded=()=>{
          const db=r.result;
          if(!db.objectStoreNames.contains(STORE)){
            const st=db.createObjectStore(STORE,{keyPath:"link"});
            st.createIndex("savedAt","savedAt");
            st.createIndex("ts","ts");
          }
        };
        r.onsuccess=()=>res(r.result);
        r.onerror=()=>rej(r.error||new Error("indexeddb error"));
      }catch(e){rej(e);}
    });
    return dbp;
  }

  function run(mode,fn){
    return open().then(db=>new Promise((res,rej)=>{
      let out;
      let t;
      try{ t=db.transaction(STORE,mode); }catch(e){ rej(e); return; }
      const req=fn(t.objectStore(STORE));
      if(req) req.onsuccess=()=>{ out=req.result; };
      t.oncomplete=()=>res(out);
      t.onerror=()=>rej(t.error||new Error("indexeddb tx failed"));
      t.onabort=()=>rej(t.error||new Error("indexeddb tx aborted"));
    }));
  }

  function put(rec){
    if(!rec||!rec.link) return Promise.resolve(false);
    return run("readwrite",st=>st.put(rec)).then(()=>true).catch(()=>false);
  }
  function get(link){
    if(!link) return Promise.resolve(null);
    return run("readonly",st=>st.get(link)).catch(()=>null);
  }
  function del(link){
    if(!link) return Promise.resolve(false);
    return run("readwrite",st=>st.delete(link)).then(()=>true).catch(()=>false);
  }
  function all(){
    return run("readonly",st=>st.getAll()).then(rows=>rows||[]).catch(()=>[]);
  }

  async function search(q,limit){
    const needle=String(q||"").trim().toLowerCase();
    if(needle.length<2) return [];
    const rows=await all();
    const out=[];
    for(const r of rows){
      const d=r.payload||{};
      const title=String(d.title||r.title||"");
      const body=(d.paragraphs||[]).join(" ");
      const hay=(title+" "+body).toLowerCase();
      const idx=hay.indexOf(needle);
      if(idx<0) continue;
      const src=body||title;
      const bi=body.toLowerCase().indexOf(needle);
      const at=bi>=0?bi:0;
      const snippet=src.slice(Math.max(0,at-60),at+needle.length+130).trim();
      out.push({
        link:r.link,title,source:r.source||d.site||"",savedAt:r.savedAt||null,
        words:d.words||0,snippet:(at>60?"…":"")+snippet+(at+needle.length+130<src.length?"…":""),
        local:true
      });
      if(out.length>=(limit||40)) break;
    }
    return out;
  }

  window.PNStore={put,get,del,all,search};
})();
