from pathlib import Path
import json
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
    page=browser.new_page(viewport={'width':1440,'height':1100}, device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((root/'output/index.html').as_uri(),wait_until='load')
    page.screenshot(path=str(root/'preview_desktop.png'))
    desktop=page.evaluate('''() => ({bodyFont:getComputedStyle(document.body).fontSize, overflow:document.documentElement.scrollWidth>innerWidth, images:document.images.length, brokenImages:[...document.images].filter(i=>i.complete && i.naturalWidth===0).length, caseSections:document.querySelectorAll('article.case').length})''')
    page.locator('#case_02-V04').scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.screenshot(path=str(root/'preview_evidence.png'))
    page.set_viewport_size({'width':390,'height':844})
    page.goto((root/'output/index.html').as_uri(),wait_until='load')
    page.screenshot(path=str(root/'preview_mobile.png'))
    mobile=page.evaluate('''() => ({bodyFont:getComputedStyle(document.body).fontSize, overflow:document.documentElement.scrollWidth>innerWidth})''')
    page.locator('a[href="#case_03"]').first.click()
    page.wait_for_timeout(300)
    navigation=page.evaluate('location.hash')
    page.locator('#case_03-V04 summary').click()
    expanded=page.locator('#case_03-V04 details').get_attribute('open') is not None
    page.route('https://reference.test/**',lambda route:route.fulfill(status=200,content_type='text/html',headers={'Content-Security-Policy':"sandbox allow-scripts; default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:"},body=(root/'output/index.html').read_text(encoding='utf-8')))
    page.set_viewport_size({'width':1440,'height':1100})
    page.goto('https://reference.test/',wait_until='load')
    page.get_by_role('button',name='Open case_01 V01 full image',exact=True).click()
    lightbox=page.locator('#image-dialog').evaluate('(d)=>d.open')
    enlarged=page.locator('#image-stage img').evaluate('(i)=>i.complete && i.naturalWidth===960')
    page.screenshot(path=str(root/'preview_lightbox.png'))
    page.get_by_role('button',name='Close image',exact=True).click()
    lightbox_closed=not page.locator('#image-dialog').evaluate('(d)=>d.open')
    browser.close()
result={'desktop':desktop,'mobile':mobile,'navigation_hash':navigation,'evidence_details_expand':expanded,'sandbox_lightbox_opens':lightbox,'sandbox_full_resolution_image_loads':enlarged,'sandbox_lightbox_closes':lightbox_closed,'sandbox_test_policy':"sandbox allow-scripts; default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:",'page_errors':errors}
assert desktop['bodyFont']=='18px' and mobile['bodyFont']=='18px'
assert not desktop['overflow'] and not mobile['overflow']
assert desktop['images']==30 and desktop['brokenImages']==0 and desktop['caseSections']==3
assert navigation=='#case_03' and expanded and not errors
assert lightbox and enlarged and lightbox_closed
(root/'render_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
