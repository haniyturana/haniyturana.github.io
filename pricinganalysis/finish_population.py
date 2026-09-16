"""Validate exported diagnostic aggregates and independent exploratory scenarios."""
import json
import gzip
from pathlib import Path
import numpy as np
import pandas as pd
from export_dashboard import unpack_records
from load_uci import clean_product_master, NON_MERCHANDISE_CODES

# Identity/name regression: variants merge, the mode beats the latest name,
# ties are stable, missing names do not win, and unusual merchandise survives.
sample = pd.DataFrame({
    'StockCode': [' abc ', 'ABC', 'abc', 'ABC', 'ABC', 'tie', 'TIE', 'blank', ' m ', 'PADS', 'DCGS0003'],
    'Description': [' Main  name ', 'Main name', 'Main name', 'Newest name', None, 'Zebra', 'Alpha', None, 'Manual', 'Cushions', 'Ashtray'],
    'UnitPrice': [1, 1, 1, 1, 1, 1, 1, 1, 100, 0.001, 999999],
    'Quantity': [1, 1, 1, 1, 1, 1, 1, 1, 1, 999999, 1],
})
clean = clean_product_master(sample)
assert len(clean) == len(sample)-1
assert clean.loc[clean.StockCode.eq('ABC'), 'Description'].eq('Main name').all()
assert clean.loc[clean.StockCode.eq('TIE'), 'Description'].eq('Alpha').all()
assert clean.loc[clean.StockCode.eq('BLANK'), 'Description'].eq('').all()
assert clean.loc[clean.StockCode.eq('PADS'), 'UnitPrice'].item() == 0.001
assert clean.loc[clean.StockCode.eq('DCGS0003'), 'UnitPrice'].item() == 999999
pd.testing.assert_frame_equal(clean, clean_product_master(clean))
pd.testing.assert_frame_equal(clean.sort_index(), clean_product_master(sample.iloc[::-1]).sort_index())

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
assert sku.index.is_unique
assert sku.index.to_series().eq(sku.index.to_series().str.strip().str.upper()).all()
for name in ['sku_pricing', 'pricing_opportunities', 'elasticity', 'scenario']:
    assert not {r['StockCode'] for r in records[name]} & NON_MERCHANDISE_CODES.keys()
assert frame.Description.eq(frame.StockCode.map(sku.Description)).all()
# Independently reconcile the exports to the pre-product-cleaning cached source.
source = pd.read_pickle(Path(__file__).resolve().parent / '.data-cache/cleaned.pkl')
source['StockCode'] = source.StockCode.astype('string').str.strip().str.upper()
before = source.StockCode.nunique()
identified_before = source.loc[source.CustomerID.notna(), 'StockCode'].nunique()
source = source.loc[~source.StockCode.isin(NON_MERCHANDISE_CODES)].copy()
source['Description'] = source.Description.astype('string').str.strip().str.replace(r'\s+', ' ', regex=True)
multiple = int(source.groupby('StockCode').Description.nunique().gt(1).sum())
names = source.groupby('StockCode').Description.agg(lambda s: s.dropna().loc[lambda v: v.ne('')].mode().iloc[0])
assert sku.Description.eq(names.reindex(sku.index)).all()
identified = source.loc[source.CustomerID.notna()]
assert set(sku.index) == set(identified.StockCode)
assert m['rows'] == len(source) and np.isclose(m['total_revenue'], source.Revenue.sum())
assert np.isclose(m['identified_revenue'], identified.Revenue.sum())
assert m['max_price'] == source.UnitPrice.max() and m['max_quantity'] == source.Quantity.max()
print(f'Normalized source SKUs: {before} -> {source.StockCode.nunique()}; identified-customer SKUs: {identified_before} -> {len(sku)}; merchandise codes with multiple descriptions consolidated: {multiple}')
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
