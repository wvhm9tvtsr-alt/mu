from playwright.sync_api import sync_playwright,expect
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/',wait_until='networkidle');page.locator('#tabs button').get_by_text('醫生結帳',exact=True).click()
 def add(item,mode):
  page.locator('#newDoctorCheckout').click();f=page.locator('#doctorForm');f.locator('[name=item]').fill(item);f.locator('[name=item]').press('Tab');f.locator('[name=mode]').select_option(mode);f.locator('[name=cost]').fill('100');f.locator('button.primary').click()
 add('測試每人成本','person');row=page.locator('#doctorGroups tbody tr').first;row.locator('[name=customer]').fill('甲');row.locator('[name=charge]').fill('1000');row.locator('[name=doctorAmount]').fill('300.25');expect(row.locator('[data-share=yiyi]')).to_have_text('599.75');expect(page.locator('[data-total=doctor]')).to_have_value('300.25');expect(page.locator('[data-total=yiyi]')).to_have_value('599.75')
 page.locator('#saveDoctorDay').click();page.reload(wait_until='networkidle');page.locator('#tabs button').get_by_text('醫生結帳',exact=True).click();page.locator('#doctorGroups summary').click();row=page.locator('#doctorGroups tbody tr').first;expect(row.locator('[name=doctorAmount]')).to_have_value('300.25');row.locator('[name=doctorAmount]').fill('0');expect(page.locator('[data-total=yiyi]')).to_have_value('900');row.locator('[name=doctorAmount]').fill('');expect(page.locator('[data-total=doctor]')).to_have_value('450')
 add('測試全天成本','day');group=page.locator('#doctorGroups details').last;first=group.locator('tbody tr').first;first.locator('[name=customer]').fill('乙');first.locator('[name=charge]').fill('1000');first.locator('[name=doctorAmount]').fill('300');group.get_by_text('＋新增客人',exact=True).click();second=group.locator('tbody tr').last;second.locator('[name=customer]').fill('丙');second.locator('[name=charge]').fill('500');second.locator('[name=doctorAmount]').fill('100');expect(page.locator('[data-total=cost]')).to_have_value('200');expect(page.locator('[data-total=doctor]')).to_have_value('850');expect(page.locator('[data-total=yiyi]')).to_have_value('1450');page.locator('#saveDoctorDay').click();expect(page.locator('#doctorStatus')).to_contain_text('結帳已儲存')
 assert page.evaluate('doctorData.records[0].lines[2].doctorAmount')==100
 assert page.evaluate('doctorData.history.at(-1).previous.lines[0].doctorAmount')==300.25
 assert page.evaluate('cloudSnapshotValid(cloudSnapshot())');assert not errors,errors
 print('PASS: editable row payment, automatic remainder, save/reload/edit, zero, reset, shared daily cost, aggregate and audit backup')
 b.close()
