
function svgLineChart(el, series, labels){
 const w=900,h=300,p={l:48,r:18,t:20,b:42};
 const values=series.flatMap(s=>s.values); const min=Math.min(...values)*.95, max=Math.max(...values)*1.05;
 const x=i=>p.l+i*(w-p.l-p.r)/(labels.length-1); const y=v=>p.t+(max-v)*(h-p.t-p.b)/(max-min||1);
 let grid=''; for(let i=0;i<5;i++){const yy=p.t+i*(h-p.t-p.b)/4; const val=max-i*(max-min)/4;grid+=`<line x1="${p.l}" y1="${yy}" x2="${w-p.r}" y2="${yy}" stroke="#e5e9eb"/><text x="${p.l-8}" y="${yy+4}" text-anchor="end" font-size="11" fill="#667085">${Math.round(val)}</text>`}
 let xs=''; labels.forEach((lab,i)=>{if(i%Math.ceil(labels.length/7)===0||i===labels.length-1) xs+=`<text x="${x(i)}" y="${h-13}" text-anchor="middle" font-size="11" fill="#667085">${lab}</text>`});
 const colors=['#137c8b','#8fa3b8','#b06b3b'];
 let lines=''; series.forEach((s,si)=>{const pts=s.values.map((v,i)=>`${x(i)},${y(v)}`).join(' ');lines+=`<polyline points="${pts}" fill="none" stroke="${colors[si]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;s.values.forEach((v,i)=>lines+=`<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${colors[si]}"/>`)});
 el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Line chart" style="width:100%;height:100%">${grid}${xs}${lines}</svg>`;
}
function svgBarChart(el, labels, values){
 const w=900,h=300,p={l:48,r:18,t:20,b:58},max=Math.max(...values)*1.15;
 const band=(w-p.l-p.r)/labels.length,bw=band*.58;
 let grid='';for(let i=0;i<5;i++){const yy=p.t+i*(h-p.t-p.b)/4;const val=max-i*max/4;grid+=`<line x1="${p.l}" y1="${yy}" x2="${w-p.r}" y2="${yy}" stroke="#e5e9eb"/><text x="${p.l-8}" y="${yy+4}" text-anchor="end" font-size="11" fill="#667085">${Math.round(val)}</text>`}
 let bars='';values.forEach((v,i)=>{const x=p.l+i*band+(band-bw)/2;const bh=v/max*(h-p.t-p.b);const y=h-p.b-bh;bars+=`<rect x="${x}" y="${y}" width="${bw}" height="${bh}" rx="6" fill="#137c8b"/><text x="${x+bw/2}" y="${h-20}" text-anchor="middle" font-size="11" fill="#667085">${labels[i]}</text>`});
 el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Bar chart" style="width:100%;height:100%">${grid}${bars}</svg>`;
}
function svgGroupedBarChart(el, labels, series, suffix=''){
 const w=900,h=320,p={l:50,r:18,t:30,b:64};
 const max=Math.max(...series.flatMap(s=>s.values))*1.18;
 const group=(w-p.l-p.r)/labels.length;
 const bw=Math.min(34,(group*.72)/series.length);
 const palette=['#137c8b','#8fa3b8','#b06b3b','#6d7f91'];
 let grid='';for(let i=0;i<5;i++){const yy=p.t+i*(h-p.t-p.b)/4;const val=max-i*max/4;grid+=`<line x1="${p.l}" y1="${yy}" x2="${w-p.r}" y2="${yy}" stroke="#e5e9eb"/><text x="${p.l-8}" y="${yy+4}" text-anchor="end" font-size="11" fill="#667085">${Math.round(val)}${suffix}</text>`}
 let bars='';labels.forEach((lab,i)=>{const start=p.l+i*group+(group-bw*series.length)/2;series.forEach((s,si)=>{const v=s.values[i],bh=v/max*(h-p.t-p.b),x=start+si*bw,y=h-p.b-bh;bars+=`<rect x="${x}" y="${y}" width="${bw-3}" height="${bh}" rx="5" fill="${palette[si]}"><title>${s.name}: ${v}${suffix}</title></rect><text x="${x+(bw-3)/2}" y="${Math.max(p.t+10,y-5)}" text-anchor="middle" font-size="10" font-weight="700" fill="#415568">${v}${suffix}</text>`});bars+=`<text x="${p.l+i*group+group/2}" y="${h-28}" text-anchor="middle" font-size="11" fill="#667085">${lab}</text>`});
 let legend='';series.forEach((s,si)=>{legend+=`<rect x="${p.l+si*150}" y="4" width="12" height="12" rx="3" fill="${palette[si]}"/><text x="${p.l+18+si*150}" y="15" font-size="11" fill="#667085">${s.name}</text>`});
 el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Grouped bar chart" style="width:100%;height:100%">${legend}${grid}${bars}</svg>`;
}
