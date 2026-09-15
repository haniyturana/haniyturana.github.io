"""Update public assets after the data export and verify every result file."""
import json
import gzip
from pathlib import Path
import numpy as np
from export_dashboard import unpack_records

root=Path(__file__).resolve().parents[1]
site=root/'projects/b2b-pricing-intelligence'
js=site/'app.js'
s=js.read_text(encoding='utf-8')
old='const r=await fetch(`data/${n}.json`);if(!r.ok)throw Error(`${n}: HTTP ${r.status}`);data[n]=await r.json();'
new='''let r;if('DecompressionStream' in window){r=await fetch(`data/${n}.json.gz`);if(r.ok){data[n]=unpack(await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json());return;}}r=await fetch(`data/${n}.json`);if(!r.ok)throw Error(`${n}: HTTP ${r.status}`);data[n]=unpack(await r.json());'''
s=s.replace(old,new)
if 'function unpack(' not in s:
    s += "\nfunction unpack(v){if(!v.columns)return v;return v.rows.map(row=>Object.fromEntries(v.columns.map((col,i)=>[col,v.dictionaries[i]&&row[i]!=null?v.dictionaries[i][row[i]]:row[i]])));}\n"
js.write_text(s,encoding='utf-8')
html=site/'index.html'
s=html.read_text(encoding='utf-8')
credit='<p>Source: Chen, D. (2012). <a href="https://doi.org/10.24432/C5CG6D">Online Retail II, UCI Machine Learning Repository</a>. Licensed CC BY 4.0. Aggregated and analysed for this portfolio.</p>'
if credit not in s: s=s.replace('</main>',credit+'</main>')
html.write_text(s,encoding='utf-8')
records={}
for p in (site/'data').glob('*.json'):
    raw=p.read_bytes()
    records[p.stem]=unpack_records(json.loads(raw,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v))))
    with gzip.open(str(p)+'.gz','wb') as f:f.write(raw)
m=records['metadata']; pairs=records['pricing_opportunities']
assert m['status']=='ready' and m['customers']==len(records['customer_summary'])
assert np.isclose(sum(r['revenue'] for r in pairs),m['identified_revenue'])
assert all(np.isclose(r['price'],r['revenue']/r['quantity']) for r in pairs)
assert all(r['CustomerID'].startswith('C') for r in pairs)
models={r['StockCode']:r for r in records['elasticity']}
for r in records['scenario']:
    assert models[r['StockCode']]['eligible']
    assert np.isclose(r['revenue'],r['price']*r['quantity'])
for r in pairs:
    if r['impact'] is not None:
        assert models[r['StockCode']]['eligible']
        assert np.isclose(r['impact'],r['revenue']*((r['new_price']/r['price'])**(1+r['beta'])-1),atol=.001)
assert np.isclose(m['modelled_opportunity'],sum(r['impact'] for r in pairs if r['impact'] is not None and r['impact']>0))
print(json.dumps(m,indent=2))
print('PASS: strict JSON, source totals, customer aliases, weighted prices, scenario formulas and model eligibility.')
print('Compressed data bytes:',sum(p.stat().st_size for p in (site/'data').glob('*.gz')))
