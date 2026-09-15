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
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/projects/b2b-pricing-intelligence/',wait_until='networkidle',timeout=120000)
        page.wait_for_function("document.querySelector('#kpis').children.length === 5",timeout=120000)
        assert '20,972,594.57' in page.locator('#kpis').inner_text()
        page.wait_for_function("document.querySelector('#priceChart').classList.contains('js-plotly-plot')",timeout=30000)
        page.select_option('#segment','Strategic')
        assert page.locator('#segmentTable tbody tr').count()==1
        page.select_option('#recommendation','Review for Increase')
        page.select_option('#confidence','Medium')
        page.select_option('#scope','selected')
        page.select_option('#sort','asc')
        page.fill('#search','DOES-NOT-EXIST')
        assert 'No qualifying results' in page.locator('#opportunities').inner_text()
        page.fill('#search','')
        for key in ['segment','recommendation','confidence','scope']:
            page.select_option('#'+key,'')
        page.select_option('#sort','desc')
        assert page.locator('#opportunities tbody tr').count()==25
        page.click('#next')
        assert page.locator('#page').inner_text().startswith('2 /')
        page.click('#prev')
        model=page.evaluate("data.elasticity.find(r=>r.eligible).StockCode")
        page.select_option('#model',model)
        assert page.locator('#scenarioTable tbody tr').count()==5
        assert page.locator('#topTable tbody tr').count()>0
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
        for width,height in [(1440,1000),(390,844)]:
            page.set_viewport_size({'width':width,'height':height})
            page.wait_for_timeout(600)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            assert page.locator('#priceChart').bounding_box()['width']<width
        assert not errors,errors
        print('PASS: actual data, Plotly, filters, pagination, historical scenarios, commercial margin/warranty formulas and validation, isolated historical KPIs, desktop/mobile overflow and resize; no JavaScript errors.')
        browser.close()
finally:
    server.shutdown()
