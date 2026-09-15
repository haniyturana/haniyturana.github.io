"""Validate exported diagnostic aggregates and independent exploratory scenarios."""
import json
import gzip
from pathlib import Path
import numpy as np
import pandas as pd
from export_dashboard import unpack_records

root=Path(__file__).resolve().parents[1]
site=root/'projects/b2b-pricing-intelligence'
records={}
for p in (site/'data').glob('*.json'):
    raw=p.read_bytes()
    records[p.stem]=unpack_records(json.loads(raw,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v))))
    with gzip.open(str(p)+'.gz','rb') as f:assert f.read()==raw
m=records['metadata']; pairs=records['pricing_opportunities']
assert m['status']=='ready' and m['customers']==len(records['customer_summary'])
assert np.isclose(sum(r['revenue'] for r in pairs),m['identified_revenue'])
assert all(np.isclose(r['price'],r['revenue']/r['quantity']) for r in pairs)
assert all(r['CustomerID'].startswith('C') for r in pairs)
models={r['StockCode']:r for r in records['elasticity']}
for r in records['scenario']:
    assert models[r['StockCode']]['eligible']
    assert np.isclose(r['revenue'],r['price']*r['quantity'])
frame=pd.DataFrame(pairs)
assert not {'confidence','new_price','impact','beta','recommendation'} & set(frame.columns)
assert 'modelled_opportunity' not in m
assert np.isclose(m['identified_revenue']+m['missing_customer_revenue'],m['total_revenue'])
assert np.allclose(frame.benchmark,frame.groupby('StockCode').price.transform('median'))
assert np.allclose(frame.sku_median_quantity,frame.groupby('StockCode').quantity.transform('median'))
assert np.allclose(frame.gap,(frame.benchmark-frame.price)/frame.benchmark)
sku=pd.DataFrame(records['sku_pricing']).set_index('StockCode')
evidence=(frame.StockCode.map(sku.customers)>=10)&(frame.StockCode.map(sku.orders)>=30)&(frame.orders>=3)
below=frame.gap>=m['gap_threshold']
low=frame.quantity<=frame.sku_median_quantity
expected=np.select([~evidence,below&low,below],['Insufficient Evidence','Pricing Review','Possible Volume Justification'],default='Maintain / No Material Gap')
assert (frame.review_status==expected).all()
assert m['relationships_reviewed']==len(frame)
assert m['pricing_review_cases']==int((expected=='Pricing Review').sum())>0
assert m['possible_volume_cases']==int((expected=='Possible Volume Justification').sum())>0
print(json.dumps(m,indent=2))
print('PASS: JSON/gzip, source totals, aliases, weighted prices, benchmarks, review classifications and separate exploratory scenarios.')
print('Compressed data bytes:',sum(p.stat().st_size for p in (site/'data').glob('*.gz')))
