const REC_DATA=[
 {sku:'SKU-9074',description:'Premium Serum',warehouse:'Central DC',erp:12,wms:0,oms:5,status:'Sellable',type:'Status mismatch',age:9,priority:'High',unitCost:85,root:'WMS status not synchronised',action:'Correct inventory status',resolved:false},
 {sku:'SKU-4218',description:'Surface Cleaner 1L',warehouse:'Central DC',erp:118,wms:96,oms:12,status:'In transit',type:'Delayed movement',age:5,priority:'High',unitCost:18,root:'Transfer receipt not posted',action:'Complete pending movement',resolved:false},
 {sku:'SKU-3320',description:'Daily Shampoo',warehouse:'North DC',erp:55,wms:55,oms:8,status:'Sellable',type:'Allocation pending',age:3,priority:'Medium',unitCost:24,root:'Order cancellation not released',action:'Release stale allocation',resolved:false},
 {sku:'SKU-7811',description:'Storage Box 20L',warehouse:'North DC',erp:240,wms:238,oms:0,status:'Sellable',type:'Count variance',age:2,priority:'Low',unitCost:12,root:'Count tolerance difference',action:'Investigate physical count',resolved:true},
 {sku:'SKU-5510',description:'Body Wash 1L',warehouse:'Central DC',erp:84,wms:61,oms:4,status:'Blocked',type:'Integration defect',age:12,priority:'High',unitCost:31,root:'Repeated interface rejection',action:'Escalate integration defect',resolved:false},
 {sku:'SKU-2481',description:'Laundry Detergent',warehouse:'North DC',erp:76,wms:70,oms:2,status:'In transit',type:'Delayed movement',age:7,priority:'Medium',unitCost:22,root:'Movement confirmation delayed',action:'Resend transaction',resolved:false},
 {sku:'SKU-6612',description:'Hand Cream',warehouse:'Central DC',erp:42,wms:42,oms:11,status:'Sellable',type:'Allocation pending',age:8,priority:'Medium',unitCost:16,root:'Stale marketplace allocation',action:'Release stale allocation',resolved:false},
 {sku:'SKU-1198',description:'Facial Cleanser',warehouse:'North DC',erp:65,wms:63,oms:0,status:'Sellable',type:'Count variance',age:1,priority:'Low',unitCost:27,root:'Small physical variance',action:'Investigate physical count',resolved:true}
];
let recRows=[],recSort={key:'sku',direction:1};
function recDerived(row){const available=Math.max(0,row.wms-row.oms),variance=row.erp-row.wms,value=Math.abs(variance)*row.unitCost;return{...row,available,variance,value}}
function recFilter(){
 const warehouse=document.getElementById('recWarehouse').value,status=document.getElementById('recStatus').value,type=document.getElementById('recType').value,priority=document.getElementById('recPriority').value,age=document.getElementById('recAge').value;
 recRows=REC_DATA.map(recDerived).filter(row=>(warehouse==='all'||row.warehouse===warehouse)&&(status==='all'||row.status===status)&&(type==='all'||row.type===type)&&(priority==='all'||row.priority===priority)&&(age==='all'||(age==='0-2'&&row.age<=2)||(age==='3-7'&&row.age>=3&&row.age<=7)||(age==='8+'&&row.age>=8)));
 recRender();
}
function recRender(){
 const erp=recRows.reduce((s,r)=>s+r.erp,0),wms=recRows.reduce((s,r)=>s+r.wms,0),oms=recRows.reduce((s,r)=>s+r.oms,0),net=recRows.reduce((s,r)=>s+r.variance,0),gross=recRows.reduce((s,r)=>s+Math.abs(r.variance),0),exposure=recRows.reduce((s,r)=>s+r.value,0);
 updateKpi('erpKpi',formatNumber(erp));updateKpi('wmsKpi',formatNumber(wms));updateKpi('omsKpi',formatNumber(oms));updateKpi('netKpi',formatNumber(net));updateKpi('grossKpi',formatNumber(gross));updateKpi('exposureKpi',formatCurrency(exposure));updateKpi('openKpi',recRows.filter(r=>!r.resolved).length);updateKpi('highKpi',recRows.filter(r=>r.priority==='High').length);updateKpi('slaKpi',recRows.filter(r=>r.age>7&&!r.resolved).length);updateKpi('resolutionKpi',`${recRows.length?Math.round(recRows.filter(r=>r.resolved).length/recRows.length*100):0}%`);
 recCharts(erp,wms,oms);recTable();recInsights(exposure,gross);
 document.getElementById('recImpact').innerHTML=[['Gross variance',`${gross} units`],['Exposure prioritised',formatCurrency(exposure)],['Older than SLA',recRows.filter(r=>r.age>7&&!r.resolved).length],['Potential auto-resolution',recRows.filter(r=>['Delayed movement','Allocation pending'].includes(r.type)).length]].map(([l,v])=>`<article><span>${l}</span><strong>${v}</strong></article>`).join('');
}
function recCharts(erp,wms,oms){
 const types=['Delayed movement','Status mismatch','Allocation pending','Count variance','Integration defect'];
 svgBarChart(document.getElementById('exceptionChart'),['Movement','Status','Allocation','Count','Integration'],types.map(t=>recRows.filter(r=>r.type===t).length));
 svgBarChart(document.getElementById('exposureChart'),['Movement','Status','Allocation','Count','Integration'],types.map(t=>recRows.filter(r=>r.type===t).reduce((s,r)=>s+r.value,0)));
 svgBarChart(document.getElementById('ageChart'),['0–2','3–7','8+'],[recRows.filter(r=>r.age<=2).length,recRows.filter(r=>r.age>=3&&r.age<=7).length,recRows.filter(r=>r.age>=8).length]);
 svgLineChart(document.getElementById('trendChart'),[{values:[14,16,13,12,10,9,recRows.filter(r=>!r.resolved).length]},{values:[3,4,5,6,7,8,recRows.filter(r=>r.resolved).length]}],['D1','D2','D3','D4','D5','D6','Today']);
 svgBarChart(document.getElementById('balanceChart'),['ERP','WMS','OMS allocated'],[erp,wms,oms]);
 svgBarChart(document.getElementById('repeatChart'),recRows.slice(0,5).map(r=>r.sku.replace('SKU-','')),recRows.slice(0,5).map(r=>Math.max(1,Math.round(r.age/2))));
}
function recInsights(exposure,gross){
 const top=[...recRows].sort((a,b)=>b.value-a.value)[0],movement=recRows.filter(r=>r.type==='Delayed movement').length,alloc=recRows.filter(r=>r.type==='Allocation pending').length;
 const insights=[{title:'Movement timing requires process correction',copy:`${movement} selected exception(s) relate to delayed postings; validate event timing before adjustment.`,badge:'<span class="badge warn">Process</span>'},{title:'Allocations explain apparent availability gaps',copy:`${alloc} selected record(s) contain pending allocations that reduce available stock without changing physical balance.`,badge:'<span class="badge neutral">Allocation</span>'},{title:'Financial exposure changes priority',copy:top?`${top.sku} contributes ${formatCurrency(top.value)} exposure and should be investigated before smaller quantity differences.`:'No records match the selected scope.',badge:'<span class="badge bad">Value risk</span>'},{title:'Net variance can hide operational workload',copy:`Net and gross variance differ because positive and negative exceptions offset. Gross selected variance is ${gross} units (${formatCurrency(exposure)} exposure).`,badge:'<span class="badge good">Control</span>'}];
 renderInsightCards(document.getElementById('recInsights'),insights);
}
function recTable(){
 const action=document.getElementById('recAction').value;let rows=filterObjects(recRows,'action',action);rows=sortObjects(rows,recSort.key,recSort.direction);
 document.getElementById('exceptionRows').innerHTML=rows.map((r,i)=>`<tr><td>${r.sku}</td><td>${r.description}</td><td>${r.warehouse}</td><td>${r.erp}</td><td>${r.wms}</td><td>${r.oms}</td><td>${r.available}</td><td>${r.variance}</td><td>${formatCurrency(r.value)}</td><td>${r.status}</td><td>${r.type}</td><td>${r.age}d</td><td><span class="badge ${r.priority==='High'?'bad':r.priority==='Medium'?'warn':'good'}">${r.priority}</span></td><td>${r.root}</td><td>${r.action}</td><td><button class="detail-button" aria-expanded="false" aria-controls="trail-${i}" data-detail="${i}">Details</button></td></tr><tr class="detail-row" id="trail-${i}" hidden><td colspan="16"><div class="investigation-trail"><div><strong>Detected issue</strong><span>${r.type}</span></div><div><strong>Evidence</strong><span>ERP ${r.erp}, WMS ${r.wms}, allocated ${r.oms}</span></div><div><strong>Likely cause</strong><span>${r.root}</span></div><div><strong>Validation</strong><span>Confirm cut-off, event and count evidence</span></div><div><strong>Resolution</strong><span>${r.action}</span></div></div></td></tr>`).join('');
 document.querySelectorAll('[data-detail]').forEach(button=>button.addEventListener('click',()=>{const row=document.getElementById(`trail-${button.dataset.detail}`),open=!row.hidden;row.hidden=open;button.setAttribute('aria-expanded',String(!open));button.textContent=open?'Details':'Hide'}));
 document.getElementById('recTableStatus').textContent=`${rows.length} of ${recRows.length} exceptions shown`;
}
['recWarehouse','recStatus','recType','recPriority','recAge','recView','recDate'].forEach(id=>document.getElementById(id).addEventListener('change',recFilter));
document.getElementById('recAction').addEventListener('change',recTable);
bindTableSort(document.querySelector('#exceptions'),key=>{recSort.direction=recSort.key===key?-recSort.direction:1;recSort.key=key;recTable()});
recFilter();
