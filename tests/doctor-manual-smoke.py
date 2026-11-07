from playwright.sync_api import sync_playwright,expect
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/',wait_until='networkidle')
 page.locator('#tabs button').get_by_text('醫生結帳',exact=True).click()
 page.locator('#doctorName').fill('新醫師')
 page.locator('#newDoctorCheckout').click();f=page.locator('#doctorForm');f.locator('[name=item]').fill('測試療程');f.locator('[name=cost]').fill('100');f.locator('button.primary').click()
 page.locator('#doctorGroups [name=customer]').fill('測試客人');page.locator('#doctorGroups [name=charge]').fill('1000')
 expect(page.locator('[data-total=doctor]')).to_have_value('450')
 page.locator('#doctorPaymentMode').select_option('manual');page.locator('[data-total=doctor]').fill('321.25');expect(page.locator('[data-total=yiyi]')).to_have_value('578.75');expect(page.locator('[data-total=yiyi]')).to_have_attribute('readonly','')
 page.locator('#saveDoctorDay').click();expect(page.locator('#doctorStatus')).to_contain_text('結帳已儲存')
 assert page.evaluate('doctorData.records[0].doctor')=='新醫師'
 page.reload(wait_until='networkidle');page.locator('#tabs button').get_by_text('醫生結帳',exact=True).click()
 expect(page.locator('#doctorName')).to_have_value('新醫師');expect(page.locator('#doctorPaymentMode')).to_have_value('manual');expect(page.locator('[data-total=doctor]')).to_have_value('321.25')
 page.locator('#doctorGroups summary').click();page.locator('#doctorGroups [name=charge]').fill('1200');expect(page.locator('[data-total=doctor]')).to_have_value('321.25')
 expect(page.locator('[data-total=yiyi]')).to_have_value('778.75')
 page.locator('[data-total=doctor]').fill('0');expect(page.locator('[data-total=yiyi]')).to_have_value('1100')
 page.locator('[data-total=doctor]').fill('1200');expect(page.locator('[data-total=yiyi]')).to_have_value('-100')
 page.locator('#doctorPaymentMode').select_option('auto');expect(page.locator('[data-total=doctor]')).to_have_value('550')
 expect(page.locator('[data-total=yiyi]')).to_have_value('550')
 assert page.evaluate('cloudSnapshotValid(cloudSnapshot())');assert not errors,errors
 print('PASS: manual payment, doctor name, persistence, costs changing, auto restore and backup validation')
 b.close()
