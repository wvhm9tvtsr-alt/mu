from playwright.sync_api import sync_playwright,expect
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/',wait_until='networkidle');page.locator('#tabs button').get_by_text('醫生結帳',exact=True).click()
 page.locator('#newDoctorCheckout').click();f=page.locator('#doctorForm');f.locator('[name=item]').fill('測試品項');f.locator('[name=cost]').fill('100');f.locator('button.primary').click();page.locator('#doctorGroups [name=customer]').fill('測試客人');page.locator('#doctorGroups [name=charge]').fill('1000');page.locator('#saveDoctorDay').click()
 original=page.evaluate('JSON.stringify(doctorData.records[0])')
 page.once('dialog',lambda d:d.dismiss());page.locator('#doctorGroups button').get_by_text('移除',exact=True).click()
 assert page.locator('#doctorGroups tbody tr').count()==1
 page.once('dialog',lambda d:d.accept());page.locator('#doctorGroups button').get_by_text('移除',exact=True).click()
 assert page.locator('#doctorGroups tbody tr').count()==0
 assert page.evaluate('JSON.stringify(doctorData.records[0])')==original
 page.once('dialog',lambda d:d.dismiss());page.locator('#saveDoctorDay').click()
 assert page.evaluate('doctorData.records.length')==1
 page.once('dialog',lambda d:d.accept());page.locator('#saveDoctorDay').click()
 assert page.evaluate('doctorData.records.length')==0
 assert page.evaluate('JSON.stringify(doctorData.history.at(-1).previous)')==original
 page.reload(wait_until='networkidle');assert page.evaluate('doctorData.records.length')==0
 assert page.evaluate('cloudSnapshotValid(cloudSnapshot())');assert not errors,errors
 print('PASS: remove final customer, cancel, staged deletion, persisted removal, history preservation, reload and backup')
 b.close()
