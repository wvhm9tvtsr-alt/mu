"""Run against a local HTTP server: python3 tests/stored-value-smoke.py [base URL]."""
from playwright.sync_api import sync_playwright, expect
import json, sys
BASE=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000/'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844})
    page=context.new_page(); errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE,wait_until='networkidle')
    # Keep all existing module payloads byte-for-byte across ledger operations.
    before=page.evaluate('cloudSnapshot()')
    page.locator('#tabs button').get_by_text('客人儲值',exact=True).click()
    page.locator('#storedNew').click()
    form=page.locator('#storedProfile')
    for name,value in {'birthday':'1990-02-28','name':'測試客人 <b>','level':'VIP 自訂'}.items():
        form.locator(f'[name={name}]').fill(value)
    form.locator('button.primary').click()
    assert page.locator('#storedName').inner_text()=='測試客人 <b>'
    assert page.locator('#storedName b').count()==0
    def transact(kind, **fields):
        f=page.locator('#storedTransaction')
        page.locator('#storedDeduct' if kind=='debit' else '#storedTopup').click()
        expect(page.locator('#storedTransactionTitle')).to_have_text('扣儲值金' if kind=='debit' else '儲值／贈送')
        expect(f.locator('[name=amount]')).to_be_visible() if kind=='debit' else expect(f.locator('[name=paid]')).to_be_visible()
        f.locator('[name=date]').fill('2026-10-23')
        for k,v in fields.items(): f.locator(f'[name={k}]').fill(str(v))
        f.locator('button.primary').click()
    transact('topup',paid='1000.10',gift='200.20',note='首儲')
    expect(page.locator('#storedSummary')).to_have_text('累計儲值：1,000.1 元｜剩餘金額：1,200.3 元')
    transact('topup',paid='0',gift='50')
    expect(page.locator('#storedSummary')).to_have_text('累計儲值：1,000.1 元｜剩餘金額：1,250.3 元')
    transact('debit',amount='250.30',note='測試扣款')
    assert page.evaluate('storedTotals(storedData,storedSelected).balance')==100000
    saved=page.evaluate('localStorage.getItem(STORED_KEY)')
    transact('debit',amount='1000.01')
    expect(page.locator('#storedStatus')).to_contain_text('餘額不足')
    assert page.evaluate('localStorage.getItem(STORED_KEY)')==saved
    transact('debit',amount='1000')
    assert page.evaluate('storedTotals(storedData,storedSelected).balance')==0
    transact('debit',amount='0.01')
    expect(page.locator('#storedStatus')).to_contain_text('餘額不足')
    page.once('dialog',lambda d:d.accept())
    page.locator('#storedHistory button').first.click()
    assert page.evaluate('storedTotals(storedData,storedSelected).balance')==100000
    assert page.locator('#storedHistory button').count()==1
    assert page.locator('#storedHistory').inner_text().count('已撤銷')==1
    assert page.evaluate("(()=>{const d=structuredClone(storedData),r=d.events.find(e=>e.kind==='reversal'); d.events.push({...r,id:'duplicate'});return storedValid(d)})()") is False
    # Profile updates keep balances and audit before/after values.
    page.locator('#storedEdit').click()
    assert form.locator('[name=birthday]').input_value()=='1990-02-28'
    assert form.locator('[name=birthday]').get_attribute('type')=='text'
    form.locator('[name=birthday]').fill('5/20')
    form.locator('[name=level]').fill('白金')
    form.locator('button.primary').click()
    assert page.evaluate('storedData.events.at(-1).previous.level')=='VIP 自訂'
    assert page.evaluate('storedData.customers[0].birthday')=='5/20'
    assert page.evaluate('storedTotals(storedData,storedSelected).balance')==100000
    # A failed storage write must not mutate in-memory or persisted balances.
    saved=page.evaluate('localStorage.getItem(STORED_KEY)')
    page.evaluate("() => {window.testSet=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new DOMException('quota','QuotaExceededError')};}")
    transact('topup',paid='25',gift='0')
    expect(page.locator('#storedStatus')).to_contain_text('儲存失敗')
    assert page.evaluate('JSON.stringify(storedData)')==saved
    page.evaluate('() => {Storage.prototype.setItem=window.testSet;}')
    # Restore clean state after intentionally rejected draft.
    page.reload(wait_until='networkidle')
    page.locator('#tabs button').get_by_text('客人儲值',exact=True).click()
    page.locator('#storedCustomers button').first.click()
    assert page.evaluate('storedTotals(storedData,storedSelected).balance')==100000
    assert page.evaluate('cloudHasDrafts()') is False
    assert page.evaluate('storedData.customers[0].birthday')=='5/20'
    current=page.evaluate('cloudSnapshot()')
    for key,value in before['data'].items():
        if key!='mu-stored-value-v1': assert current['data'][key]==value,key
    assert page.evaluate('cloudSnapshotValid(cloudSnapshot())') is True
    assert page.evaluate("(()=>{const p=cloudSnapshot();delete p.data[STORED_KEY];const q=cloudUpgradeSnapshot(p);return cloudSnapshotValid(q)&&JSON.parse(q.data[STORED_KEY]).events.length===0})()") is True
    assert page.evaluate("(()=>{const p=cloudSnapshot();delete p.data[STORED_KEY];return cloudUpgradeSnapshot(p,storedData).data[STORED_KEY]===JSON.stringify(storedData)})()") is True
    # Full backup includes the ledger and is readable after reload.
    page.locator('#cloudArea > summary').click()
    page.locator('#cloudArea details summary').get_by_text('完整備份與同步前備份',exact=True).click()
    with page.expect_download() as download: page.locator('#cloudExport').click()
    backup=json.loads(open(download.value.path()).read())
    assert json.loads(backup['payload']['data']['mu-stored-value-v1'])['events'][-1]['profile']['level']=='白金'
    # Both current and pre-ledger full backups restore without losing stored value.
    for legacy in [False, True]:
        restored=json.loads(json.dumps(backup))
        if legacy: del restored['payload']['data']['mu-stored-value-v1']
        page.once('dialog',lambda d:d.accept())
        page.locator('#cloudRestoreFile').set_input_files({'name':'backup.json','mimeType':'application/json','buffer':json.dumps(restored).encode()})
        expect(page.locator('#cloudStatus')).to_contain_text('完整備份已還原')
        assert page.evaluate('storedTotals(storedData,storedData.customers[0].id).balance')==100000
    assert page.evaluate("async () => {const a=cloudSnapshot(), b=structuredClone(a), hashes=await cloudHashes(a);const d=JSON.parse(b.data[STORED_KEY]);d.customers[0].level='remote';b.data[STORED_KEY]=JSON.stringify(d);const result=await cloudMerge(a,b,hashes);return result.conflicts.length===0&&JSON.parse(result.payload.data[STORED_KEY]).customers[0].level==='remote'}") is True
    # An outdated browser tab cannot overwrite a newer balance.
    stale=context.new_page(); stale.goto(BASE,wait_until='networkidle')
    stale.locator('#tabs button').get_by_text('客人儲值',exact=True).click()
    stale.locator('#storedCustomers button').first.click()
    page.locator('#storedCustomers button').first.click()
    transact('topup',paid='1',gift='0')
    fresh=page.evaluate('localStorage.getItem(STORED_KEY)')
    sf=stale.locator('#storedTransaction'); stale.locator('#storedDeduct').click()
    sf.locator('[name=date]').fill('2026-10-23'); sf.locator('[name=amount]').fill('1')
    sf.locator('button.primary').click()
    expect(stale.locator('#storedStatus')).to_contain_text('儲存失敗')
    assert page.evaluate('localStorage.getItem(STORED_KEY)')==fresh
    stale.close()
    # Corrupt ledger is never automatically replaced with empty data.
    page.evaluate("cloudNativeSet.call(localStorage,STORED_KEY,'corrupt')")
    page.reload(wait_until='networkidle')
    page.locator('#tabs button').get_by_text('客人儲值',exact=True).click()
    expect(page.locator('#storedStatus')).to_contain_text('無法讀取')
    assert page.evaluate('localStorage.getItem(STORED_KEY)')=='corrupt'
    assert not errors,errors
    print('PASS: mobile UI, customer/profile audit, topup/gifts, exact cents, debit/insufficient funds, reversal/duplicate guard, reload, failed writes, existing data preservation, full backup, legacy snapshots, corrupt storage; no page errors')
    browser.close()
