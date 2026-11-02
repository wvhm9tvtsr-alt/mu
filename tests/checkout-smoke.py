"""Isolated browser checks; no real customer data."""
from playwright.sync_api import sync_playwright, expect
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    c=b.new_context(viewport={'width':390,'height':844})
    page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8000/',wait_until='networkidle')
    before=page.evaluate('cloudSnapshot()')
    page.locator('#tabs button').get_by_text('結帳紀錄',exact=True).click()
    def add(kind,values):
        page.locator('#checkoutAdd-'+kind).click()
        f=page.locator('#checkoutForm')
        for key,value in values.items():
            el=f.locator('[name='+key+']')
            if key=='status':el.select_option(value)
            else:el.fill(value)
        return f
    def save(f):f.locator('button.primary').click()
    f=add('ledger',{'date':'2026-11-02','cash':'100.10','transfer':'200.20','card':'300.30','reviewer':'核對員'})
    page.locator('#checkoutPersonAdd-unsettled').click()
    page.locator('#checkoutPeople-unsettled [data-person-name]').fill('甲')
    page.locator('#checkoutPeople-unsettled [data-person-amount]').fill('40.40')
    page.locator('#checkoutPersonAdd-unpaid').click()
    page.locator('#checkoutPeople-unpaid [data-person-name]').fill('乙')
    page.locator('#checkoutPeople-unpaid [data-person-amount]').fill('50.50')
    save(f)
    expect(page.locator('#checkoutRows-ledger')).to_contain_text('600.6 元')
    expect(page.locator('#checkoutRows-ledger')).to_contain_text('甲／40.4 元')
    expect(page.locator('#checkoutTotal-ledger')).to_contain_text('50.5 元')
    save(add('ledger',{'date':'2026-11-02'}))
    expect(page.locator('#checkoutFeedback')).to_contain_text('同日')
    page.once('dialog',lambda d:d.accept());page.locator('#checkoutCancel').click()
    save(add('deposit',{'amount':'80.15'}))
    save(add('deposit',{'amount':'20.25','status':'已核對'}))
    expect(page.locator('#checkoutTotal-deposit')).to_contain_text('100.4 元')
    expect(page.locator('#checkoutTotal-deposit')).to_contain_text('80.15 元')
    save(add('claim',{'item':'耗材','amount':'30.35'}))
    save(add('petty',{'amount':'1000','pending':'125.55'}))
    expect(page.locator('#checkoutTotal-petty')).to_contain_text('125.55 元')
    save(add('petty',{'amount':'10','pending':'11'}))
    expect(page.locator('#checkoutFeedback')).to_contain_text('未回帳不可大於')
    page.once('dialog',lambda d:d.accept());page.locator('#checkoutCancel').click()
    # Edit amount, preserve prior version, update totals.
    page.locator('#checkoutRows-claim button').get_by_text('編輯',exact=True).click()
    page.locator('#checkoutForm [name=amount]').fill('35.45');save(page.locator('#checkoutForm'))
    expect(page.locator('#checkoutTotal-claim')).to_contain_text('35.45 元')
    assert page.evaluate('checkoutData.history.at(-1).previous.amount')==3035
    # Archive excludes from totals; restore brings it back.
    page.once('dialog',lambda d:d.accept());page.locator('#checkoutRows-claim button').get_by_text('封存',exact=True).click()
    expect(page.locator('#checkoutTotal-claim')).to_contain_text('0 元')
    page.locator('#checkoutArchived').check()
    page.once('dialog',lambda d:d.accept());page.locator('#checkoutRows-claim button').get_by_text('還原',exact=True).click()
    page.locator('#checkoutArchived').uncheck()
    expect(page.locator('#checkoutTotal-claim')).to_contain_text('35.45 元')
    snapshot=page.evaluate('JSON.stringify(checkoutData)')
    page.reload(wait_until='networkidle');page.locator('#tabs button').get_by_text('結帳紀錄',exact=True).click()
    assert page.evaluate('JSON.stringify(checkoutData)')==snapshot
    assert page.evaluate('cloudSnapshotValid(cloudSnapshot())')
    # Old backups preserve new records, even when stored-value data is also absent.
    assert page.evaluate('()=>{const p=cloudSnapshot();delete p.data[CHECKOUT_KEY];delete p.data[STORED_KEY];const d=cloudUpgradeSnapshot(p);return cloudSnapshotValid(d)&&d.data[CHECKOUT_KEY]===JSON.stringify(checkoutData)}')
    current=page.evaluate('cloudSnapshot()')
    for k,v in before['data'].items():
        if k!='mu-checkout-v1':assert current['data'][k]==v,k
    # Failed writes never replace the in-memory records.
    page.evaluate("()=>{window.testSet=Storage.prototype.setItem;Storage.prototype.setItem=()=>{throw Error('quota')}}")
    save(add('claim',{'item':'失敗測試','amount':'10'}))
    expect(page.locator('#checkoutFeedback')).to_contain_text('儲存失敗')
    assert page.evaluate('JSON.stringify(checkoutData)')==snapshot
    page.evaluate('()=>{Storage.prototype.setItem=window.testSet}')
    assert not errors,errors
    print('PASS: four sections, totals, named unpaid lists, duplicate date guard, edit audit, archive/restore, reload, backup compatibility, failed writes, other modules unchanged')
    b.close()
