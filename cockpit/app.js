"use strict";
const $ = id => document.getElementById(id);
const esc = s => String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const flat = s => String(s==null?"":s).replace(/<br\s*\/?>/gi," ").replace(/\s+/g," ").trim();

let TODAY = midnight();
function midnight(){const d=new Date();return new Date(d.getFullYear(),d.getMonth(),d.getDate());}
function pd(s){const m=/^(\d{4})-(\d{2})-(\d{2})/.exec(String(s||""));return m?new Date(+m[1],+m[2]-1,+m[3]):null;}
function dd(s){const d=pd(s);return d?Math.round((d-TODAY)/864e5):null;}
function md(s){const d=pd(s);return d?(d.getMonth()+1)+"/"+d.getDate():"—";}
function ymd(s){const d=pd(s);return d?d.getFullYear()+"/"+(d.getMonth()+1)+"/"+d.getDate():"未設定";}
const yen = n => (n==null||isNaN(n)||n===0)?"—":"¥"+Math.round(n).toLocaleString("ja-JP");
const man = n => (n==null||isNaN(n))?"—":Math.round(n/1e4).toLocaleString("ja-JP");
const blank = v => {const s=String(v==null?"":v).trim();return !s||/^[（(]\s*要記入\s*[)）]/.test(s);};
const rel = v => {try{const a=JSON.parse(v||"[]");return Array.isArray(a)?a:[];}catch(e){return[];}};
const base = t => String(t||"").replace(/[（(]\s*(着手金|残金)\s*[)）]\s*$/,"").trim();

const STAGES=["作成中","送付済","商談中","受注","保留","失注"];
const ACTIVE={"作成中":1,"送付済":1,"商談中":1};
const IDLE=90;
let D=null, tab="today";

function buildDeals(rows){
  const map={},order=[];
  rows.forEach(r=>{
    const sp=r["請求区分"]==="着手金"||r["請求区分"]==="残金";
    const key=sp?(r["クライアント"]||"")+"␟"+base(r["提案名"]):"u␟"+r.url;
    let d=map[key];
    if(!d){d={key,url:r.url,name:sp?base(r["提案名"]):(r["提案名"]||"（無題）"),client:r["クライアント"]||"",
      stage:r["ステージ"]||"",kind:r["見積種別"]||"",channel:r["チャネル"]||"",split:sp,parts:0,
      amount:0,cost:0,hasCost:false,due:null,sent:null,resume:null,next:"",delivery:""};map[key]=d;order.push(d);}
    d.parts++;
    if(typeof r["金額"]==="number")d.amount+=r["金額"];
    if(r["印刷原価"]!=null||r["制作原価"]!=null){d.hasCost=true;d.cost+=(r["印刷原価"]||0)+(r["制作原価"]||0);}
    const due=r["date:次アクション期日:start"];
    if(due&&(!d.due||pd(due)<pd(d.due)))d.due=due;
    if(r["date:送付日:start"])d.sent=r["date:送付日:start"];
    if(r["date:再開予定:start"])d.resume=r["date:再開予定:start"];
    if(r["納品状況"])d.delivery=r["納品状況"];
    if((r["次アクション"]||"").length>d.next.length)d.next=r["次アクション"]||"";
  });
  return order;
}

function triage(deals,exts,clients){
  const t={overdue:[],soon:[],stalled:[],needsField:[],funnel:[],idle:[],resuming:[],noStage:[]};
  deals.forEach(d=>{
    if(d.stage==="保留"){const n=dd(d.resume);if(n!=null&&n<=30)t.resuming.push({d,n});return;}
    if(!d.stage){t.noStage.push(d);return;}
    if(!ACTIVE[d.stage])return;
    const n=dd(d.due);
    if(d.due==null){if(d.stage==="商談中")t.stalled.push(d);}
    else if(n<0)t.overdue.push({kind:"提案",d,n});
    else if(n<=3)t.soon.push({kind:"提案",d,n});
    if(d.stage==="送付済"&&!d.sent)t.funnel.push(d);
  });
  exts.forEach(e=>{
    if(e["ステータス"]==="受注"||e["ステータス"]==="見送り")return;
    const n=dd(e["date:期日:start"]);
    if(n!=null){if(n<0)t.overdue.push({kind:"拡張",e,n});else if(n<=3)t.soon.push({kind:"拡張",e,n});}
    if(blank(e["着手条件"]))t.needsField.push({type:"着手条件",title:e["案件名"],url:e.url,meta:(e["ステータス"]||"")+" / 確度"+(e["確度"]||"—")});
  });
  clients.forEach(c=>{
    if(c["ステータス"]==="休眠"&&blank(c["再開条件"])){
      const q=dd(c["date:直近請求日:start"]);
      t.needsField.push({type:"再開条件",title:c["企業名"],url:c.url,meta:"休眠"+(q!=null?" / "+(-q)+"日経過":"")});
    }
    if(c["ステータス"]==="取引中"||c["ステータス"]==="納品済"){
      const q=dd(c["date:直近請求日:start"]);
      if(q!=null&&-q>=IDLE)t.idle.push({c,days:-q});
    }
  });
  t.overdue.sort((a,b)=>a.n-b.n);t.soon.sort((a,b)=>a.n-b.n);
  t.resuming.sort((a,b)=>a.n-b.n);t.idle.sort((a,b)=>b.days-a.days);
  return t;
}

const delta = n => n==null?'<span class="d ok">期日なし</span>'
  : n<0?`<span class="d crit">${-n}日超過</span>`
  : n===0?'<span class="d crit">今日</span>'
  : n<=3?`<span class="d warn">あと${n}日</span>`:`<span class="d ok">あと${n}日</span>`;

function row(o){return `<a class="row ${o.sv}" href="${esc(o.url||"#")}" target="_blank" rel="noopener">
  <span class="st"></span><span class="rm"><span class="rt">${esc(o.title)}</span>
  <span class="rmeta">${o.meta}</span>${o.note?`<span class="rnote">${esc(flat(o.note))}</span>`:""}</span>
  <span class="rs">${o.side}</span></a>`;}
function sec(title,n,why,body){return `<div class="sec"><h2><span class="bar"></span>${esc(title)}
  <span class="n">${n===null?"":n+"件"}</span></h2>${why?`<div class="why">${esc(why)}</div>`:""}${body}</div>`;}
const none = m => `<div class="empty">${esc(m||"なし")}</div>`;

function renderToday(){
  const t=D.t;let o="";
  const ar=it=>{const sv=it.n<0?"crit":"warn";
    if(it.kind==="提案"){const d=it.d;return row({sv,url:d.url,title:d.name,note:d.next,
      meta:`<span class="pill">${esc(d.stage)}</span><span>${esc(d.client)}</span>`+(d.split?`<span class="pill">分割${d.parts}行</span>`:""),
      side:(d.amount?`<span class="amt">${yen(d.amount)}</span>`:`<span class="due">金額未定</span>`)+`<span class="due">${md(d.due)}</span>`+delta(it.n)});}
    const e=it.e;return row({sv,url:e.url,title:e["案件名"],note:e["次アクション"],
      meta:`<span class="pill gold">拡張案件</span><span>確度${esc(e["確度"]||"—")}</span>`,
      side:(e["想定金額"]?`<span class="amt">${yen(e["想定金額"])}</span>`:`<span class="due">想定額なし</span>`)+`<span class="due">${md(e["date:期日:start"])}</span>`+delta(it.n)});};
  o+=sec("期日超過",t.overdue.length,"受注・失注・保留は数えない。",t.overdue.length?`<div class="rows">${t.overdue.map(ar).join("")}</div>`:none());
  o+=sec("今日〜3日以内",t.soon.length,"",t.soon.length?`<div class="rows">${t.soon.map(ar).join("")}</div>`:none());
  o+=sec("再開の時期が来た保留案件",t.resuming.length,"保留は失注ではなく時期の問題。放置すると来期見込みが消える。",
    t.resuming.length?`<div class="rows">${t.resuming.map(x=>{const d=x.d,ov=x.n<0;
      return row({sv:ov?"crit":"hold",url:d.url,title:d.name,note:d.next,
        meta:`<span class="pill">保留</span><span>${esc(d.client)}</span><span class="pill">再開 ${ymd(d.resume)}</span>`,
        side:(d.amount?`<span class="amt">${yen(d.amount)}</span>`:"")+`<span class="due">${md(d.resume)}</span><span class="d ${ov?"crit":"warn"}">${ov?(-x.n)+"日超過":"あと"+x.n+"日"}</span>`});}).join("")}</div>`:none("30日以内に再開予定の保留案件はなし"));
  o+=sec("要確認：空欄",t.needsField.length,"着手条件が空欄の拡張案件はアイデアのまま死ぬ。再開条件が空欄の休眠先は永久に休眠のまま終わる。",
    t.needsField.length?`<div class="rows">${t.needsField.map(f=>row({sv:"warn",url:f.url,title:f.title,
      meta:`<span class="pill gold">${esc(f.type)}未記入</span><span>${esc(f.meta)}</span>`,side:`<span class="due">Notionで記入</span>`})).join("")}</div>`:none());
  o+=sec("停滞：商談中だが期日なし",t.stalled.length,"次に何をするか決まっていない商談は止まる。",
    t.stalled.length?`<div class="rows">${t.stalled.map(d=>row({sv:"warn",url:d.url,title:d.name,note:d.next,
      meta:`<span class="pill">商談中</span><span>${esc(d.client)}</span>`,side:(d.amount?`<span class="amt">${yen(d.amount)}</span>`:"")+`<span class="due">期日未設定</span>`})).join("")}</div>`:none());
  o+=sec("ステージ未設定",t.noStage.length,"ステージが空欄の案件は集計から丸ごと漏れる。",
    t.noStage.length?`<div class="rows">${t.noStage.map(d=>row({sv:"warn",url:d.url,title:d.name,
      meta:`<span class="pill gold">ステージ未設定</span><span>${esc(d.client)}</span>`,side:`<span class="due">Notionで設定</span>`})).join("")}</div>`:none());
  o+=sec("計測の穴：送付日が未入力",t.funnel.length,"送付日がないとファネルが測れない。",
    t.funnel.length?`<div class="rows">${t.funnel.map(d=>row({sv:"warn",url:d.url,title:d.name,
      meta:`<span class="pill">送付済</span><span>${esc(d.client)}</span>`,side:`<span class="due">送付日を入れる</span>`})).join("")}</div>`:none());
  const stuck=D.deals.filter(d=>d.stage==="受注"&&(d.delivery==="制作中"||d.delivery==="未着手"))
    .map(d=>({d,days:dd(d.sent||d.due)!=null?-dd(d.sent||d.due):null}));
  o+=sec("納品が動いていない受注案件",stuck.length,
    "受注したまま制作が進んでいない案件。売上は立っているが納品が終わっていない。",
    stuck.length?`<div class="rows">${stuck.map(x=>row({sv:x.d.delivery==="未着手"?"crit":"warn",url:x.d.url,title:x.d.name,note:x.d.next,
      meta:`<span class="pill ${x.d.delivery==="未着手"?"gold":"navy"}">${esc(x.d.delivery)}</span><span>${esc(x.d.client)}</span>`,
      side:(x.d.amount?`<span class="amt">${yen(x.d.amount)}</span>`:"")+`<span class="due">受注済</span>`})).join("")}</div>`:none());
  o+=sec(`放置：直近請求から${IDLE}日以上`,t.idle.length,"会議ではなく直近請求日で見る。納品が回っている顧客ほど会議をしないため。",
    t.idle.length?`<div class="rows">${t.idle.map(x=>row({sv:x.days>=180?"crit":"warn",url:x.c.url,title:x.c["企業名"],note:x.c["再開条件"]||x.c["備考"],
      meta:`<span class="pill">${esc(x.c["ステータス"])}</span><span>${esc(x.c["相手区分"]||"")}</span>`,
      side:`<span class="amt">${yen(x.c["累計売上"])}</span><span class="d ${x.days>=180?"crit":"warn"}">${x.days}日</span>`})).join("")}</div>`:none());
  return o;
}

let pf="active";
function renderPipe(){
  const by={};STAGES.forEach(s=>by[s]={n:0,a:0});
  D.deals.forEach(d=>{if(!by[d.stage])by[d.stage]={n:0,a:0};by[d.stage].n++;by[d.stage].a+=d.amount;});
  const mx=Math.max(...STAGES.map(s=>by[s].a),1);
  const col={"作成中":"var(--label3)","送付済":"var(--blue)","商談中":"var(--orange)","受注":"var(--green)","保留":"var(--accent)","失注":"rgba(120,120,128,.25)"};
  let o=sec("ステージ別",null,"「保留」は時期の問題であって失注ではない。",
    `<div class="stages">${STAGES.map(s=>{const b=by[s],w=Math.max(b.a/mx*100,b.n?1.5:0);
      return `<div class="stage"><span class="nm">${s}</span><span class="tr"><span class="fl" style="width:${w.toFixed(1)}%;background:${col[s]}"></span></span>
      <span class="nu"><b>${b.n}</b>件 ${b.a?man(b.a)+"万":"—"}</span></div>`;}).join("")}</div>`);
  const sh=D.deals.filter(d=>pf==="active"?!!ACTIVE[d.stage]:pf==="won"?d.stage==="受注":pf==="cold"?(d.stage==="保留"||d.stage==="失注"):true)
    .sort((a,b)=>{const i=STAGES.indexOf(a.stage)-STAGES.indexOf(b.stage);return i||(b.amount-a.amount);});
  const seg=`<div class="segwrap">${[["active","進行中"],["won","受注"],["cold","保留・失注"],["all","全部"]]
    .map(x=>`<button class="use" data-pf="${x[0]}" style="${pf===x[0]?"background:var(--surface);box-shadow:0 1px 3px rgba(0,0,0,.14);font-weight:590":""}">${x[1]}</button>`).join("")}</div>`;
  o+=sec("案件一覧",sh.length,"着手金と残金の2行は1案件として統合。粗利は原価が入っている案件のみ実額。",
    seg+`<div class="tw"><table><thead><tr><th>提案</th><th>クライアント</th><th>ステージ</th><th class="n">金額</th><th class="n">粗利</th><th>納品状況</th><th class="n">期日</th></tr></thead><tbody>${
    sh.map(d=>{const n=dd(d.due),g=d.hasCost?d.amount-d.cost:null;
      return `<tr><td><a class="nm" href="${esc(d.url)}" target="_blank">${esc(d.name)}</a>${d.split?` <span class="pill">分割${d.parts}</span>`:""}
        <div class="sub">${esc(flat(d.next).slice(0,80))}</div></td>
        <td>${esc(d.client)}<div class="sub">${esc(d.channel)}</div></td>
        <td><span class="pill">${esc(d.stage)}</span></td><td class="n">${yen(d.amount)}</td>
        <td class="n">${g!=null?yen(g)+`<div class="sub">${d.amount?(g/d.amount*100).toFixed(1)+"%":""}</div>`:'<span class="sub">原価未入力</span>'}</td>
        <td>${d.stage==="受注"?(d.delivery?`<span class="pill ${d.delivery==="納品済"?"ok":d.delivery==="継続納品中"?"wine":"navy"}">${esc(d.delivery)}</span>`:'<span class="pill gold">未記入</span>'):'<span class="sub">—</span>'}</td>
        <td class="n">${d.due?md(d.due)+`<div class="sub">${n<0?(-n)+"日超過":"あと"+n+"日"}</div>`:'<span class="sub">—</span>'}</td></tr>`;}).join("")
    ||'<tr><td colspan="7" class="sub">該当なし</td></tr>'}</tbody></table></div>`);
  return o;
}

let cf="live";
const CF={
  live:  {label:"動いている先", st:["接触中","取引中","相談レベル"], why:"いま接触・取引がある先。まずここを見る。"},
  dig:   {label:"掘り起こし候補", st:["納品済","休眠"], why:"納品済・休眠。受注の8割が紹介なので、ここが次の紹介元になる。消さずに再開条件で管理する。"},
  closed:{label:"終了", st:["破談"], why:"追わないと判断した先。判断理由を残すこと自体に意味があるので削除しない。"},
  all:   {label:"全部", st:null, why:""}
};
function renderClients(){
  const conf=CF[cf];
  const cs=D.clients.filter(c=>!conf.st||conf.st.includes(c["ステータス"]||""))
    .sort((a,b)=>(b["累計売上"]||0)-(a["累計売上"]||0));
  const tot=D.clients.reduce((s,c)=>s+(c["累計売上"]||0),0);
  const counts={};D.clients.forEach(c=>{const k=c["ステータス"]||"—";counts[k]=(counts[k]||0)+1;});
  const seg=`<div class="segwrap">${Object.entries(CF).map(([k,v])=>{
    const n=v.st?D.clients.filter(c=>v.st.includes(c["ステータス"]||"")).length:D.clients.length;
    return `<button class="use" data-cf="${k}" style="${cf===k?"background:var(--surface);box-shadow:0 1px 3px rgba(0,0,0,.14);font-weight:590":""}">${v.label} ${n}</button>`;}).join("")}</div>`;
  const breakdown=`<div class="why" style="margin-left:0">${Object.entries(counts).map(([k,v])=>`${k} ${v}`).join(" ／ ")}</div>`;
  return sec("クライアントマスタ",cs.length,conf.why,seg+breakdown+
    `<div class="tw"><table><thead><tr><th>企業名</th><th>ステータス</th><th class="n">累計売上</th><th class="n">回数</th><th class="n">直近請求</th><th>再開条件</th><th>紹介者</th><th></th></tr></thead><tbody>${
    cs.map(c=>{const q=dd(c["date:直近請求日:start"]),idle=q!=null?-q:null,sh=tot?(c["累計売上"]||0)/tot*100:0;
      const st=c["ステータス"]||"";
      const need=(st==="休眠"||st==="納品済")&&blank(c["再開条件"]);
      const pc=st==="取引中"?"ok":st==="休眠"?"gold":st==="破談"?"":st==="納品済"?"navy":"";
      return `<tr><td><a class="nm" href="${esc(c.url)}" target="_blank">${esc(c["企業名"])}</a>
        <div class="sub">${esc(flat(c["備考"]).slice(0,70))}</div></td>
        <td><span class="pill ${pc}">${esc(st||"—")}</span><div class="sub">${esc(c["相手区分"]||"")}</div></td>
        <td class="n">${yen(c["累計売上"])}${sh>=3?`<div class="sub">${sh.toFixed(1)}%</div>`:""}</td>
        <td class="n">${c["取引回数"]!=null?c["取引回数"]:"—"}</td>
        <td class="n">${q!=null?ymd(c["date:直近請求日:start"])+`<div class="sub" style="color:${idle>=180?"var(--red)":idle>=90?"var(--orange)":"var(--label3)"}">${idle}日</div>`:'<span class="sub">—</span>'}</td>
        <td>${need?'<span class="pill gold">未記入</span>':esc(flat(c["再開条件"]).slice(0,50))||'<span class="sub">—</span>'}</td>
        <td>${esc(c["紹介者"]||"")}<div class="sub">${esc(c["接点の起点"]||"")}</div></td>
        <td><button class="use" data-company="${esc(c["企業名"])}">提案書</button></td></tr>`;}).join("")
    ||'<tr><td colspan="8" class="sub">該当なし</td></tr>'}</tbody></table></div>`);
}

function renderExts(){
  const nm={};D.clients.forEach(c=>nm[c.url]=c["企業名"]);
  const live=D.exts.filter(e=>e["ステータス"]!=="見送り");
  const sum=live.reduce((s,e)=>s+(e["想定金額"]||0),0);
  const rdy=live.filter(e=>!blank(e["着手条件"])).length;
  let o=`<div class="empty" style="border-left:3px solid var(--accent);margin-bottom:18px">
    <b>生きている拡張案件 ${live.length}件・想定 ${man(sum)}万円。うち着手条件が書けているのは ${rdy}件。</b><br>
    着手条件は「いつ・何が起きたら動くか」。空欄の案件はアイデアのまま死ぬ。</div>`;
  ["高","中","低"].forEach(p=>{
    const g=live.filter(e=>e["確度"]===p).sort((a,b)=>(b["想定金額"]||0)-(a["想定金額"]||0));
    o+=sec("確度 "+p,g.length,"",g.length?`<div class="rows">${g.map(e=>{
      const cu=rel(e["クライアント"])[0],cn=cu&&nm[cu]?nm[cu]:"（マスタ未登録）",need=blank(e["着手条件"]),n=dd(e["date:期日:start"]);
      return row({sv:p==="高"?"ok":need?"warn":"hold",url:e.url,title:e["案件名"],
        note:need?"着手条件が未記入。"+flat(e["次アクション"]):"着手条件："+flat(e["着手条件"]),
        meta:`<span class="pill ${need?"gold":""}">${need?"着手条件 未記入":"着手条件あり"}</span><span class="pill">${esc(e["種別"]||"")}</span><span>${esc(cn)}</span>`,
        side:(e["想定金額"]?`<span class="amt">${yen(e["想定金額"])}</span>`:`<span class="due">想定額なし</span>`)+
             (e["date:期日:start"]?`<span class="due">${md(e["date:期日:start"])}</span>`+delta(n):`<span class="due">期日なし</span>`)});}).join("")}</div>`:none());
  });
  return o;
}

let pcf="";
function renderPrices(){
  const rows=D.prices||[];
  const makers=[...new Set(rows.map(r=>r["印刷会社"]||"—"))];
  const seg=`<div class="segwrap">
    <button class="use" data-pcf="" style="${pcf===""?"background:var(--surface);box-shadow:0 1px 3px rgba(0,0,0,.14);font-weight:590":""}">全部 ${rows.length}</button>
    ${makers.map(m=>`<button class="use" data-pcf="${esc(m)}" style="${pcf===m?"background:var(--surface);box-shadow:0 1px 3px rgba(0,0,0,.14);font-weight:590":""}">${esc(m)} ${rows.filter(r=>(r["印刷会社"]||"—")===m).length}</button>`).join("")}</div>`;
  const sh=rows.filter(r=>!pcf||(r["印刷会社"]||"—")===pcf)
    .sort((a,b)=>(a["印刷会社"]||"").localeCompare(b["印刷会社"]||"")
      ||String(a["サイズ"]||"").localeCompare(String(b["サイズ"]||""))
      ||(a["ページ数"]||0)-(b["ページ数"]||0)||(a["部数"]||0)-(b["部数"]||0));
  return sec("印刷単価マスタ",sh.length,
    "同一仕様（印刷会社×サイズ×ページ数×製本方式×本文用紙×部数）は最新見積1行だけを持つ運用。見積日を見て鮮度を判断する。",
    seg+`<div class="tw"><table><thead><tr><th>印刷会社</th><th>サイズ</th><th class="n">P</th><th>製本方式</th><th>本文用紙</th><th class="n">部数</th><th class="n">1部単価</th><th class="n">見積日</th><th>備考</th></tr></thead><tbody>${
    sh.map(r=>{const q=dd(r["date:見積日:start"]);const age=q!=null?-q:null;
      return `<tr><td><a class="nm" href="${esc(r.url)}" target="_blank">${esc(r["印刷会社"]||"—")}</a></td>
      <td>${esc(r["サイズ"]||"")}</td><td class="n">${r["ページ数"]!=null?r["ページ数"]:"—"}</td>
      <td>${esc(r["製本方式"]||"")}</td><td>${esc(r["本文用紙"]||"")}</td>
      <td class="n">${r["部数"]!=null?r["部数"].toLocaleString("ja-JP"):"—"}</td>
      <td class="n"><b>${r["1部単価"]!=null?"¥"+r["1部単価"].toLocaleString("ja-JP"):"—"}</b></td>
      <td class="n">${r["date:見積日:start"]?ymd(r["date:見積日:start"])+`<div class="sub">${age}日前</div>`:'<span class="sub">—</span>'}</td>
      <td class="sub" style="max-width:250px">${esc(flat(r["備考"]).slice(0,60))}</td></tr>`;}).join("")
    ||'<tr><td colspan="9" class="sub">該当なし</td></tr>'}</tbody></table></div>`);
}

function renderKPI(){
  const act=D.deals.filter(d=>ACTIVE[d.stage]);
  const pipe=act.reduce((s,d)=>s+d.amount,0);
  const hold=D.deals.filter(d=>d.stage==="保留");
  const ha=hold.reduce((s,d)=>s+d.amount,0);
  const won=D.deals.filter(d=>d.stage==="受注").reduce((s,d)=>s+d.amount,0);
  const need=D.t.overdue.length+D.t.soon.length;
  const cards=[
    {l:"アクティブ案件",v:act.length,u:"件",n:"作成中・送付済・商談中"},
    {l:"進行中の総額",v:man(pipe),u:"万円",n:`受注済 ${man(won)}万円は含まない`},
    {l:"粗利見込み（参考）",v:man(pipe*0.67),u:"万円",n:"限界利益率67%の仮置き。実額ではない"},
    {l:"保留＝来期見込み",v:man(ha),u:"万円",n:`${hold.length}件。失注ではなく時期の問題`+(D.t.resuming.length?` ／ 再開時期 ${D.t.resuming.length}件`:"")},
    {l:"要対応",v:need,u:"件",n:`期日超過 ${D.t.overdue.length}件・3日以内 ${D.t.soon.length}件`,c:D.t.overdue.length?"crit":""}];
  $("kpis").innerHTML=cards.map(c=>`<div class="kpi ${c.c||""}"><div class="l">${c.l}</div>
    <div class="v">${c.v}<i>${c.u}</i></div><div class="n">${esc(c.n)}</div></div>`).join("");
}

function render(){
  if(!D)return;
  renderKPI();
  $("c-today").textContent=(D.t.overdue.length+D.t.soon.length)||"";
  $("c-pipe").textContent=D.deals.filter(d=>ACTIVE[d.stage]).length||"";
  $("c-client").textContent=D.clients.length||"";
  $("c-ext").textContent=D.exts.filter(e=>e["ステータス"]!=="見送り").length||"";
  $("c-price").textContent=D.prices.length||"";
  if(tab==="today")$("p-today").innerHTML=renderToday();
  if(tab==="pipe")$("p-pipe").innerHTML=renderPipe();
  if(tab==="client")$("p-client").innerHTML=renderClients();
  if(tab==="ext")$("p-ext").innerHTML=renderExts();
  if(tab==="price")$("p-price").innerHTML=renderPrices();
}

async function load(force){
  $("dot").className="dot";$("fresh").textContent="読み込み中…";
  try{
    const r=await fetch("/api/notion"+(force?"?force=1":""));
    const d=await r.json();
    if(d.error){$("dot").className="dot err";$("fresh").textContent=d.error;return;}
    D={props:d.props||[],clients:d.clients||[],exts:d.exts||[],prices:d.prices||[]};
    D.deals=buildDeals(D.props);
    D.t=triage(D.deals,D.exts,D.clients);
    const age=Math.round((Date.now()/1000-d.at)/60);
    $("dot").className="dot ok";
    $("fresh").textContent=(age<1?"たった今":age+"分前")+"取得";
    if(d.errors)$("fresh").textContent+=" ／ 一部エラー";
    render();
  }catch(e){$("dot").className="dot err";$("fresh").textContent="取得失敗";}
}

const TABS=["today","pipe","client","ext","price","make","mm"];
function go(t){
  tab=t;
  document.body.dataset.tab=t;      /* モバイルでKPIの出し分けに使う */
  document.querySelectorAll("#nav button").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.t===t)));
  TABS.forEach(x=>{const p=$("p-"+x);if(p)p.hidden=(x!==t);});
  render();
  /* 切り替えたら先頭へ。動かないと「変わっていない」ように見える */
  const soft=matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth";
  window.scrollTo({top:0,behavior:soft});
}
$("nav").addEventListener("click",e=>{const b=e.target.closest("button[data-t]");if(b)go(b.dataset.t);});
$("reload").addEventListener("click",()=>load(true));
document.addEventListener("click",e=>{
  const p2=e.target.closest("[data-pcf]");
  if(p2){pcf=p2.getAttribute("data-pcf");render();return;}
  const cf2=e.target.closest("[data-cf]");
  if(cf2){cf=cf2.getAttribute("data-cf");render();return;}
  const pf2=e.target.closest("[data-pf]");
  if(pf2){pf=pf2.getAttribute("data-pf");render();return;}
  const u=e.target.closest("[data-company]");
  if(u){
    $("company").value=u.getAttribute("data-company");
    go("make");$("context").focus();updateWhich();return;
  }
});

/* ---- 提案書生成 ---- */
const logEl=()=>$("log"),filesEl=()=>$("files");
function add(kind,text){const d=document.createElement("div");d.className="r "+kind;
  if(kind==="tool"){const i=text.indexOf("  ");d.innerHTML="<b>"+esc(i>0?text.slice(0,i):text)+"</b> "+esc(i>0?text.slice(i):"");}
  else d.textContent=text;
  logEl().appendChild(d);logEl().scrollTop=logEl().scrollHeight;}
let whichTimer=null;
async function updateWhich(){
  const c=$("company").value.trim();
  const el=$("which");
  if(!c){el.textContent="";return;}
  try{
    const r=await fetch("/api/which?c="+encodeURIComponent(c));
    const j=await r.json();
    el.innerHTML = j.cmd==="teian"
      ? '<span class="pill wine">既存顧客</span> /teian で追加提案を組みます（Notionの提案・拡張案件・議事録を読みます）'
      : j.cmd==="shodan"
      ? '<span class="pill navy">新規企業</span> /shodan で初回提案を組みます（公開情報を調査します）' : "";
  }catch(e){el.textContent="";}
}
$("company").addEventListener("input",()=>{clearTimeout(whichTimer);whichTimer=setTimeout(updateWhich,400);});

$("go").addEventListener("click",async()=>{
  const company=$("company").value.trim();
  if(!company){$("company").focus();return;}
  $("go").disabled=true;$("go").textContent="実行中…";
  logEl().innerHTML="";filesEl().innerHTML="";
  const res=await fetch("/run",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({company,context:$("context").value,skip_notion:$("skip").checked})});
  const j=await res.json();
  if(j.error){add("error",j.error);done();return;}
  const es=new EventSource("/stream/"+j.id);
  es.onmessage=ev=>{const d=JSON.parse(ev.data);
    if(d.kind==="end"){add("meta","— "+d.text+" —");es.close();done();load(true);return;}
    if(d.kind==="file"){const a=document.createElement("a");
      a.href="/file/"+encodeURIComponent(d.text);a.textContent="⬇ "+d.text;filesEl().appendChild(a);
      const r=document.createElement("a");r.href="#";r.textContent="📂 Finderで表示";
      r.onclick=x=>{x.preventDefault();fetch("/reveal?f="+encodeURIComponent(d.text));};filesEl().appendChild(r);return;}
    add(d.kind,d.text);};
  es.onerror=()=>{es.close();done();};
});
function done(){$("go").disabled=false;$("go").textContent="調査して提案書を作る";}

/* ---- 議事録の取り込み ---- */
function addTo(el,kind,text){const d=document.createElement("div");d.className="r "+kind;
  if(kind==="tool"){const i=text.indexOf("  ");d.innerHTML="<b>"+esc(i>0?text.slice(0,i):text)+"</b> "+esc(i>0?text.slice(i):"");}
  else d.textContent=text;
  el.appendChild(d);el.scrollTop=el.scrollHeight;}
$("mmGo").addEventListener("click",async()=>{
  const el=$("mmLog");
  $("mmGo").disabled=true;$("mmGo").textContent="取り込み中…";el.innerHTML="";
  const res=await fetch("/run",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({mode:"mm",context:$("mmPeriod").value})});
  const j=await res.json();
  if(j.error){addTo(el,"error",j.error);mmDone();return;}
  const es=new EventSource("/stream/"+j.id);
  es.onmessage=ev=>{const d=JSON.parse(ev.data);
    if(d.kind==="end"){addTo(el,"meta","— "+d.text+" —");es.close();mmDone();load(true);return;}
    if(d.kind==="file")return;
    addTo(el,d.kind,d.text);};
  es.onerror=()=>{es.close();mmDone();};
});
function mmDone(){$("mmGo").disabled=false;$("mmGo").textContent="Circlebackから取り込む";}

const wd=["日","月","火","水","木","金","土"];
$("today").textContent=`${TODAY.getFullYear()}/${TODAY.getMonth()+1}/${TODAY.getDate()}（${wd[TODAY.getDay()]}）`;
document.body.dataset.tab="today";
load(false);
setInterval(()=>{const n=midnight();if(n.getTime()!==TODAY.getTime()){TODAY=n;render();}},60000);
