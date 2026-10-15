"""Patient page layout checks at desktop and phone widths, with mocked data."""
import json
import os
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    backend = os.getenv("PATIENT_TEST_API_URL", "http://localhost:8000")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        page.add_init_script("localStorage.setItem('mmss_token','layout-test'); localStorage.setItem('mmss_role','patient');")
        def respond(route):
            body = {'profile': {'full_name': 'Layout Test', 'patient_id': 'TEST', 'age': 45, 'gender': 'Other', 'medical_condition': 'Hypertension'}, 'medicines': [], 'schedules': [], 'history': [], 'requests': [], 'google_client_id': ''}
            route.fulfill(status=200, content_type='application/json', body=json.dumps(body))
        page.route(f'{backend}/**', respond)
        routes = [('/patient-dashboard', 'My Medication Dashboard'), ('/patient-dashboard?tab=voice', 'Voice Search'), ('/patient-dashboard?tab=medicines', 'My Medicines'), ('/patient-profile', 'My Profile'), ('/scan-medicines', 'Scan & Add Medicines')]
        for width in (1440, 390):
            page.set_viewport_size({'width': width, 'height': 900})
            for route, title in routes:
                page.goto('http://localhost:5173' + route)
                heading = page.get_by_role('heading', name=title, level=1, exact=True)
                expect(heading).to_be_visible()
                expect(page.locator('h1')).to_have_count(1)
                nav = page.get_by_role('navigation', name='Patient navigation')
                expect(nav).to_be_visible()
                expect(page.locator('.patient-navigation')).to_have_count(0)
                expect(page.locator('.patient-sidebar')).to_be_visible()
                expect(nav.get_by_role('link', name='Knowledge Graph')).to_have_count(0)
                expect(nav.get_by_role('link', name='My Medicines', exact=True)).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), route
                expect(nav.locator('[aria-current="page"]')).to_have_count(1)
                expect(nav.get_by_role('link', name='Dashboard', exact=True)).to_be_visible()
                if route == '/patient-dashboard?tab=medicines':
                    expect(page.get_by_role('heading', name='Medicine Schedule', exact=False)).to_be_visible()
                    expect(page.get_by_text('Check notification delivery', exact=True)).to_be_visible()
            if width == 1440:
                output = Path(tempfile.gettempdir()) / 'patient-scan-layout.png'
                page.screenshot(path=str(output), full_page=True)
                print('Screenshot:', output)
        guest = browser.new_page()
        guest.route(f'{backend}/**', respond)
        guest.goto('http://localhost:5173/public')
        expect(guest.get_by_label('Name', exact=True)).to_be_visible()
        guest.get_by_role('button', name='Login', exact=True).click()
        expect(guest.get_by_text('Google sign-in is not available yet.', exact=False)).to_be_visible()
        guest.get_by_label('Password', exact=True).fill('test-password')
        guest.get_by_label('Show password', exact=True).check()
        expect(guest.get_by_label('Password', exact=True)).to_have_attribute('type', 'text')
        guest.evaluate("localStorage.setItem('mmss_token', 'expired'); localStorage.setItem('mmss_role', 'patient');")
        guest.route(f'{backend}/patient/profile', lambda route: route.fulfill(status=401, content_type='application/json', body='{}'))
        guest.goto('http://localhost:5173/patient-profile')
        expect(guest).to_have_url('http://localhost:5173/public?session=expired')
        expect(guest.get_by_text('Your session expired. Please sign in again.', exact=True)).to_be_visible()
        assert guest.evaluate("localStorage.getItem('mmss_token')") is None
        browser.close()
    print('PASS: all five patient sections at desktop and phone widths; headings, nav placement, active links, no horizontal overflow')


if __name__ == '__main__':
    main()
