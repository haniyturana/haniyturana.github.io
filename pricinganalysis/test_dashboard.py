"""Real browser smoke checks using a local static HTTP server and installed Edge."""
import functools
import http.server
import json
import os
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
        if os.environ.get('PLOTLY_TEST_JS'):
            page.route('https://cdn.plot.ly/plotly-2.35.2.min.js',lambda route:route.fulfill(path=os.environ['PLOTLY_TEST_JS'],content_type='application/javascript'))
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/projects/b2b-pricing-intelligence/',wait_until='networkidle',timeout=120000)
        page.wait_for_function("document.querySelector('#kpis').children.length === 5",timeout=120000)
        metadata=json.loads((root/'projects/b2b-pricing-intelligence/data/metadata.json').read_text())
        assert f"{metadata['identified_revenue']:,.2f}" in page.locator('#kpis').inner_text()
        assert 'Modelled' not in page.locator('#kpis').inner_text()
        assert page.locator('#confidence').count()==0
        assert page.evaluate("data.pricing_opportunities.every(r=>!['confidence','new_price','impact','beta'].some(k=>k in r))")
        assert page.locator('#opportunities th').all_text_contents()==['Customer','SKU','Description','Orders','Quantity','Effective Price','SKU Median Price','Price Gap %','Volume Position','Pricing Review Status']
        assert page.locator('#sort').input_value()=='priority'
        assert page.evaluate("Array.from(document.querySelectorAll('.review-row')).every(r=>r.cells[9].textContent==='Pricing Review')")
        assert page.locator('#review-summary strong').all_text_contents()==['72','2,428','52,376','426,112']
        first_page=page.locator('#opportunities').inner_html()
        page.click('#next')
        assert page.locator('#page').inner_text().startswith('2 /')
        assert page.locator('#opportunities').inner_html()!=first_page
        page.click('#prev')
        assert page.locator('#opportunities').inner_html()==first_page
        # Exercise status boundaries and gap ordering across the entire result set.
        assert page.evaluate("""() => {
            const original=data.pricing_opportunities;
            const sample=reviewStatuses.flatMap(status=>original.filter(r=>r.review_status===status).slice(0,3)).reverse();
            data.pricing_opportunities=sample;matrix();
            const actual=Array.from(document.querySelectorAll('.review-row'),r=>[r.cells[0].textContent,r.cells[1].textContent]);
            const expected=[...sample].sort((a,b)=>reviewStatuses.indexOf(a.review_status)-reviewStatuses.indexOf(b.review_status)||b.gap-a.gap||a.CustomerID.localeCompare(b.CustomerID)||a.StockCode.localeCompare(b.StockCode)).map(r=>[r.CustomerID,r.StockCode]);
            data.pricing_opportunities=original;matrix();
            return JSON.stringify(actual)===JSON.stringify(expected);
        }""")
        page.fill('#search','C01315 84927E')
        assert page.locator('.review-row').count()==1
        assert page.locator('#review-summary strong').all_text_contents()==['0','0','0','1']
        detail=page.locator('.review-detail details')
        assert not detail.evaluate('(e)=>e.open')
        detail.locator('summary').focus()
        page.keyboard.press('Enter')
        assert detail.evaluate('(e)=>e.open')
        assert detail.locator('dd').all_text_contents()[:2]==['Large','£0.08']
        for width in [1440,768,390,320]:
            page.set_viewport_size({'width':width,'height':1000})
            page.wait_for_function("document.documentElement.scrollWidth<=innerWidth+1")
            assert page.locator('#opportunities').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
        detail.locator('summary').click()
        assert not detail.evaluate('(e)=>e.open')
        page.fill('#search','')
        for width in [1440,768,390,320]:
            page.set_viewport_size({'width':width,'height':1000})
            assert page.locator('#opportunities').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
        page.set_viewport_size({'width':1440,'height':1000})
        print('PASS pricing priority, filtered counts, keyboard details, pagination and responsive review table',flush=True)
        page.wait_for_function("document.querySelector('#priceChart').classList.contains('js-plotly-plot')",timeout=30000)
        def check_product_charts():
            result=page.evaluate("""() => {
                const s=data.sku_pricing.find(r=>r.StockCode===$('sku').value);
                const rows=data.pricing_opportunities.filter(r=>r.StockCode===s.StockCode&&(!$('segment').value||r.segment===$('segment').value));
                const p=$('priceChart'),v=$('volumeChart');
                const below=rows.filter(r=>r.gap>=data.metadata.gap_threshold);
                return {
                    bands:p.data.length===1&&p.data[0].type==='bar'&&p.data[0].y.reduce((a,b)=>a+b,0)===rows.length,
                    axes:p.layout.xaxis.title.text==='Price position'&&p.layout.yaxis.title.text==='Number of customers',
                    logScale:v.layout.xaxis.type==='log',
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
        assert page.locator('#skuStats th').all_text_contents()==['SKU','Canonical Description','Customers','Minimum','Median Customer Price','Maximum','Spread','Revenue']
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
            assert page.locator('#opportunities .review-row').count()>0
            assert all(s==status for s in page.locator('#opportunities .review-row td:nth-child(10)').all_text_contents())
        assert page.evaluate("data.pricing_opportunities.filter(r=>r.review_status==='Pricing Review').every(r=>r.eligible&&r.orders>=3&&r.gap>=data.metadata.gap_threshold&&r.quantity<=r.sku_median_quantity)")
        assert page.evaluate("data.pricing_opportunities.filter(r=>r.review_status==='Possible Volume Justification').every(r=>r.eligible&&r.orders>=3&&r.gap>=data.metadata.gap_threshold&&r.quantity>r.sku_median_quantity)")
        page.select_option('#recommendation','')
        page.select_option('#sort','desc')
        assert page.locator('#opportunities .review-row').count()==25
        gaps=[float(s.replace('%','').replace(',','')) for s in page.locator('#opportunities .review-row td:nth-child(8)').all_text_contents()]
        assert gaps==sorted(gaps,reverse=True)
        page.select_option('#sort','asc')
        gaps=[float(s.replace('%','').replace(',','')) for s in page.locator('#opportunities .review-row td:nth-child(8)').all_text_contents()]
        assert gaps==sorted(gaps)
        page.select_option('#sort','desc')
        page.click('#next')
        assert page.locator('#page').inner_text().startswith('2 /')
        page.click('#prev')
        model=page.evaluate("data.elasticity.find(r=>r.eligible).StockCode")
        page.select_option('#sku',model)
        assert page.locator('#scenarioTable tbody tr').count()==5
        assert page.locator('#scenarioTable tr.suggested-row').count()==1
        assert page.evaluate("$('scenarioChart').layout.xaxis.type==='category'")
        assert page.locator('#topTable').count()==0
        review_table=page.locator('#opportunities').inner_html()
        page.evaluate("window.savedModels=data.elasticity;data.elasticity=[];matrix();data.elasticity=window.savedModels;delete window.savedModels")
        assert page.locator('#opportunities').inner_html()==review_table
        assert page.evaluate("priceSuggestion!==null")
        # Deterministic selection, ties, missing scenarios and ineligible evidence.
        assert page.evaluate("""() => {
            const rows=testedChanges.map(change=>({change,price:10*(1+change),quantity:10,revenue:100}));
            if(selectPriceSuggestion({eligible:true},rows).suggested.change!==0)return false;
            for(const winner of testedChanges){
                const test=rows.map(r=>({...r,revenue:r.change===winner?200:100}));
                if(selectPriceSuggestion({eligible:true},test).suggested.change!==winner)return false;
            }
            return selectPriceSuggestion({eligible:false},rows)===null&&selectPriceSuggestion(null,rows)===null&&selectPriceSuggestion({eligible:true},rows.slice(1))===null;
        }""")
        assert page.evaluate("priceBands([-0.1,0,0.0001,.049999,.05,.149999,.15,.8].map(gap=>({gap}))).map(b=>b.count)")==[2,2,2,2]
        assert page.evaluate("priceBands([]).every(b=>b.count===0&&b.percent===0)")
        assert not page.locator('#modelStats').is_visible()
        assert all(word not in page.locator('#elasticity').inner_text() for word in ['Coefficient','p-value','R²','regression'])
        page.locator('#method details').first.locator('summary').click()
        assert page.locator('#modelStats').is_visible()
        assert 'Coefficient' in page.locator('#modelStats').inner_text()
        page.locator('#method details').first.locator('summary').click()
        # Real click on a Plotly bar, then toggle the same bar off.
        bar=page.locator('#segmentChart .trace.bars .point path').first
        bar.click(force=True)
        assert page.locator('#segment').input_value()=='Small'
        check_product_charts()
        bar.click(force=True)
        assert page.locator('#segment').input_value()==''
        assert page.evaluate("$('segmentChart').data[0].customdata.every(r=>r.length===3)")
        # An ineligible SKU stays selectable but cannot send a suggested price.
        weak=page.evaluate("data.sku_pricing.find(s=>s.eligible&&!data.elasticity.some(m=>m.StockCode===s.StockCode&&m.eligible)).StockCode")
        page.select_option('#sku',weak)
        assert page.locator('#suggestion-state').inner_text()=='Insufficient historical evidence for price suggestion'
        assert page.locator('#test-suggested').is_disabled()
        page.select_option('#sku',model)
        expected=page.evaluate('priceSuggestion')
        page.click('#test-suggested')
        assert float(page.locator('#commercial-proposed').input_value())==expected['suggested']['price']
        assert float(page.locator('#commercial-current').input_value())==expected['baseline']['price']
        assert 'Enter cost assumptions to evaluate profitability.' in page.locator('#comparison-status').inner_text()
        assert page.locator('#commercial-cost').input_value()==''
        assert page.evaluate("""() => {
            const context={rows:[{price:10,quantity:100},{price:11,quantity:90}]};
            const r=commercialComparison(context,10,11,6);
            const manual=commercialComparison(context,10,12,6);
            return r.current.revenue===1000&&r.proposed.revenue===990&&r.current.profit===400&&r.proposed.profit===450&&r.current.margin===.4&&Math.abs(r.proposed.margin-5/11)<1e-12&&manual.proposed.demand===null&&manual.proposed.profit===null;
        }""")
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
        for width,height in [(1440,1000),(768,1024),(390,844)]:
            page.set_viewport_size({'width':width,'height':height})
            page.wait_for_timeout(600)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert page.locator('#priceChart').bounding_box()['width']<width
            assert page.locator('#volumeChart').bounding_box()['width']<width
            assert page.locator('#sku').bounding_box()['x']+page.locator('#sku').bounding_box()['width']<=width
            assert page.evaluate("$('priceChart')._fullLayout._size.w>100&&$('volumeChart')._fullLayout._size.w>100")
            for chart_id in ['segmentChart','priceChart','volumeChart','scenarioChart','commercial-waterfall']:
                assert page.locator('#'+chart_id).bounding_box()['width']<width
            page.evaluate("Plotly.Fx.hover('scenarioChart',[{curveNumber:0,pointNumber:0}])")
            hover=page.locator('#scenarioChart .hoverlayer').text_content()
            assert all(label in hover for label in ['Price:', 'Model-implied demand:', 'Model-implied revenue:', 'Revenue change:'])
            page.evaluate("Plotly.Fx.unhover('scenarioChart')")
            page.select_option('#segment','Medium')
            check_product_charts()
            page.select_option('#segment','')
            assert page.evaluate("Array.from(document.querySelectorAll('.table-wrap')).every(e=>e.getBoundingClientRect().right<=innerWidth+1&&getComputedStyle(e).overflowX==='auto')")
            if os.environ.get('PRICING_SCREENSHOTS'):
                page.screenshot(path=str(Path(os.environ['PRICING_SCREENSHOTS'])/f'pricing-{width}.png'),full_page=True)
                page.locator('#elasticity').screenshot(path=str(Path(os.environ['PRICING_SCREENSHOTS'])/f'opportunity-{width}.png'))
            print(f'PASS responsive {width}x{height}: charts, filters, contained scrollable tables, no page overflow',flush=True)
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
