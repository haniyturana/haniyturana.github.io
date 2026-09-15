'use strict';
// Pure scenario calculation: no historical dataset is read or modified.
function calculateCommercialScenario(v){
  for(const key of ['cost','months','claimRate','claimCost','service','target'])if(v[key]==null||!Number.isFinite(v[key])||v[key]<0)throw Error('Enter a non-negative number in every required scenario field.');
  if(!Number.isInteger(v.months))throw Error('Warranty period must be a whole number of months.');
  if(v.claimRate>100)throw Error('Warranty claim probability must be between 0% and 100%.');
  if(v.target>=100)throw Error('Target gross margin must be below 100%.');
  if(v.claimRate>0&&v.months===0)throw Error('Enter the warranty period covered by your claim-rate assumption.');
  if(v.claimRate>0&&!v.confirmed)throw Error('Confirm that the claim probability covers the entered warranty period.');
  for(const key of ['current','benchmark'])if(v[key]!=null&&(!Number.isFinite(v[key])||v[key]<=0))throw Error('Optional selling price and benchmark must be positive, or left blank.');
  const warranty=v.claimRate/100*v.claimCost,serve=v.cost+warranty+v.service,required=serve/(1-v.target/100),profit=v.current==null?null:v.current-serve,margin=v.current==null?null:profit/v.current;
  if(![warranty,serve,required].every(Number.isFinite))throw Error('Inputs are too large to calculate. Enter smaller amounts.');
  return {warranty,serve,required,profit,margin,requiredGap:v.current==null?null:v.current-required,benchmarkGap:v.benchmark==null?null:required-v.benchmark,marginAmount:required-serve};
}
function commercial(){
  const ids=['cost','months','claimRate','claimCost','service','target','current','benchmark'];
  const values=Object.fromEntries(ids.map(id=>[id,$('commercial-'+id).value.trim()===''?null:Number($('commercial-'+id).value)]));
  values.confirmed=$('commercial-confirm').checked;
  let r;try{r=calculateCommercialScenario(values);}catch(e){$('commercial-status').textContent=e.message;$('commercial-kpis').innerHTML='';$('commercial-decision').textContent='';if(window.Plotly)Plotly.purge('commercial-waterfall');return;}
  $('commercial-status').textContent=`User-defined scenario · ${fmt(values.months)}-month warranty · ${fmt(values.claimRate)}% claim probability across that period. Duration is context; it does not multiply warranty cost.`;
  const cards=[['Cost to serve',gbp(r.serve),'Per unit'],['Expected warranty cost / unit',gbp(r.warranty),'Probability × average claim cost'],['Required price for target margin',gbp(r.required),'Recommended Price Floor'],['Current gross margin',pct(r.margin),r.profit==null?'Enter current selling price':`Gross profit per unit: ${gbp(r.profit)}`],['Price gap vs required price',gbp(r.requiredGap),'Current price − required price'],['Price gap vs market benchmark',gbp(r.benchmarkGap),'Required price − user-defined benchmark']];
  $('commercial-kpis').innerHTML=cards.map(c=>`<div class="card">${esc(c[0])}<strong>${esc(c[1])}</strong><span>${esc(c[2])}</span></div>`).join('');
  const messages=[];
  if(values.current!=null)messages.push(values.current<r.required?'Current price does not meet the selected target gross margin under this cost scenario.':'Current price meets the selected target gross margin under this cost scenario.');
  if(values.benchmark!=null)messages.push(r.required>values.benchmark?'Required price is above the market benchmark. Management may need to review cost-to-serve, target margin, product differentiation, or customer-specific commercial terms.':r.required<values.benchmark?'Required price is below the market benchmark, suggesting potential pricing headroom. Further validation using customer demand, competitor positioning and contractual terms is recommended.':'Required price equals the user-defined market benchmark. Validate demand and commercial terms before making a pricing decision.');
  if(!messages.length)messages.push('Enter an optional current price or market benchmark to compare it with the scenario price floor.');
  messages.push('Pricing headroom alone is not a recommendation to increase price.');
  $('commercial-decision').textContent=messages.join(' ');
  chart('commercial-waterfall',[{type:'waterfall',orientation:'v',measure:['relative','relative','relative','total','relative','total'],x:['Product cost','Warranty provision','Service cost','Cost to serve','Required margin','Recommended price floor'],y:[values.cost,r.warranty,values.service,0,r.marginAmount,0],text:[values.cost,r.warranty,values.service,r.serve,r.marginAmount,r.required].map(gbp),textposition:'outside',connector:{line:{color:'#aebdcb'}},increasing:{marker:{color:'#168b80'}},totals:{marker:{color:'#203e59'}},hovertemplate:'%{x}<br>%{text}<extra></extra>'}],'','Scenario amount per unit (GBP)');
}
document.querySelectorAll('#commercial input').forEach(input=>input.addEventListener('input',()=>{if(input.id==='commercial-months')$('commercial-confirm').checked=false;commercial();}));
$('commercial-reset').onclick=()=>{document.querySelectorAll('#commercial input').forEach(i=>{if(i.type==='checkbox')i.checked=false;else i.value='';});commercial();};
commercial();
