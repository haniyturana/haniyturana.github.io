"""Export existing cleaned transactions using the canonical merchandise master."""
from pathlib import Path
import json
import gzip
import numpy as np
import pandas as pd
from load_uci import clean_product_master

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / 'projects/b2b-pricing-intelligence/data'

def unpack_records(value):
    if not isinstance(value, dict) or 'columns' not in value:
        return value
    dictionaries = value['dictionaries']
    return [dict(zip(value['columns'], [dictionaries[str(i)][x] if str(i) in dictionaries and x is not None else x for i,x in enumerate(row)])) for row in value['rows']]

def export_dashboard(df, output=DEFAULT_OUTPUT, gap_threshold=.15):
    """Export audited aggregates; optional scipy enables observational regressions."""
    if not np.isfinite(gap_threshold) or not 0 < gap_threshold < 1:
        raise ValueError('gap_threshold must be between 0 and 1 (exclusive).')
    d = df.rename(columns={'Invoice': 'InvoiceNo', 'Price': 'UnitPrice', 'Customer ID': 'CustomerID'}).copy()
    required = ['InvoiceNo', 'StockCode', 'CustomerID', 'Quantity', 'UnitPrice', 'InvoiceDate', 'Revenue']
    missing = set(required) - set(d.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    if d.empty or not pd.api.types.is_datetime64_any_dtype(d.InvoiceDate):
        raise ValueError('Supply a nonempty cleaned df with datetime InvoiceDate.')
    if d[required].drop(columns='CustomerID').isna().any().any() or not np.isfinite(d[['Quantity','UnitPrice','Revenue']]).all().all() or (d[['Quantity','UnitPrice']] <= 0).any().any():
        raise ValueError('Cleaned-data preconditions failed; no rows were removed.')
    if d.InvoiceNo.astype(str).str.upper().str.startswith('C').any() or not np.allclose(d.Revenue, d.Quantity*d.UnitPrice):
        raise ValueError('Cancelled invoices or Revenue mismatch; inspect upstream cleaning.')
    d = clean_product_master(d)
    if d.empty:
        raise ValueError('No merchandise transactions available.')
    quality = {'date_start': str(d.InvoiceDate.min().date()), 'date_end': str(d.InvoiceDate.max().date()), 'rows': len(d), 'orders': d.InvoiceNo.nunique(), 'total_revenue': d.Revenue.sum(), 'missing_customer_rows': int(d.CustomerID.isna().sum()), 'missing_customer_revenue': d.loc[d.CustomerID.isna(),'Revenue'].sum(), 'quantity_p999': d.Quantity.quantile(.999), 'price_p999': d.UnitPrice.quantile(.999), 'max_quantity': d.Quantity.max(), 'max_price': d.UnitPrice.max()}
    d = d.loc[d.CustomerID.notna()].copy()
    if d.empty:
        raise ValueError('No identified customers available.')
    # Public-facing sequential aliases; no original customer IDs exported.
    aliases = {v: f'C{i:05d}' for i,v in enumerate(sorted(d.CustomerID.astype(str).unique()),1)}
    d['CustomerID'] = d.CustomerID.astype(str).map(aliases)
    d['StockCode'] = d.StockCode.astype(str)
    if 'Description' not in d:
        d['Description'] = ''
    c = d.groupby('CustomerID').agg(revenue=('Revenue','sum'), quantity=('Quantity','sum'), orders=('InvoiceNo','nunique'), skus=('StockCode','nunique'), first=('InvoiceDate','min'), last=('InvoiceDate','max')).reset_index()
    c['aov'] = c.revenue/c.orders
    c['units_per_order'] = c.quantity/c.orders
    c['recency_days'] = (d.InvoiceDate.max()-c['last']).dt.days
    c['orders_per_month'] = c.orders / (((c['last']-c['first']).dt.days+1)/30.4375).clip(lower=1)
    rank = c.revenue.rank(pct=True)
    c['segment'] = np.select([(rank >= .95)&(c.orders>=5), rank>=.8, rank>=.5], ['Strategic','Large','Medium'],default='Small')
    p = d.groupby(['CustomerID','StockCode']).agg(quantity=('Quantity','sum'), revenue=('Revenue','sum'), orders=('InvoiceNo','nunique')).reset_index()
    p['price'] = p.revenue/p.quantity
    p['order_quantity'] = p.quantity/p.orders
    latest = d.sort_values('InvoiceDate').groupby(['CustomerID','StockCode']).tail(1)[['CustomerID','StockCode','UnitPrice']].rename(columns={'UnitPrice':'latest_price'})
    p = p.merge(latest).merge(c[['CustomerID','segment']])
    s = p.groupby('StockCode').agg(customers=('CustomerID','nunique'), benchmark=('price','median'), minimum=('price','min'), maximum=('price','max'), quantity=('quantity','sum'), revenue=('revenue','sum')).reset_index()
    counts = d.groupby('StockCode').agg(transactions=('InvoiceNo','size'), orders=('InvoiceNo','nunique')).reset_index()
    s = s.merge(counts).merge(d[['StockCode', 'Description']].drop_duplicates('StockCode'))
    s['weighted_price'] = s.revenue/s.quantity
    s['spread'] = (s.maximum-s.minimum)/s.benchmark
    s['eligible'] = (s.customers>=10)&(s.orders>=30)
    p = p.merge(s[['StockCode','Description','benchmark','eligible']])
    # Match exported precision so an exact 15% gap has a stable classification.
    p['gap'] = ((p.benchmark-p.price)/p.benchmark).round(10)
    p['sku_median_quantity'] = p.groupby('StockCode').quantity.transform('median')
    low = p.quantity <= p.sku_median_quantity
    p['volume_position'] = np.where(low, 'At or below SKU customer median', 'Above SKU customer median')
    p['review_status'] = np.select([~p.eligible | (p.orders<3), (p.gap>=gap_threshold)&low, p.gap>=gap_threshold], ['Insufficient Evidence','Pricing Review','Possible Volume Justification'],default='Maintain / No Material Gap')
    p['reason'] = np.select([p.review_status.eq('Insufficient Evidence'),p.review_status.eq('Pricing Review'),p.review_status.eq('Possible Volume Justification')], ['Fewer than 10 SKU customers, 30 SKU orders, or 3 customer-SKU orders.', f'Effective price meets the {gap_threshold:.0%} below-median screening threshold; quantity is at or below the SKU customer median. Review whether commercial terms justify the gap.', f'Effective price meets the {gap_threshold:.0%} below-median screening threshold; quantity is above the SKU customer median. Higher volume may justify the difference; review commercial terms before changing price.'],default='No material below-benchmark gap under the configurable screening rule.')
    d['month'] = d.InvoiceDate.dt.to_period('M').astype(str)
    monthly = d.groupby(['StockCode','month']).agg(quantity=('Quantity','sum'),revenue=('Revenue','sum')).reset_index()
    monthly['price'] = monthly.revenue/monthly.quantity
    fits, scenarios = [], []
    try:
        from scipy.stats import linregress
    except ImportError:
        linregress = None
    for sku,g in monthly.groupby('StockCode'):
        if linregress is None or len(g)<12 or g.price.nunique()<4 or g.price.std()/g.price.mean()<.05 or g.quantity.std()/g.quantity.mean()<.05:
            continue
        fit = linregress(np.log(g.price),np.log(g.quantity))
        if not np.isfinite([fit.slope,fit.pvalue,fit.rvalue]).all():
            continue
        eligible = bool(-3 <= fit.slope < 0 and fit.pvalue<.05 and fit.rvalue**2>=.2)
        fits.append(dict(StockCode=sku,beta=fit.slope,pvalue=fit.pvalue,r2=fit.rvalue**2,n=len(g),eligible=eligible,interpretation='Exploratory monthly association; seasonality, inventory availability and customer mix are uncontrolled. Promotions and contracts are unavailable. Association does not prove price caused demand changes.',points=g[['month','price','quantity']].to_dict('records')))
        if eligible:
            base_price=g.revenue.sum()/g.quantity.sum(); base_qty=g.quantity.sum()
            for change in [-.05,0,.03,.05,.1]:
                price=base_price*(1+change); qty=base_qty*(1+change)**fit.slope
                scenarios.append(dict(StockCode=sku,change=change,price=price,quantity=qty,revenue=price*qty,impact=price*qty-g.revenue.sum()))
    # Diagnostic classifications above do not depend on regression or scenarios.
    quality.update(status='ready',customers=len(c),skus=len(s),identified_revenue=c.revenue.sum(),relationships_reviewed=len(p),pricing_review_cases=int(p.review_status.eq('Pricing Review').sum()),possible_volume_cases=int(p.review_status.eq('Possible Volume Justification').sum()),gap_threshold=gap_threshold,elasticity_available=linregress is not None)
    out=Path(output); out.mkdir(parents=True,exist_ok=True)
    def write(name,value):
        if isinstance(value,pd.DataFrame):
            if name == 'pricing_opportunities':
                frame=value.copy()
                dictionaries={}
                for i,col in enumerate(frame.columns):
                    if pd.api.types.is_string_dtype(frame[col]) or frame[col].dtype == object:
                        codes, labels=pd.factorize(frame[col],sort=False)
                        dictionaries[str(i)]=labels.tolist()
                        frame[col]=pd.Series(codes,index=frame.index).replace(-1,np.nan)
                value={'columns':list(frame.columns),'dictionaries':dictionaries,'rows':json.loads(frame.to_json(orient='values'))}
            else:
                value=json.loads(value.to_json(orient='records',date_format='iso'))
        text=json.dumps(value,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x),separators=(',',':'))
        (out/f'{name}.json').write_text(text,encoding='utf-8')
        with gzip.open(out/f'{name}.json.gz', 'wb') as f:
            f.write(text.encode('utf-8'))
    write('metadata',quality)
    write('customer_summary',c.drop(columns=['first','last']))
    write('sku_pricing',s)
    write('pricing_opportunities',p)
    write('elasticity',fits)
    write('scenario',scenarios)
    assert np.isclose(c.revenue.sum(),p.revenue.sum()) and np.isclose(s.revenue.sum(),p.revenue.sum())
    print(f'Exported {len(c):,} customers, {len(s):,} SKUs, {len(p):,} customer-SKU aggregates to {out}')
    return quality
