const FC_DATA={
 all:{label:'All categories',baseDemand:18420,mape:12.8,bias:1.8,drivers:[88,66,53,44],actual:[380,420,395,470,510,495,540,575,560,620,650,690]},
 home:{label:'Home care',baseDemand:10480,mape:11.6,bias:.9,drivers:[91,54,48,39],actual:[225,245,230,270,295,285,310,330,320,355,370,395]},
 personal:{label:'Personal care',baseDemand:7940,mape:13.9,bias:2.6,drivers:[84,72,61,49],actual:[155,175,165,200,215,210,230,245,240,265,280,295]}
};
const FC_SKUS=[
 {sku:'HC-1042',product:'Surface Cleaner 1L',category:'home',stock:240,daily:14,error:.12},
 {sku:'HC-2158',product:'Laundry Detergent 2L',category:'home',stock:520,daily:13,error:.09},
 {sku:'HC-3301',product:'Storage Box 20L',category:'home',stock:180,daily:8,error:.18},
 {sku:'PC-1042',product:'Daily Shampoo 500ml',category:'personal',stock:190,daily:12,error:.14},
 {sku:'PC-2158',product:'Body Wash 1L',category:'personal',stock:310,daily:10,error:.11},
 {sku:'PC-3301',product:'Hand Cream 100ml',category:'personal',stock:380,daily:5,error:.22}
];
const FC_SCENARIOS={base:{label:'Base',factor:1,error:0},promotion:{label:'Promotion uplift',factor:1.18,error:.025},slowdown:{label:'Demand slowdown',factor:.88,error:.015}};
const FC_SERVICE={90:1.28,95:1.65,98:2.05};
let fcRows=[],fcSort={key:'sku',direction:1};

function fcCalculate(){
 const category=document.getElementById('category').value;
 const horizon=Number(document.getElementById('horizon').value);
 const lead=Number(document.getElementById('leadTime').value);
 const service=document.getElementById('serviceLevel').value;
 const scenarioKey=document.getElementById('demandScenario').value;
 const scenario=FC_SCENARIOS[scenarioKey],source=FC_DATA[category];
 const skus=FC_SKUS.filter(row=>category==='all'||row.category===category);
 fcRows=skus.map(row=>{
  const adjustedDaily=row.daily*scenario.factor;
  const forecast=Math.round(adjustedDaily*horizon);
  const leadDemand=Math.round(adjustedDaily*lead);
  // Safety stock uses forecast error, service factor and square-root lead-time scaling.
  const safety=Math.round(adjustedDaily*row.error*FC_SERVICE[service]*Math.sqrt(lead));
  const reorder=leadDemand+safety;
  const order=Math.max(0,forecast+safety-row.stock);
  const cover=Math.max(0,Math.round(row.stock/adjustedDaily));
  const risk=row.stock<reorder?'High':cover>horizon*1.5?'Excess':'Controlled';
  const action=risk==='High'?'Reorder':risk==='Excess'?'Reduce future purchases':row.error>.2?'Review forecast':cover<lead*2?'Monitor':'Hold';
  const reasons={Reorder:'Stock is below the uncertainty-adjusted reorder point.',Monitor:'Coverage is adequate but close to the lead-time requirement.',Hold:'Current stock supports expected demand.','Reduce future purchases':'Coverage materially exceeds the selected horizon.','Review forecast':'Forecast uncertainty is high relative to demand.'};
  return {...row,forecast,error:(row.error+scenario.error)*100,leadDemand,safety,reorder,order,cover,risk,action,reason:reasons[action]};
 });
 const demand=Math.round(source.baseDemand*(horizon/30)*scenario.factor);
 const safety=fcRows.reduce((sum,row)=>sum+row.safety,0),order=fcRows.reduce((sum,row)=>sum+row.order,0);
 const excess=fcRows.filter(row=>row.risk==='Excess').reduce((sum,row)=>sum+Math.max(0,row.stock-row.forecast),0);
 const risk=fcRows.filter(row=>row.risk==='High').length;
 const cover=Math.round(fcRows.reduce((sum,row)=>sum+row.cover,0)/fcRows.length);
 updateKpi('demandKpi',formatNumber(demand));updateKpi('mapeKpi',`${(source.mape+scenario.error*100+(horizon-30)/75).toFixed(1)}%`);updateKpi('biasKpi',formatPercent(source.bias+(scenarioKey==='promotion'?-1.2:scenarioKey==='slowdown'?1.1:0)));updateKpi('riskKpi',risk);updateKpi('safetyKpi',formatNumber(safety));updateKpi('orderKpi',formatNumber(order));updateKpi('coverKpi',`${cover} days`);updateKpi('excessKpi',formatNumber(excess));
 document.getElementById('demandNote').textContent=`Next ${horizon} days`;
 document.getElementById('filterStatus').textContent=`${source.label} · ${horizon} days · ${service}% service · ${scenario.label}`;
 fcRenderCharts(source,scenario,horizon);
 fcRenderTable();
 fcRenderInsights();
 document.getElementById('forecastImpact').innerHTML=[['Forecast demand',formatNumber(demand)],['Safety stock',formatNumber(safety)],['Recommended order',formatNumber(order)],['Potential excess',formatNumber(excess)]].map(([label,value])=>`<article><span>${label}</span><strong>${value}</strong></article>`).join('');
}
function fcRenderCharts(source,scenario,horizon){
 const weeks=horizon/7>12?12:Math.max(4,Math.round(horizon/7)),actual=source.actual.slice(-weeks),fitted=actual.map((v,i)=>Math.round(v*(i%2?1.02:.98))),future=actual.map((v,i)=>Math.round(v*scenario.factor*(1+.012*i)));
 svgLineChart(document.getElementById('forecastChart'),[{values:actual},{values:fitted},{values:future}],actual.map((_,i)=>`W${i+1}`));
 const names=['Recent demand','Promotion','Price','Seasonality'];document.getElementById('driverList').innerHTML=source.drivers.map((value,i)=>`<div class="bar-row"><span>${names[i]}</span><div class="bar-track"><div class="bar-fill" style="width:${value}%"></div></div><b>${value}</b></div>`).join('');
 const labels=fcRows.map(row=>row.sku.replace(/^[A-Z]+-/,''));
 svgGroupedBarChart(document.getElementById('stockChart'),labels,[{name:'Current stock',values:fcRows.map(row=>row.stock)},{name:'Reorder point',values:fcRows.map(row=>row.reorder)}]);
 svgBarChart(document.getElementById('riskChart'),['High','Controlled','Excess'],['High','Controlled','Excess'].map(risk=>fcRows.filter(row=>row.risk===risk).length));
 svgGroupedBarChart(document.getElementById('recommendedChart'),labels,[{name:'Current',values:fcRows.map(row=>row.stock)},{name:'Recommended',values:fcRows.map(row=>row.stock+row.order)}]);
}
function fcRenderInsights(){
 const high=fcRows.find(row=>row.risk==='High'),stable=fcRows.find(row=>row.action==='Hold')||fcRows[0],excess=fcRows.find(row=>row.risk==='Excess');
 const insights=[];
 if(high)insights.push({title:`${high.product} requires replenishment`,copy:`Current stock is below its reorder point of ${formatNumber(high.reorder)} units. Recommended order: ${formatNumber(high.order)}.`,badge:'<span class="badge bad">Reorder</span>'});
 insights.push({title:`${stable.product} has manageable coverage`,copy:`Estimated cover is ${stable.cover} days under the selected assumptions.`,badge:'<span class="badge good">Monitor</span>'});
  if(excess)insights.push({title:`${excess.product} carries excess-stock risk`,copy:`Coverage extends to ${excess.cover} days, supporting lower future purchasing.`,badge:'<span class="badge warn">Reduce</span>'});
  if(!excess)insights.push({title:'No material excess-stock signal in this view',copy:'Selected SKUs remain within the synthetic coverage threshold; continue monitoring slower items.',badge:'<span class="badge good">Controlled</span>'});
  insights.push({title:'Uncertainty changes inventory, not just the chart',copy:'Higher service levels and longer lead times increase safety stock and reorder points.',badge:'<span class="badge neutral">Decision rule</span>'});
 renderInsightCards(document.getElementById('forecastInsights'),insights);
}
function fcRenderTable(){
 const action=document.getElementById('forecastActionFilter').value;let rows=filterObjects(fcRows,'action',action);rows=sortObjects(rows,fcSort.key,fcSort.direction);
 document.getElementById('recommendationRows').innerHTML=rows.map(row=>`<tr><td>${row.sku}</td><td>${row.product}</td><td>${row.category==='home'?'Home care':'Personal care'}</td><td>${row.stock}</td><td>${row.forecast}</td><td>${row.error.toFixed(1)}%</td><td>${row.leadDemand}</td><td>${row.safety}</td><td>${row.reorder}</td><td>${row.order}</td><td>${row.cover}</td><td>${row.risk}</td><td><span class="badge ${row.action==='Reorder'?'bad':row.action==='Hold'?'good':'warn'}">${row.action}</span></td><td>${row.reason}</td></tr>`).join('');
 document.getElementById('forecastTableStatus').textContent=`${rows.length} of ${fcRows.length} SKUs shown`;
}
['category','horizon','serviceLevel','leadTime','demandScenario'].forEach(id=>document.getElementById(id).addEventListener('change',fcCalculate));
document.getElementById('forecastActionFilter').addEventListener('change',fcRenderTable);
bindTableSort(document.querySelector('#recommendations'),key=>{fcSort.direction=fcSort.key===key?-fcSort.direction:1;fcSort.key=key;fcRenderTable()});
fcCalculate();
