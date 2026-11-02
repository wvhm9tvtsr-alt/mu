"""Atomic four-section settlement, browser-isolated data only."""
from playwright.sync_api import sync_playwright, expect
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844});page=c.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/',wait_until='networkidle')
 page.locator('#tabs button').get_by_text('結帳紀錄',exact=True).click()
 others=page.evaluate('cloudSnapshot()')
 def fill(kind,values,save=True):
  page.locator('#checkoutAdd-'+kind).click();f=page.locator('#checkoutForm')
  for k,v in values.items():
   el=f.locator('[name='+k+']')
   if k=='status':el.select_option(v)
   else:el.fill(v)
  if save:f.locator('button.primary').click()
 fill('ledger',{'date':'2026-11-02','cash':'100.10','transfer':'200.20','card':'300.30','reviewer':'核對員'},False)
 page.locator('#checkoutPersonAdd-unpaid').click()
 page.locator('#checkoutPeople-unpaid [data-person-name]').fill('測試客人')
 page.locator('#checkoutPeople-unpaid [data-person-amount]').fill('50.55')
 page.locator('#checkoutForm button.primary').click()
 fill('deposit',{'amount':'80.15'})
 fill('claim',{'item':'耗材','amount':'30.35'})
 # The final open form is included without needing a separate Save action.
 fill('petty',{'amount':'1000','pending':'125.55'},False)
 page.evaluate("()=>{window.writeCount=0;window.oldSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===CHECKOUT_KEY)window.writeCount++;return window.oldSet.call(this,k,v)}}")
 page.locator('#checkoutSettle').click()
 expect(page.locator('#checkoutStatus')).to_contain_text('結算已儲存，共 4 筆')
 assert page.evaluate('window.writeCount')==1
 assert page.evaluate('checkoutData.settlements.length')==1
 assert page.evaluate('checkoutData.settlements[0].records.length')==4
 expect(page.locator('#checkoutTotal-ledger')).to_contain_text('600.6 元')
 expect(page.locator('#checkoutRows-ledger')).to_contain_text('測試客人／50.55 元')
 expect(page.locator('#checkoutTotal-petty')).to_contain_text('125.55 元')
 assert page.locator('#checkoutRows-ledger button').count()==0
 expect(page.locator('#checkoutSettleControls')).to_be_hidden()
 snapshot=page.evaluate('JSON.stringify(checkoutData.settlements[0])')
 page.reload(wait_until='networkidle');page.locator('#tabs button').get_by_text('結帳紀錄',exact=True).click()
 expect(page.locator('#checkoutRows-ledger tr')).to_have_count(0)
 page.locator('#checkoutSettlementSelect').select_option(index=1)
 expect(page.locator('#checkoutRows-ledger')).to_contain_text('核對員')
 assert page.evaluate('JSON.stringify(checkoutData.settlements[0])')==snapshot
 # Empty settlement does not produce duplicates.
 page.locator('#checkoutCurrentView').click();page.locator('#checkoutSettle').click()
 expect(page.locator('#checkoutStatus')).to_contain_text('本次尚無紀錄')
 assert page.evaluate('checkoutData.settlements.length')==1
 # Failure keeps the form, staged records, and saved settlements intact.
 fill('claim',{'item':'本次','amount':'15.25'},False)
 original=page.evaluate('JSON.stringify(checkoutData)')
 page.evaluate("()=>{window.oldSet=Storage.prototype.setItem;Storage.prototype.setItem=()=>{throw Error('儲存空間不足')}}")
 page.locator('#checkoutSettle').click()
 expect(page.locator('#checkoutStatus')).to_contain_text('尚未完成結算')
 expect(page.locator('#checkoutForm')).to_be_visible()
 assert page.evaluate('JSON.stringify(checkoutData)')==original
 page.evaluate('()=>{Storage.prototype.setItem=window.oldSet}')
 page.locator('#checkoutSettle').click()
 expect(page.locator('#checkoutStatus')).to_contain_text('結算已儲存，共 1 筆')
 assert page.evaluate('checkoutData.settlements.length')==2
 assert page.evaluate('JSON.stringify(checkoutData.settlements[0])')==snapshot
 # A legacy v1 payload remains readable; backup and sync preserve batches.
 assert page.evaluate('checkoutValid({version:1,records:[],history:[]})')
 assert page.evaluate('cloudSnapshotValid(cloudSnapshot())')
 assert page.evaluate('()=>{const p=cloudSnapshot();delete p.data[CHECKOUT_KEY];return cloudUpgradeSnapshot(p).data[CHECKOUT_KEY]===JSON.stringify(checkoutData)}')
 # Force a backup round trip, then render the previously saved batch.
 assert page.evaluate('async()=>{const p=cloudSnapshot();await cloudApply(p,cloudEpoch);return checkoutData.settlements.length}')==2
 current=page.evaluate('cloudSnapshot()')
 for k,v in others['data'].items():
  if k!='mu-checkout-v1':assert current['data'][k]==v,k
 assert not errors,errors
 print('PASS: one-click atomic four-section save, unsaved form inclusion, snapshot totals, reload/history, duplicate prevention, failed write recovery, old format, backup round trip, other ledgers unchanged')
 b.close()
