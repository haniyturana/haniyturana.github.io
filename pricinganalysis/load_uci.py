"""Reproducible official UCI source, cached locally and excluded from publication."""
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile
import pandas as pd

def load_cleaned_uci():
    cache = Path(__file__).resolve().parent / '.data-cache'
    cache.mkdir(exist_ok=True)
    parquet = cache / 'cleaned.pkl'
    if parquet.exists():
        return pd.read_pickle(parquet)
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
    return df

if __name__ == '__main__':
    from export_dashboard import export_dashboard
    export_dashboard(load_cleaned_uci())
