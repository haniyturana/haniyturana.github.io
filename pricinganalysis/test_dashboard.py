"""Real browser smoke checks using a local static HTTP server and installed Edge."""
import functools
import http.server
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[]
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/projects/b2b-pricing-intelligence/',wait_until='networkidle',timeout=120000)
        page.wait_for_function("document.querySelector('#kpis').children.length === 5",timeout=120000)
        metadata=json.loads((root/'projects/b2b-pricing-intelligence/data/metadata.json').read_text())
        assert f"{metadata['identified_revenue']:,.2f}" in page.locator('#kpis').inner_text()
        assert 'Modelled' not in page.locator('#kpis').inner_text()
        assert page.locator('#confidence').count()==0
        assert page.evaluate("data.pricing_opportunities.every(r=>!['confidence','new_price','impact','beta'].some(k=>k in r))")
        assert page.locator('#opportunities th').all_text_contents()==['Customer','SKU','Description','Customer Segment','Orders','Quantity','Effective Price','Latest Price','SKU Median Price','Price Gap %','Volume Position','Pricing Review Status','Reason']
        page.wait_for_function("document.querySelector('#priceChart').classList.contains('js-plotly-plot')",timeout=30000)
        def check_product_charts():
            result=page.evaluate("""() => {
                const s=data.sku_pricing.find(r=>r.StockCode===$('sku').value);
                const rows=data.pricing_opportunities.filter(r=>r.StockCode===s.StockCode&&(!$('segment').value||r.segment===$('segment').value));
                const p=$('priceChart'),v=$('volumeChart');
                const below=rows.filter(r=>r.gap>=data.metadata.gap_threshold);
                return {
                    histogram:p.data.length===1&&p.data[0].type==='histogram'&&JSON.stringify(p.data[0].x)===JSON.stringify(rows.map(r=>r.price)),
                    axes:p.layout.xaxis.title.text==='Effective price (GBP)'&&p.layout.yaxis.title.text==='Number of customers',
                    priceLines:p.layout.shapes[0].x0===s.benchmark&&Math.abs(p.layout.shapes[1].x0-s.benchmark*.85)<1e-9&&p.layout.shapes[1].line.dash==='dash',
                    volumeLines:v.layout.shapes[0].y0===s.benchmark&&v.layout.shapes[1].x0===rows[0].sku_median_quantity,
                    uniform:typeof v.data[0].marker.size==='number',
                    hover:JSON.stringify(v.data[0].customdata)===JSON.stringify(rows.map(r=>[r.CustomerID,r.orders,r.gap*100,r.review_status])),
                    summary:$('priceInterpretation').textContent.includes(`${fmt(below.length)} customers (${(100*below.length/rows.length).toFixed(1)}%)`),
                    names:Array.from($('sku').options).every(o=>o.text===`${o.value} · ${data.sku_pricing.find(s=>s.StockCode===o.value).Description}`),
                    unique:new Set(Array.from($('sku').options,o=>o.value)).size===$('sku').options.length
                };
            }""")
            assert all(result.values()),result
        check_product_charts()
        assert page.locator('#skuStats th').all_text_contents()==['SKU','Canonical Description','Customers','Minimum','Median customer price','Maximum','Spread','Revenue']
        assert 'Benchmark' not in page.locator('#dispersion').inner_text()
        original_sku=page.locator('#sku').input_value()
        page.select_option('#sku',index=1)
        check_product_charts()
        page.select_option('#sku',original_sku)
        page.select_option('#segment','Strategic')
        check_product_charts()
        assert page.locator('#segmentTable tbody tr').count()==1
        page.select_option('#recommendation','Pricing Review')
        page.select_option('#scope','selected')
        page.select_option('#sort','asc')
        page.fill('#search','DOES-NOT-EXIST')
        assert 'No qualifying results' in page.locator('#opportunities').inner_text()
        page.fill('#search','')
        for key in ['segment','recommendation','scope']:
            page.select_option('#'+key,'')
        # Exercise exact-threshold, high/low-volume and empty-selection wording.
        interpretations=page.evaluate("""() => {
            const saved=data,sku=$('sku').value;
            const rows=[
                {StockCode:sku,CustomerID:'C1',quantity:10,orders:3,price:8.5,gap:.15,sku_median_quantity:20,review_status:'Pricing Review'},
                {StockCode:sku,CustomerID:'C2',quantity:20,orders:3,price:10,gap:0,sku_median_quantity:20,review_status:'Maintain / No Material Gap'},
                {StockCode:sku,CustomerID:'C3',quantity:30,orders:3,price:11,gap:-.1,sku_median_quantity:20,review_status:'Maintain / No Material Gap'}
            ];
            try {
                data={...saved,sku_pricing:[{StockCode:sku,Description:'Test',benchmark:10}],pricing_opportunities:rows};
                products();
                const low=$('volumeInterpretation').textContent,price=$('priceInterpretation').textContent;
                rows[0].quantity=30;rows[2].quantity=10;products();
                const high=$('volumeInterpretation').textContent;
                data.pricing_opportunities=[];products();
                const empty=$('priceInterpretation').textContent;
                rows[0].gap=0;rows[0].price=10;data.pricing_opportunities=rows;products();
                return {low,price,high,empty,none:$('volumeInterpretation').textContent};
            } finally {data=saved;products();}
        }""")
        assert '1 customers (33.3%)' in interpretations['price']
        assert '1 of 1' in interpretations['low'] and 'at or below' in interpretations['low']
        assert '1 of 1' in interpretations['high'] and 'above the median' in interpretations['high']
        assert interpretations['empty']=='No customers match this SKU and segment selection.'
        assert interpretations['none'].startswith('No displayed customers pay at least 15%')
        for status in ['Pricing Review','Possible Volume Justification']:
            page.select_option('#recommendation',status)
            assert page.locator('#opportunities tbody tr').count()>0
            assert all(s==status for s in page.locator('#opportunities tbody td:nth-child(12)').all_text_contents())
        assert page.evaluate("data.pricing_opportunities.filter(r=>r.review_status==='Pricing Review').every(r=>r.eligible&&r.orders>=3&&r.gap>=data.metadata.gap_threshold&&r.quantity<=r.sku_median_quantity)")
        assert page.evaluate("data.pricing_opportunities.filter(r=>r.review_status==='Possible Volume Justification').every(r=>r.eligible&&r.orders>=3&&r.gap>=data.metadata.gap_threshold&&r.quantity>r.sku_median_quantity)")
        page.select_option('#recommendation','')
        page.select_option('#sort','desc')
        assert page.locator('#opportunities tbody tr').count()==25
        gaps=[float(s.replace('%','').replace(',','')) for s in page.locator('#opportunities tbody td:nth-child(10)').all_text_contents()]
        assert gaps==sorted(gaps,reverse=True)
        page.select_option('#sort','asc')
        gaps=[float(s.replace('%','').replace(',','')) for s in page.locator('#opportunities tbody td:nth-child(10)').all_text_contents()]
        assert gaps==sorted(gaps)
        page.select_option('#sort','desc')
        page.click('#next')
        assert page.locator('#page').inner_text().startswith('2 /')
        page.click('#prev')
        model=page.evaluate("data.elasticity.find(r=>r.eligible).StockCode")
        page.select_option('#model',model)
        assert page.locator('#scenarioTable tbody tr').count()==5
        assert page.locator('#topTable').count()==0
        review_table=page.locator('#opportunities').inner_html()
        page.evaluate("window.savedModels=data.elasticity;data.elasticity=[];matrix();data.elasticity=window.savedModels;delete window.savedModels")
        assert page.locator('#opportunities').inner_html()==review_table
        assert page.evaluate("Array.from(document.querySelector('#model').options).every(o=>data.elasticity.find(r=>r.StockCode===o.value).eligible)")
        before=page.locator('#kpis').inner_text()
        assert page.locator('#commercial-kpis').inner_text()==''
        for key,value in {'cost':'100','months':'24','claimRate':'5','claimCost':'40','service':'8','target':'40','current':'150','benchmark':'200'}.items():
            page.fill('#commercial-'+key,value)
        assert 'Confirm' in page.locator('#commercial-status').inner_text()
        page.check('#commercial-confirm')
        result=page.evaluate("calculateCommercialScenario({cost:100,months:24,claimRate:5,claimCost:40,service:8,target:40,current:150,benchmark:200,confirmed:true})")
        assert result['warranty']==2 and result['serve']==110
        assert abs(result['required']-183.3333333333)<1e-6
        assert abs(result['margin']-40/150)<1e-6
        assert 'does not meet' in page.locator('#commercial-decision').inner_text()
        assert '£183.33' in page.locator('#commercial-kpis').inner_text()
        page.fill('#commercial-months','36')
        assert not page.is_checked('#commercial-confirm')
        page.check('#commercial-confirm')
        assert '£183.33' in page.locator('#commercial-kpis').inner_text()
        page.fill('#commercial-current','200')
        assert 'Current price meets' in page.locator('#commercial-decision').inner_text()
        page.fill('#commercial-target','100')
        assert 'below 100%' in page.locator('#commercial-status').inner_text()
        page.fill('#commercial-target','40')
        page.fill('#commercial-current','0')
        assert 'must be positive' in page.locator('#commercial-status').inner_text()
        page.fill('#commercial-current','')
        page.fill('#commercial-benchmark','')
        assert 'Enter an optional' in page.locator('#commercial-decision').inner_text()
        assert page.locator('#kpis').inner_text()==before
        for width,height in [(1440,1000),(390,844),(320,740)]:
            page.set_viewport_size({'width':width,'height':height})
            page.wait_for_timeout(600)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert page.locator('#priceChart').bounding_box()['width']<width
            assert page.locator('#volumeChart').bounding_box()['width']<width
            assert page.locator('#sku').bounding_box()['x']+page.locator('#sku').bounding_box()['width']<=width
            assert page.evaluate("$('priceChart')._fullLayout._size.w>100&&$('volumeChart')._fullLayout._size.w>100")
        page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='networkidle')
        cards=page.locator('.intelligence-grid > .project-card')
        assert cards.count()==2
        assert cards.nth(0).locator('h3').inner_text()=='Jewellery Retail Performance & Campaign Intelligence'
        assert cards.nth(1).locator('h3').inner_text()=='B2B Pricing Intelligence'
        assert page.evaluate("Array.from(document.querySelectorAll('.intelligence-grid>.project-card')).map(c=>Array.from(c.children).map(e=>e.tagName).join(',')).every((s,i,a)=>s===a[0])")
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width,'height':1000})
            cards.first.scroll_into_view_if_needed()
            page.mouse.move(0,0)
            page.wait_for_timeout(400)
            a,b=cards.nth(0).bounding_box(),cards.nth(1).bounding_box()
            assert abs(a['width']-b['width'])<1
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            if width>760:
                assert abs(a['y']-b['y'])<1 and b['x']>a['x']
                assert abs(a['height']-b['height'])<1
                for selector in ['h3','p:not(.case-type)','.tags','dl div:nth-child(1)','dl div:nth-child(2)','dl div:nth-child(3)','.project-link']:
                    assert abs(cards.nth(0).locator(selector).bounding_box()['y']-cards.nth(1).locator(selector).bounding_box()['y'])<1,selector
            else:
                assert abs(a['x']-b['x'])<1 and b['y']>=a['y']+a['height']
        assert not errors,errors
        print('PASS: identified revenue, diagnostic classifications, filters, pagination, independent exploratory models, preserved commercial simulator, desktop/mobile dashboard and aligned paired portfolio cards; no JavaScript errors.')
        browser.close()
finally:
    server.shutdown()
