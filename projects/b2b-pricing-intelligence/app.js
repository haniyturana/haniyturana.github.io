'use strict';
const $=id=>document.getElementById(id), money=new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP',maximumFractionDigits:2}), num=new Intl.NumberFormat('en-GB',{maximumFractionDigits:2});
const fmt=v=>v==null?'—':num.format(v), gbp=v=>v==null?'—':money.format(v), pct=v=>v==null?'—':`${fmt(v*100)}%`, esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let data={},page=0;
function table(id,rows,cols){$(id).innerHTML=rows.length?`<div class="table-wrap" tabindex="0" aria-label="Scrollable data table"><table><thead><tr>${cols.map(c=>`<th>${esc(c[0])}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr class="${r.selected?'suggested-row':''}">${cols.map(c=>`<td>${esc((c[2]||((x)=>x))(r[c[1]]))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:'<p class="note">No qualifying results for this selection.</p>';}
function chart(id,traces,x='',y='',layout={}){if(!window.Plotly){$(id).textContent='Chart library unavailable. Tables remain available.';return;}Plotly.react(id,traces,{margin:{t:30,r:25,b:65,l:75},paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{family:'Segoe UI, sans-serif',color:'#53657a'},showlegend:false,...layout,xaxis:{title:x,automargin:true,...layout.xaxis},yaxis:{title:y,automargin:true,gridcolor:'#edf1f5',...layout.yaxis}},{responsive:true,displayModeBar:false});}
const reviewStatuses=['Pricing Review','Possible Volume Justification','Maintain / No Material Gap','Insufficient Evidence'];
const cols=[['Customer','CustomerID'],['SKU','StockCode'],['Description','Description'],['Orders','orders',fmt],['Quantity','quantity',fmt],['Effective Price','price',gbp],['SKU Median Price','benchmark',gbp],['Price Gap %','gap',pct],['Volume Position','volume_position'],['Pricing Review Status','review_status']];
function reviewTable(rows){
  $('opportunities').innerHTML=rows.length?`<table class="review-table"><thead><tr>${cols.map(c=>`<th scope="col">${esc(c[0])}</th>`).join('')}</tr></thead>${rows.map(r=>`<tbody><tr class="review-row">${cols.map(c=>`<td data-label="${esc(c[0])}">${esc((c[2]||((x)=>x))(r[c[1]]))}</td>`).join('')}</tr><tr class="review-detail"><td colspan="10"><details><summary>Details for ${esc(r.CustomerID)} / ${esc(r.StockCode)}</summary><dl>${[['Customer Segment',r.segment],['Latest Price',gbp(r.latest_price)],['Reason',r.reason],['Revenue',gbp(r.revenue)],['SKU median customer quantity',fmt(r.sku_median_quantity)]].map(([label,value])=>`<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl></details></td></tr></tbody>`).join('')}</table>`:'<p class="note">No qualifying results for this selection.</p>';
}
function matrix(){
  const q=$('search').value.toLowerCase();
  const rows=data.pricing_opportunities.filter(r=>(!$('segment').value||r.segment===$('segment').value)&&(!$('recommendation').value||r.review_status===$('recommendation').value)&&(!$('scope').value||r.StockCode===$('sku').value)&&[r.CustomerID,r.StockCode,r.Description].join(' ').toLowerCase().includes(q));
  const counts=Object.fromEntries(reviewStatuses.map(status=>[status,0]));
  rows.forEach(r=>counts[r.review_status]++);
  $('review-summary').innerHTML=reviewStatuses.map((status,i)=>`<div class="review-count ${i===0?'primary-count':''}"><span>${esc(status)}</span><strong>${fmt(counts[status])}</strong></div>`).join('');
  rows.sort((a,b)=>($('sort').value==='priority'?reviewStatuses.indexOf(a.review_status)-reviewStatuses.indexOf(b.review_status):0)||($('sort').value==='asc'?a.gap-b.gap:b.gap-a.gap)||a.CustomerID.localeCompare(b.CustomerID)||a.StockCode.localeCompare(b.StockCode));
  page=Math.min(page,Math.max(0,Math.ceil(rows.length/25)-1));
  reviewTable(rows.slice(page*25,page*25+25));
  $('page').textContent=`${rows.length?page+1:0} / ${Math.ceil(rows.length/25)} | ${fmt(rows.length)} results`;
  $('prev').disabled=page===0;$('next').disabled=(page+1)*25>=rows.length;
}
function products(){
  const sku=$('sku').value,s=data.sku_pricing.find(r=>r.StockCode===sku);
  const allRows=data.pricing_opportunities.filter(r=>r.StockCode===sku);
  const rows=allRows.filter(r=>!$('segment').value||r.segment===$('segment').value);
  const percent=v=>`${(v*100).toFixed(1)}%`, threshold=data.metadata.gap_threshold;
  const median=s?.benchmark, medianQuantity=allRows[0]?.sku_median_quantity;
  const below=rows.filter(r=>r.gap>=threshold);
  table('skuStats',s?[s]:[],[['SKU','StockCode'],['Canonical Description','Description'],['Customers','customers',fmt],['Minimum','minimum',gbp],['Median Customer Price','benchmark',gbp],['Maximum','maximum',gbp],['Spread','spread',percent],['Revenue','revenue',gbp]]);
  const reference=(vertical,value,dash,color)=>({type:'line',xref:vertical?'x':'paper',yref:vertical?'paper':'y',x0:vertical?value:0,x1:vertical?value:1,y0:vertical?0:value,y1:vertical?1:value,line:{color,width:2,dash}});
  const bands=priceBands(rows);
  chart('priceChart',[{type:'bar',x:bands.map(b=>b.label),y:bands.map(b=>b.count),customdata:bands.map(b=>b.percent),marker:{color:['#63778e','#168b80','#75b9ac','#c17b35']},hovertemplate:'%{x}<br>Customers: %{y:,.0f}<br>Share: %{customdata:.1f}%<extra></extra>'}],'Price position','Number of customers',{
    xaxis:{tickvals:bands.map(b=>b.label),ticktext:['At / above<br>median','0–5% below<br>median','5–15% below<br>median','15%+ below<br>median'],tickfont:{size:11}},yaxis:{tickformat:',d',rangemode:'tozero'},bargap:.25
  });
  $('priceMedianKey').textContent=`Median customer price: ${gbp(median)}`;
  $('priceThresholdKey').textContent=`${(threshold*100).toFixed(0)}% below median: ${gbp(median==null?null:median*(1-threshold))}`;
  $('priceInterpretation').textContent=rows.length
    ?`The SKU median customer price is ${gbp(median)}. ${fmt(below.length)} customers (${percent(below.length/rows.length)}) pay at least ${(threshold*100).toFixed(0)}% below the median customer price.`
    :'No customers match this SKU and segment selection.';
  chart('volumeChart',[{type:'scatter',mode:'markers',x:rows.map(r=>r.quantity),y:rows.map(r=>r.price),customdata:rows.map(r=>[r.CustomerID,r.orders,r.gap*100,r.review_status]),marker:{size:8,color:rows.map(r=>r.gap>=threshold?'#c17b35':'#168b80'),symbol:rows.map(r=>r.gap>=threshold?'diamond':'circle'),opacity:.7},hovertemplate:'Customer: %{customdata[0]}<br>Quantity: %{x:,.0f}<br>Orders: %{customdata[1]:,.0f}<br>Effective price: £%{y:,.2f}<br>Price gap vs median: %{customdata[2]:.1f}%<br>Pricing review status: %{customdata[3]}<extra></extra>'}],'Customer quantity (log scale)','Weighted effective price (GBP)',{
    xaxis:{type:'log',tickformat:',~g',nticks:5},yaxis:{tickprefix:'£',tickformat:',.2f',nticks:5},
    shapes:s&&medianQuantity!=null?[reference(false,median,'solid','#63778e'),reference(true,medianQuantity,'dash','#c17b35')]:[]
  });
  $('volumeMedianKey').textContent=`Median customer price: ${gbp(median)}`;
  $('volumeQuantityKey').textContent=`Median customer quantity: ${fmt(medianQuantity)}`;
  const higher=below.filter(r=>r.quantity>medianQuantity).length;
  $('volumeInterpretation').textContent=!rows.length?'No customers match this SKU and segment selection.'
    :!below.length?`No displayed customers pay at least ${(threshold*100).toFixed(0)}% below the median customer price.`
    :higher>below.length/2?`${fmt(higher)} of ${fmt(below.length)} customers paying at least ${(threshold*100).toFixed(0)}% below the median also purchased above the median customer quantity.`
    :`${fmt(below.length-higher)} of ${fmt(below.length)} customers paying at least ${(threshold*100).toFixed(0)}% below the median purchased at or below the median customer quantity.`;
  matrix();
  models();
}
function priceBands(rows){
  const bands=['At / above median','0–5% below median','5–15% below median','15%+ below median'].map(label=>({label,count:0,percent:0}));
  rows.forEach(r=>bands[r.gap<=0?0:r.gap<.05?1:r.gap<.15?2:3].count++);
  bands.forEach(b=>b.percent=rows.length?100*b.count/rows.length:0);
  return bands;
}
function segments(){
  const selected=$('segment').value;
  const rows=['Small','Medium','Large','Strategic'].map(segment=>{const c=data.customer_summary.filter(r=>r.segment===segment),sum=k=>c.reduce((a,r)=>a+r[k],0),orders=sum('orders');return {segment,customers:c.length,revenue:sum('revenue'),aov:orders?sum('revenue')/orders:null,units:orders?sum('quantity')/orders:null};});
  chart('segmentChart',[{type:'bar',x:rows.map(r=>r.segment),y:rows.map(r=>r.revenue),customdata:rows.map(r=>[r.customers,r.aov,r.units]),marker:{color:rows.map(r=>!selected||selected===r.segment?'#168b80':'#cdd8e1'),line:{color:rows.map(r=>selected===r.segment?'#203e59':'transparent'),width:3}},hovertemplate:'Segment: %{x}<br>Customers: %{customdata[0]:,.0f}<br>Revenue: £%{y:,.2f}<br>Average order value: £%{customdata[1]:,.2f}<br>Units per order: %{customdata[2]:,.2f}<extra></extra>'}],'','Revenue (GBP)');
  const plot=$('segmentChart');
  if(plot.on){plot.removeAllListeners('plotly_click');plot.on('plotly_click',event=>{const segment=event.points[0].x;$('segment').value=$('segment').value===segment?'':segment;page=0;segments();});}
  $('segment-selection').textContent=selected?`${selected} selected. Click it again to show all segments.`:'All segments. Click a bar to filter customers.';
  table('segmentTable',rows.filter(r=>!selected||r.segment===selected),[['Segment','segment'],['Customers','customers',fmt],['Revenue','revenue',gbp],['Average order value','aov',gbp],['Units per order','units',fmt]]);
  products();
}
const testedChanges=[-.05,0,.03,.05,.10];
function selectPriceSuggestion(model,scenarios){
  if(!model?.eligible)return null;
  const rows=testedChanges.map(change=>scenarios.find(r=>Math.abs(r.change-change)<1e-10));
  if(rows.some(r=>!r||![r.price,r.quantity,r.revenue].every(Number.isFinite)||r.price<=0||r.quantity<0||r.revenue<0))return null;
  // Revenue ties prefer no change, then the smallest absolute price change, then the lower change.
  const ranked=[...rows].sort((a,b)=>b.revenue-a.revenue||Math.abs(a.change)-Math.abs(b.change)||a.change-b.change);
  return {rows,baseline:rows[1],suggested:ranked[0]};
}
let priceSuggestion=null;
function models(){
  const sku=$('sku').value,m=data.elasticity.find(r=>r.StockCode===sku),product=data.sku_pricing.find(r=>r.StockCode===sku);
  priceSuggestion=selectPriceSuggestion(m,data.scenario.filter(r=>r.StockCode===sku));
  $('opportunity-product').textContent=`${sku} · ${product?.Description||''}`;
  table('modelStats',m?[m]:[],[['SKU','StockCode'],['Coefficient','beta',fmt],['p-value','pvalue',v=>v==null?'—':v.toPrecision(3)],['R²','r2',fmt],['Months','n',fmt],['Interpretation','interpretation']]);
  chart('elasticityChart',m?[{type:'scatter',mode:'markers',x:m.points.map(r=>r.price),y:m.points.map(r=>r.quantity),text:m.points.map(r=>r.month),marker:{color:'#168b80'}}]:[],'Monthly effective price (GBP)','Monthly quantity');
  $('test-suggested').disabled=!priceSuggestion;
  if(!priceSuggestion){
    $('suggestion-state').textContent='Insufficient historical evidence for price suggestion';
    $('suggestion-kpis').innerHTML='';$('suggestion-why').textContent='Historical evidence is insufficient to produce a reliable price scenario.';
    $('scenarioTable').innerHTML='<p>No price suggestion is available for this SKU.</p>';
    chart('scenarioChart',[],'Price scenario','Model-implied revenue (GBP)',{xaxis:{type:'category'}});return;
  }
  const {baseline,suggested,rows}=priceSuggestion;
  $('suggestion-state').textContent=suggested.change===0?'Maintain Current Price':suggested.change>0?'Price Increase Scenario for Review':'Price Decrease Scenario for Review';
  const cards=[['Current / historical reference price',gbp(baseline.price)],['Suggested Price for Review',gbp(suggested.price)],['Suggested price change',pct(suggested.change)],['Model-implied demand',fmt(suggested.quantity)],['Model-implied revenue',gbp(suggested.revenue)],['Revenue change vs historical baseline',gbp(suggested.revenue-baseline.revenue)]];
  $('suggestion-kpis').innerHTML=cards.map(([label,value])=>`<div class="card"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join('');
  $('suggestion-why').textContent=suggested.change===0?'The current price produces the strongest model-implied revenue among the tested scenarios, so no price change is suggested.':`Among the tested price scenarios, ${suggested.change>0?'+':''}${pct(suggested.change)} produces the highest model-implied revenue while accounting for the observed historical demand response.`;
  table('scenarioTable',rows.map(r=>({...r,selected:r===suggested,choice:r===suggested?'Suggested Price for Review':r.change===0?'Historical baseline':'Tested scenario',difference:r.revenue-baseline.revenue})),[['Price change','change',pct],['Price','price',gbp],['Model-implied demand','quantity',fmt],['Model-implied revenue','revenue',gbp],['Revenue change','difference',gbp],['Review','choice']]);
  chart('scenarioChart',[{type:'bar',x:rows.map(r=>pct(r.change)),y:rows.map(r=>r.revenue),customdata:rows.map(r=>[r.price,r.quantity,r.revenue-baseline.revenue,r===suggested?'Suggested Price for Review':'Tested scenario']),marker:{color:rows.map(r=>r===suggested?'#168b80':'#a5b6c6')},hovertemplate:'%{customdata[3]}<br>Price: £%{customdata[0]:,.2f}<br>Model-implied demand: %{customdata[1]:,.2f}<br>Model-implied revenue: £%{y:,.2f}<br>Revenue change: £%{customdata[2]:,.2f}<extra></extra>'}],'Price scenario','Model-implied revenue (GBP)',{xaxis:{type:'category'}});
}
async function init(){try{const names=['metadata','customer_summary','sku_pricing','pricing_opportunities','elasticity','scenario'];await Promise.all(names.map(async n=>{let r;if('DecompressionStream' in window){r=await fetch(`data/${n}.json.gz`);if(r.ok){data[n]=unpack(await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json());return;}}r=await fetch(`data/${n}.json`);if(!r.ok)throw Error(`${n}: HTTP ${r.status}`);data[n]=unpack(await r.json());}));const m=data.metadata;if(m.status!=='ready'){$('status').textContent='Awaiting analysis export. Run the notebook export cell with your cleaned df. No portfolio results have been invented.';return;}$('status').textContent=`${m.date_start} – ${m.date_end} · ${fmt(m.rows)} cleaned transaction lines · ${fmt(m.missing_customer_rows)} rows without customer identity`;const k=[['Total Identified Revenue',gbp(m.identified_revenue),'Identified customer accounts only'],['Customers',fmt(m.customers),'Descriptive purchasing-account proxy'],['SKUs',fmt(m.skus),'Identified-customer scope'],['Customer-SKU Relationships Reviewed',fmt(m.relationships_reviewed),'Includes insufficient-evidence cases'],['Pricing Review Cases',fmt(m.pricing_review_cases),'Below benchmark without obvious volume justification']];$('screening-note').textContent=`The ${pct(m.gap_threshold)} price-gap threshold is a configurable screening choice, not an economically proven optimal threshold. Volume position compares total customer-SKU quantity with the SKU customer median. Review commercial terms before changing price.`;$('kpis').innerHTML=k.map(r=>`<div class="card">${esc(r[0])}<strong>${esc(r[1])}</strong><span>${esc(r[2])}</span></div>`).join('');$('sku').innerHTML=data.sku_pricing.filter(r=>r.eligible).sort((a,b)=>b.revenue-a.revenue).map(r=>`<option value="${esc(r.StockCode)}">${esc(r.StockCode)} · ${esc(r.Description)}</option>`).join('');segments();}catch(e){$('status').textContent=`Analysis could not be loaded: ${e.message}. Serve this folder over HTTP (GitHub Pages or a local static preview).`;}}
['search','recommendation','scope','sort'].forEach(id=>$(id).addEventListener('input',()=>{if(!data.metadata||data.metadata.status!=='ready')return;page=0;matrix();}));$('segment').onchange=()=>{if(data.metadata?.status==='ready'){page=0;segments();}};$('sku').onchange=()=>{if(data.metadata?.status==='ready'){page=0;products();}};$('prev').onclick=()=>{if(page>0){page--;matrix();}};$('next').onclick=()=>{if(data.metadata?.status==='ready'){page++;matrix();}};init();

function unpack(v){if(!v.columns)return v;return v.rows.map(row=>Object.fromEntries(v.columns.map((col,i)=>[col,v.dictionaries[i]&&row[i]!=null?v.dictionaries[i][row[i]]:row[i]])));}

// Resize after container changes, including opening the technical details panel.
const chartObserver=new ResizeObserver(entries=>entries.forEach(({target})=>{
  if(window.Plotly&&target.data&&target.clientWidth&&target.clientHeight)Plotly.Plots.resize(target);
}));
document.querySelectorAll('.chart').forEach(element=>chartObserver.observe(element));
document.querySelectorAll('details').forEach(element=>element.addEventListener('toggle',()=>{
  if(element.open)element.querySelectorAll('.chart').forEach(plot=>{if(window.Plotly&&plot.data)Plotly.Plots.resize(plot);});
}));
