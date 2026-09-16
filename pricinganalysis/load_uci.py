"""Reproducible official UCI source, cached locally and excluded from publication."""
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile
import pandas as pd

# Explicit transaction codes found by auditing both sheets of Online Retail II.
# No price, quantity, code-pattern or description-keyword exclusion is applied.
NON_MERCHANDISE_CODES = {
    'M': 'Manual transaction, not an identified merchandise SKU',
    'POST': 'Postage charge',
    'DOT': 'Dotcom postage charge',
    'C2': 'Carriage charge',
    'ADJUST': 'Administrative adjustment',
    'ADJUST2': 'Administrative adjustment',
    'B': 'Bad-debt adjustment',
    'BANK CHARGES': 'Bank charge',
    'AMAZONFEE': 'Amazon fee',
    'CRUK': 'Charity commission',
    'D': 'Discount transaction',
    'S': 'Generic samples transaction, not an identified merchandise SKU',
    'TEST001': 'Test product entry',
    'TEST002': 'Test product entry',
    '22016': 'Gift voucher (100 GBP), not merchandise',
    **{f'GIFT_0001_{amount}': f'Gift voucher ({amount} GBP), not merchandise'
       for amount in (10, 20, 30, 40, 50, 70, 80)},
}


def clean_product_master(df):
    """Normalize SKU identity, exclude audited service codes, and resolve names.

    Description votes use nonempty, non-null whitespace-normalized text across
    all supplied cleaned transactions, including unidentified customers. Ties
    use lexical order; an SKU with no valid description retains an empty name.
    """
    d = df.copy()
    d['StockCode'] = d.StockCode.astype('string').str.strip().str.upper()
    if d.StockCode.isna().any() or d.StockCode.eq('').any():
        raise ValueError('StockCode must be a nonempty canonical product identifier.')
    d = d.loc[~d.StockCode.isin(NON_MERCHANDISE_CODES)].copy()
    descriptions = (d.Description if 'Description' in d else pd.Series('', index=d.index))
    d['Description'] = descriptions.astype('string').str.strip().str.replace(r'\s+', ' ', regex=True)
    valid = d.Description.notna() & d.Description.ne('')
    votes = d.loc[valid].groupby(['StockCode', 'Description']).size().rename('count').reset_index()
    canonical = (votes.sort_values(['StockCode', 'count', 'Description'], ascending=[True, False, True])
                 .drop_duplicates('StockCode').set_index('StockCode').Description)
    d['Description'] = d.StockCode.map(canonical).fillna('')
    return d


def load_cleaned_uci():
    cache = Path(__file__).resolve().parent / '.data-cache'
    cache.mkdir(exist_ok=True)
    parquet = cache / 'cleaned.pkl'
    if parquet.exists():
        return clean_product_master(pd.read_pickle(parquet))
    archive = cache / 'online-retail-ii.zip'
    if not archive.exists() or archive.stat().st_size == 0:
        print('Downloading official UCI Online Retail II dataset…', flush=True)
        urlretrieve('https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip', archive)
    with ZipFile(archive) as z:
        with z.open('online_retail_II.xlsx') as f:
            sheets = pd.read_excel(f, sheet_name=None)
    df = pd.concat(sheets.values(), ignore_index=True).rename(columns={'Invoice':'InvoiceNo','Price':'UnitPrice','Customer ID':'CustomerID'})
    df['InvoiceDate'] = pd.to_datetime(df.InvoiceDate, errors='coerce')
    for col in ['Quantity','UnitPrice']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['StockCode','Quantity','UnitPrice','InvoiceDate'])
    df = df.loc[(df.Quantity>0)&(df.UnitPrice>0)&~df.InvoiceNo.astype(str).str.upper().str.startswith('C')].copy()
    df['Revenue'] = df.Quantity * df.UnitPrice
    # Keep duplicates and positive extremes, matching the requested cleaning rules.
    df.to_pickle(parquet)
    return clean_product_master(df)

if __name__ == '__main__':
    from export_dashboard import export_dashboard
    export_dashboard(load_cleaned_uci())
