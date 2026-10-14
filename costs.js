const COSTS_KEY='mu-equipment-costs-v1';
const COST_CATEGORIES=['儀器','針劑','水光','點滴'],expandedCosts=new Set();
let costsData={records:[],history:[]},costsLoadError=false,editingCost=null,showArchivedCosts=false;
const costsMoney=n=>n.toLocaleString('zh-TW',{maximumFractionDigits:2});
function costResult(r){const factor=r.basis==='unit'?r.quantity:1,cost=amount(r.cost*factor),price=amount(r.price*factor);return {cost,price,profit:amount(price-cost)};}
function validCosts(d){return d&&Array.isArray(d.records)&&Array.isArray(d.history)&&d.records.every(r=>typeof r.id==='string'&&typeof r.category==='string'&&r.category.trim()&&typeof r.name==='string'&&r.name.trim()&&Number.isSafeInteger(r.quantity)&&r.quantity>0&&['unit','total'].includes(r.basis)&&['cost','price'].every(k=>Number.isFinite(r[k])&&r[k]>=0)&&Object.values(costResult(r)).every(Number.isFinite)&&(r.archived===undefined||typeof r.archived==='boolean'))&&new Set(d.records.map(r=>r.id)).size===d.records.length;}
try{const raw=localStorage.getItem(COSTS_KEY);if(raw){const d=JSON.parse(raw);if(!validCosts(d))throw Error();costsData=d;}}catch{costsLoadError=true;}
const costsArea=document.createElement('section');costsArea.id='costsArea';costsArea.innerHTML=`
<div class="sectionTitle" style="justify-content:flex-start;flex-wrap:wrap"><h3>儀器、微整成本</h3><button id="newCost" class="primary">新增</button></div>
<p id="costsStatus" role="status"></p>
<form id="costsForm" class="financeForm" hidden>
<h4 id="costsFormTitle" class="wide">新增成本</h4>
<label>分類<select name="category" required><option>儀器</option><option>針劑</option><option>水光</option><option>點滴</option></select></label>
<label>名稱<input name="name" required maxlength="200"></label>
<label>數量<input name="quantity" type="number" min="1" step="1" value="1" required></label>
<label>金額方式<select name="basis"><option value="unit">成本、定價為單件金額</option><option value="total">成本、定價為整筆金額</option></select></label>
<label>成本（元）<input name="cost" type="number" min="0" step="0.01" required></label>
<label>定價（元）<input name="price" type="number" min="0" step="0.01" required></label>
<div class="wide totalCard"><span>淨利</span><strong id="costsPreview">0 元</strong><small id="costsFormula"></small></div>
<div class="wide"><button class="primary">儲存</button><button id="cancelCost" type="button">取消</button></div><p id="costsFeedback" class="wide formFeedback" role="alert"></p></form>

<div class="tools"><input id="costsSearch" placeholder="搜尋分類或名稱" aria-label="搜尋儀器、微整成本"><button id="costsArchiveToggle">查看封存紀錄</button></div>
<div id="costsRows"></div>
<p id="costsEmpty"></p><p><small>淨利依金額方式自動計算。</small></p>
<details><summary>留檔與備份</summary><p>資料與修改前版本儲存在此瀏覽器，請定期備份。</p><div class="tools"><button id="costsExport">匯出成本完整備份</button><button id="costsImport">匯入備份</button><input id="costsFile" type="file" accept=".json" hidden></div></details>`;
$('title').after(costsArea);
const renderBeforeCosts=render;render=function(){renderBeforeCosts();const active=sheets[current].name==='儀器、微整成本';costsArea.hidden=!active;if(active){document.querySelectorAll('.panel > .tools,.panel > .note,.panel > .scroll,.panel > p,#editor').forEach(e=>e.hidden=true);renderCosts();}};
function saveCosts(d,restore=false){if(costsLoadError&&!restore){$('costsStatus').textContent='既有資料無法讀取，請匯入備份，避免覆蓋。';return false;}try{localStorage.setItem(COSTS_KEY,JSON.stringify(d));costsData=d;costsLoadError=false;$('costsStatus').textContent='已儲存在此瀏覽器，修改已留檔。';return true;}catch{$('costsStatus').textContent='儲存失敗，請先匯出備份。';return false;}}
function commitCost(r,actionName){const previous=costsData.records.find(x=>x.id===r.id)||null,d={records:[...costsData.records.filter(x=>x.id!==r.id),r],history:[...costsData.history,{date:new Date().toISOString(),action:actionName,previous,record:structuredClone(r)}]};return validCosts(d)&&saveCosts(d);}
function resetCost(){editingCost=null;$('costsForm').reset();$('costsForm').hidden=true;}
function previewCost(){const f=$('costsForm').elements,r={basis:f.basis.value,quantity:Number(f.quantity.value),cost:Number(f.cost.value),price:Number(f.price.value)};$('costsPreview').textContent=costsMoney(costResult(r).profit)+' 元';$('costsFormula').textContent=r.basis==='unit'?'淨利＝（定價 − 成本）× 數量':'淨利＝定價 − 成本';}
function openCost(r){editingCost=r?.id||null;const form=$('costsForm');form.reset();if(r){if(![...form.elements.category.options].some(o=>o.value===r.category)){const option=document.createElement('option');option.value=r.category;option.textContent=r.category;form.elements.category.append(option);}fill(form,r);}$('costsFormTitle').textContent=r?'編輯成本':'新增成本';$('costsFeedback').textContent='';form.hidden=false;previewCost();form.scrollIntoView({block:'start'});form.elements.category.focus({preventScroll:true});}
function renderCosts(){
 if(costsLoadError)$('costsStatus').textContent='無法讀取既有成本資料，原資料未覆蓋，請匯入備份。';
 $('costsArchiveToggle').textContent=showArchivedCosts?'返回目前紀錄':'查看封存紀錄';$('costsRows').replaceChildren();
 const q=$('costsSearch').value.trim(),rows=costsData.records.filter(r=>!!r.archived===showArchivedCosts&&(r.category+' '+r.name).includes(q));
 const categories=[...new Set([...COST_CATEGORIES,...costsData.records.map(r=>r.category)])];
 for(const category of categories){
  const records=rows.filter(r=>r.category===category);if(q&&!records.length)continue;
  const group=document.createElement('details');group.className='agentGroup';group.dataset.category=category;group.open=expandedCosts.has(category)||!!q;
  group.addEventListener('toggle',()=>{if(!group.isConnected)return;if(group.open)expandedCosts.add(category);else expandedCosts.delete(category);});
  const summary=document.createElement('summary'),title=document.createElement('strong'),count=document.createElement('span');title.textContent=category;count.textContent=records.length+' 筆';summary.append(title,count);group.append(summary);
  if(records.length){
   const scroll=document.createElement('div');scroll.className='scroll';const table=document.createElement('table');table.innerHTML='<thead><tr><th>分類</th><th>名稱</th><th>數量</th><th>成本</th><th>定價</th><th>淨利</th><th>操作</th></tr></thead>';const body=document.createElement('tbody');
   for(const r of records){const tr=document.createElement('tr'),result=costResult(r);for(const v of [r.category,r.name,r.quantity,costsMoney(r.cost)+' 元'+(r.basis==='unit'?'／件':'／整筆'),costsMoney(r.price)+' 元'+(r.basis==='unit'?'／件':'／整筆'),costsMoney(result.profit)+' 元'])td(tr,v);const ops=td(tr,'');if(showArchivedCosts)action(ops,'還原',()=>{if(commitCost({...r,archived:false},'還原'))renderCosts();});else{action(ops,'編輯',()=>openCost(r));action(ops,'封存',()=>{if(confirm('封存此成本紀錄？原資料保留，可還原。')&&commitCost({...r,archived:true},'封存')){resetCost();renderCosts();}});}body.append(tr);}
   table.append(body);scroll.append(table);group.append(scroll);
  }else{const empty=document.createElement('p');empty.textContent='此分類尚無紀錄。';group.append(empty);}
  $('costsRows').append(group);
 }
 $('costsEmpty').textContent=rows.length?'共 '+rows.length+' 筆紀錄。':'尚無符合條件的紀錄，可按標題旁「新增」填寫。';
}
$('newCost').onclick=()=>openCost();$('cancelCost').onclick=resetCost;$('costsForm').oninput=()=>{previewCost();$('costsFeedback').textContent='';};$('costsForm').noValidate=true;$('costsForm').onsubmit=e=>{e.preventDefault();const invalid=e.target.querySelector(':invalid');if(invalid){$('costsFeedback').textContent='請填寫分類、名稱、正整數數量及有效金額。';invalid.focus();return;}const d=Object.fromEntries(new FormData(e.target)),r={...d,id:editingCost||recordId(),category:d.category.trim(),name:d.name.trim(),quantity:Number(d.quantity),cost:Number(d.cost),price:Number(d.price),archived:false};if(!validCosts({records:[r],history:[]})){$('costsFeedback').textContent='請確認名稱、分類、數量及金額有效。';return;}if(commitCost(r,editingCost?'編輯':'新增')){expandedCosts.add(r.category);resetCost();renderCosts();}};
$('costsSearch').oninput=renderCosts;$('costsArchiveToggle').onclick=()=>{showArchivedCosts=!showArchivedCosts;resetCost();renderCosts();};$('costsExport').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(costsData,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='儀器微整成本完整備份.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};$('costsImport').onclick=()=>$('costsFile').click();$('costsFile').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{const d=JSON.parse(await f.text());if(!validCosts(d))throw Error();if(confirm('匯入將取代目前成本紀錄及留檔，是否繼續？')&&saveCosts(d,true)){resetCost();renderCosts();}}catch{$('costsStatus').textContent='匯入失敗：不是有效的成本備份。';}e.target.value='';};render();
