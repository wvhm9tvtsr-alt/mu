"""Petty cash itemization, legacy amounts and settlement snapshots."""
from playwright.sync_api import sync_playwright, expect
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844});page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/',wait_until='networkidle')
 page.locator('#tabs button').get_by_text('結帳紀錄',exact=True).click()
 page.locator('#checkoutAdd-petty').click();page.locator('#checkoutForm [name=amount]').fill('1000')
 def add(item,amount):
  page.locator('#checkoutPendingAdd').click();row=page.locator('#checkoutPendingItems > div').last
  row.locator('[data-pending-item]').fill(item);row.locator('[data-pending-amount]').fill(amount)
 add('文具','20.15');add('車資','30.25')
 expect(page.locator('#checkoutPendingTotal')).to_have_text('未回帳 total：50.4 元')
 page.locator('#checkoutForm button.primary').click()
 expect(page.locator('#checkoutRows-petty')).to_contain_text('文具／20.15 元')
 expect(page.locator('#checkoutTotal-petty')).to_contain_text('50.4 元')
 page.locator('#checkoutRows-petty button').get_by_text('編輯',exact=True).click()
 page.locator('#checkoutPendingItems > div').first.locator('button').click()
 expect(page.locator('#checkoutPendingTotal')).to_have_text('未回帳 total：30.25 元')
 page.locator('#checkoutForm button.primary').click()
 assert page.evaluate('checkoutData.records[0].pending')==3025
 page.locator('#checkoutSettle').click()
 expect(page.locator('#checkoutStatus')).to_contain_text('結算已儲存')
 page.reload(wait_until='networkidle');page.locator('#tabs button').get_by_text('結帳紀錄',exact=True).click()
 page.locator('#checkoutHistoryView').click()
 page.locator('#checkoutSettlementSelect').select_option(index=1)
 expect(page.locator('#checkoutRows-petty')).to_contain_text('車資／30.25 元')
 assert page.evaluate('cloudSnapshotValid(cloudSnapshot())')
 # Legacy batches retain their original stored object; item labels are display-only.
 page.evaluate("()=>{const r={id:'legacy',kind:'petty',date:'2026-11-02',amount:10000,pending:2500,archived:false,updatedAt:new Date().toISOString()};checkoutData={version:1,records:[r],history:[],settlements:[{id:'batch-old',date:r.date,at:r.updatedAt,records:[structuredClone(r)]}]};checkoutSettlementView='batch-old';checkoutRender()}")
 before=page.evaluate('JSON.stringify(checkoutData)')
 expect(page.locator('#checkoutRows-petty')).to_contain_text('舊資料（未填品項）／25 元')
 assert page.evaluate('checkoutValid(checkoutData)')
 assert page.evaluate('JSON.stringify(checkoutData)')==before
 # Editing legacy current records preserves old amount and permits a real description.
 page.evaluate("()=>{checkoutData.settlements=[];checkoutSettlementView=null;checkoutHistoryView=false;checkoutRender()}")
 page.locator('#checkoutRows-petty button').get_by_text('編輯',exact=True).click()
 expect(page.locator('[data-pending-amount]')).to_have_value('25')
 page.locator('[data-pending-item]').fill('補填品項');page.locator('#checkoutForm button.primary').click()
 assert page.evaluate('checkoutData.records[0].pendingItems[0].item')=='補填品項'
 assert page.evaluate('checkoutData.records[0].pending')==2500
 assert not errors,errors
 print('PASS: multiple petty cash items, exact total, edit/removal, settlement/reload, legacy snapshot unchanged and legacy edit compatibility')
 b.close()
