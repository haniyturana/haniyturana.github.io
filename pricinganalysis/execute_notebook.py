"""Execute this plain-Python notebook, retaining tables and charts without a kernel service."""
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import IPython.display
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
os.chdir(root)
p=root/'pricinganalysis_ucimlrepo.ipynb'
n=json.loads(p.read_text(encoding='utf-8'))
# Do not embed original customer identifiers in publishable notebook outputs.
for cell in n['cells']:
    if cell['cell_type']=='code':
        s=''.join(cell['source'])
        s=s.replace('from export_dashboard import export_dashboard, DEFAULT_OUTPUT','from export_dashboard import export_dashboard, DEFAULT_OUTPUT, unpack_records')
        s=s.replace("pd.DataFrame(json.loads((DEFAULT_OUTPUT / f'{name}.json').read_text(encoding='utf-8')))", "pd.DataFrame(unpack_records(json.loads((DEFAULT_OUTPUT / f'{name}.json').read_text(encoding='utf-8'))))")
        s=s.replace("display(df.describe(include='all').T)","display(df[['Quantity', 'UnitPrice', 'Revenue']].describe().T)")
        s=s.replace("display(df.nlargest(10, 'Quantity'))", "display(df.nlargest(10, 'Quantity')[['StockCode','Quantity','UnitPrice','Revenue']])")
        s=s.replace("display(df.nlargest(10, price_column))", "display(df.nlargest(10, price_column)[['StockCode','Quantity',price_column,'Revenue']])")
        cell['source']=s.splitlines(True)
namespace={'__name__':'__main__'}
count=0
for cell in n['cells']:
    if cell['cell_type']!='code': continue
    count+=1
    outputs=[]
    def display(*objects,**kwargs):
        for obj in objects:
            data={'text/plain':repr(obj)}
            if hasattr(obj,'_repr_html_'): data['text/html']=obj._repr_html_()
            outputs.append(dict(output_type='display_data',metadata={},data=data))
    def show(*args,**kwargs):
        for number in plt.get_fignums():
            fig=plt.figure(number); buf=io.BytesIO(); fig.savefig(buf,format='png',bbox_inches='tight')
            outputs.append(dict(output_type='display_data',metadata={},data={'image/png':base64.b64encode(buf.getvalue()).decode()}))
        plt.close('all')
    IPython.display.display=display
    plt.show=show
    stdout=io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exec(compile(''.join(cell['source']),f'notebook-cell-{count}','exec'),namespace)
    if stdout.getvalue():outputs.insert(0,dict(output_type='stream',name='stdout',text=stdout.getvalue()))
    cell['outputs']=outputs;cell['execution_count']=count
    print(f'Executed cell {count}',flush=True)
p.write_text(json.dumps(n,indent=1),encoding='utf-8')
print('Notebook executed and saved successfully.')
