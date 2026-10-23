"""Isolated browser regression test. Requires the static site on port 8000."""
from playwright.sync_api import sync_playwright, expect
import json, sys
BASE=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000/'
legacy={'records':[{'id':'old-1','date':'2026-01-01','kind':'進貨','name':'歷史客人','dose':'原值','cc':1.5,'cost':500,'price':0,'archived':False}], 'history':[{'action':'原有留檔','previous':None}]}
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844})
    context.add_init_script("if(!localStorage.getItem('mu-mounjaro-v1'))localStorage.setItem('mu-mounjaro-v1',"+json.dumps(json.dumps(legacy,ensure_ascii=False))+ ")")
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE,wait_until='networkidle')
    other=page.evaluate('cloudSnapshot()')
    page.locator('#tabs button').get_by_text('猛健樂記錄',exact=True).click()
    page.locator('#penClosed').click()
    assert page.locator('#mounjaroLegacy').get_attribute('open') is not None
    expect(page.locator('#mounjaroRows tr')).to_have_count(1)
    expect(page.locator('#mounjaroRows')).to_be_visible()
    expect(page.locator('#mounjaroLegacy > summary')).to_contain_text('1 筆')
    assert page.evaluate('mounjaro.records')==legacy['records']
    assert page.evaluate('localStorage.getItem(MOUNJARO_KEY)')==json.dumps(legacy,ensure_ascii=False)
    page.locator('#penActive').click()
    expect(page.locator('#mounjaroLegacy')).to_be_hidden()
    def create(label,cc,cost):
        page.locator('#penNew').click();f=page.locator('#penForm')
        for k,v in {'label':label,'date':'2026-10-01','dose':'測試','cc':cc,'cost':cost}.items():f.locator(f'[name={k}]').fill(v)
        f.locator('button.primary').click()
    def card(label):return page.locator('#penCards > details').filter(has=page.locator('summary').filter(has_text=label))
    def open_card(label):
        c=card(label)
        if c.get_attribute('open') is None:c.locator('summary').click()
        return c
    def sale(label,cc,price):
        open_card(label).get_by_role('button',name='新增售出',exact=True).click()
        f=page.locator('#penSaleForm')
        for k,v in {'date':'2026-10-23','name':'測試客人','cc':cc,'price':price,'note':'測試'}.items():f.locator(f'[name={k}]').fill(v)
        f.locator('button.primary').click()
    create('第一隻','3','1000.15');create('第二隻','5','2000')
    sale('第一隻','1.1','800.10')
    assert page.evaluate('mounjaroPenSummary(mounjaro.pens.find(p=>p.label==="第一隻"))')=={'sold':1100000,'remaining':1900000,'revenue':80010,'profit':-20005}
    assert page.evaluate('mounjaroPenSummary(mounjaro.pens.find(p=>p.label==="第二隻")).remaining')==5000000
    open_card('第一隻').get_by_role('button',name='賣完結算',exact=True).click()
    expect(page.locator('#mounjaroStatus')).to_contain_text('尚有')
    snapshot=page.evaluate('JSON.stringify(mounjaro)')
    sale('第一隻','2','1000')
    expect(page.locator('#penSaleFeedback')).to_contain_text('剩餘 cc')
    assert page.evaluate('JSON.stringify(mounjaro)')==snapshot
    page.locator('#penSaleForm [name=cc]').fill('1.9');page.locator('#penSaleForm button.primary').click()
    assert page.evaluate('mounjaroPenSummary(mounjaro.pens.find(p=>p.label==="第一隻")).profit')==79995
    page.once('dialog',lambda d:d.accept());open_card('第一隻').get_by_role('button',name='賣完結算',exact=True).click()
    assert page.locator('#penCards > details').count()==1
    page.locator('#penClosed').click();c=open_card('第一隻')
    assert c.locator('tbody tr').count()==2
    assert c.get_by_role('button',name='新增售出').count()==0
    page.reload(wait_until='networkidle');page.locator('#tabs button').get_by_text('猛健樂記錄',exact=True).click();page.locator('#penClosed').click()
    assert page.evaluate('mounjaro.pens.find(p=>p.label==="第一隻").closed') is True
    page.once('dialog',lambda d:d.accept());open_card('第一隻').get_by_role('button',name='重新開啟',exact=True).click()
    page.locator('#penActive').click();c=open_card('第一隻')
    page.once('dialog',lambda d:d.accept());c.locator('tbody tr').first.get_by_role('button',name='撤銷售出',exact=True).click()
    assert page.evaluate('mounjaroPenSummary(mounjaro.pens.find(p=>p.label==="第一隻")).remaining')==1100000
    assert page.evaluate('mounjaro.pens.find(p=>p.label==="第一隻").sales.length')==2
    sale('第一隻','1.1','850')
    assert page.evaluate('mounjaroPenSummary(mounjaro.pens.find(p=>p.label==="第一隻")).profit')==84985
    # Editing a sale updates this pen and retains the previous version in history.
    open_card('第一隻').locator('tbody tr').last.get_by_role('button',name='修改',exact=True).click()
    page.locator('#penSaleForm [name=price]').fill('851.25')
    page.locator('#penSaleForm [name=name]').fill('更正客人')
    page.locator('#penSaleForm button.primary').click()
    assert page.evaluate('mounjaroPenSummary(mounjaro.pens.find(p=>p.label==="第一隻")).profit')==85110
    assert page.evaluate('mounjaro.history.at(-1).action')=='修改售出'
    # Editing legacy data must not remove the independent ledgers.
    page.locator('#penClosed').click()
    if page.locator('#mounjaroLegacy').get_attribute('open') is None:page.locator('#mounjaroLegacy > summary').click()
    page.locator('#mounjaroRows button').get_by_text('編輯',exact=True).click()
    page.locator('#mounjaroForm [name=name]').fill('歷史更正')
    page.locator('#mounjaroForm button.primary').click()
    assert page.evaluate('mounjaro.pens.length')==2
    assert page.evaluate('mounjaro.history.at(-1).previous.name')=='歷史客人'
    page.reload(wait_until='networkidle')
    page.locator('#tabs button').get_by_text('猛健樂記錄',exact=True).click()
    page.locator('#penClosed').click()
    expect(page.locator('#mounjaroRows')).to_contain_text('歷史更正')
    assert page.evaluate('mounjaro.history[0]')==legacy['history'][0]
    # Failed writes preserve the previous in-memory state.
    original=page.evaluate('JSON.stringify(mounjaro)')
    page.evaluate("() => {window.testSet=Storage.prototype.setItem;Storage.prototype.setItem=()=>{throw Error('quota')};}")
    create('失敗的第三隻','1','100')
    expect(page.locator('#penFeedback')).to_contain_text('儲存失敗')
    assert page.evaluate('JSON.stringify(mounjaro)')==original
    page.evaluate('() => {Storage.prototype.setItem=window.testSet;}');page.locator('#penForm').evaluate("f=>{f.hidden=true;delete f.dataset.cloudDirty}")
    # Export includes complete history and both ledgers; validate restored payload.
    page.locator('#penClosed').click()
    page.locator('#mounjaroLegacy details > summary').click()
    with page.expect_download() as download:page.locator('#mounjaroExport').click()
    saved=json.loads(open(download.value.path()).read());assert len(saved['pens'])==2
    assert saved['history'][0]==legacy['history'][0]
    assert page.evaluate('d=>validMounjaro(d)',saved) is True
    assert page.evaluate('cloudSnapshotValid(cloudSnapshot())') is True
    current=page.evaluate('cloudSnapshot()')
    for k,v in other['data'].items():
        if k!='mu-mounjaro-v1':assert current['data'][k]==v,k
    # Pre-pen imports preserve the new ledgers and their audit history.
    expected_pens=page.evaluate('mounjaro.pens')
    expected_audit=page.evaluate('mounjaro.history.filter(h=>h.penId)')
    page.once('dialog',lambda d:d.accept())
    page.locator('#mounjaroFile').set_input_files({'name':'old.json','mimeType':'application/json','buffer':json.dumps(legacy).encode()})
    expect(page.locator('#mounjaroStatus')).to_contain_text('已儲存')
    assert page.evaluate('mounjaro.pens')==expected_pens
    assert page.evaluate('mounjaro.history.filter(h=>h.penId)')==expected_audit
    assert page.evaluate("async () => {let p=cloudSnapshot();const d=JSON.parse(p.data[MOUNJARO_KEY]);delete d.pens;d.history=d.history.filter(h=>!h.penId);p.data[MOUNJARO_KEY]=JSON.stringify(d);await cloudApply(cloudUpgradeSnapshot(p,storedData,true),cloudEpoch);return mounjaro.pens.length}")==2
    assert page.evaluate('mounjaro.history.filter(h=>h.penId)')==expected_audit
    # Recovery search reads backups without changing current records or pen ledgers.
    missing={**legacy['records'][0], 'id':'missing-from-backup','name':'待補回紀錄'}
    page.evaluate("async d => {const payload=cloudSnapshot();payload.data[MOUNJARO_KEY]=JSON.stringify(d);await cloudBackup(payload,'測試舊紀錄來源')}",{'records':[missing],'history':[]})
    before_recovery=page.evaluate('JSON.stringify(mounjaro)')
    page.locator('#mounjaroFindOld').click()
    expect(page.locator('#mounjaroRecoveryStatus')).to_contain_text('找到')
    assert page.evaluate('JSON.stringify(mounjaro)')==before_recovery
    assert page.locator('#mounjaroRecoveryChoices button').get_by_text('補回缺少的 1 筆',exact=True).count()==1
    page.once('dialog',lambda d:d.accept())
    page.locator('#mounjaroRecoveryChoices button').get_by_text('補回缺少的 1 筆',exact=True).click()
    expect(page.locator('#mounjaroRecoveryStatus')).to_contain_text('已補回 1 筆')
    assert page.evaluate('mounjaro.pens')==expected_pens
    assert page.evaluate('mounjaro.records.some(r=>r.id==="missing-from-backup")') is True
    assert page.locator('#mounjaroLegacy').get_attribute('open') is not None
    expect(page.locator('#mounjaroRows')).to_contain_text('待補回紀錄')
    # Same source cannot introduce duplicate records.
    page.locator('#mounjaroFindOld').click()
    expect(page.locator('#mounjaroRecoveryStatus')).to_contain_text('找到')
    assert page.locator('#mounjaroRecoveryChoices button').get_by_text('補回缺少的 1 筆',exact=True).count()==0
    assert page.evaluate("Object.keys(localStorage).some(k=>k.startsWith('mu-mounjaro-before-recovery-'))") is True
    assert not errors,errors
    print('PASS: separate pens, legacy preservation, precise quantities/money, cost once, oversell guard, settlement/reopen, reversal audit, reload, failed writes, backups and other modules')
    browser.close()
