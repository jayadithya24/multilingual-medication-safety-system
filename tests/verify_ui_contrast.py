"""Visual-only browser checks. Doctor identity/data are stubbed; no clinical claims."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://localhost:5173/')
        page.screenshot(path=str(ROOT / 'artifacts/home-contrast.png'), full_page=True)
        page.evaluate("sessionStorage.setItem('mmss_session', 'active'); sessionStorage.setItem('mmss_role', 'doctor');")
        page.route('**/auth/me', lambda route: route.fulfill(json={'username': 'visual@example.invalid', 'full_name': 'Visual test', 'role': 'doctor'}))
        page.route('**/doctor/patients', lambda route: route.fulfill(json={'patients': []}))
        page.goto('http://localhost:5173/doctor-patients')
        expect(page.get_by_text('No patients have active approved access.', exact=True)).to_be_visible()
        assert page.get_by_label('Patient sharing code').evaluate('(e) => getComputedStyle(e).backgroundColor') == 'rgb(255, 255, 255)'
        assert page.locator('.patient-sharing-form label').evaluate('(e) => getComputedStyle(e).color') == 'rgb(30, 41, 59)'
        assert page.get_by_text('No patients have active approved access.', exact=True).evaluate('(e) => getComputedStyle(e).color') == 'rgb(71, 85, 105)'
        page.screenshot(path=str(ROOT / 'artifacts/patient-history-contrast.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontal overflow'
        page.screenshot(path=str(ROOT / 'artifacts/patient-history-mobile.png'), full_page=True)
        assert not errors, errors
        browser.close()
        print(json.dumps({'visual_only_identity_stub': True, 'readable_form_and_empty_state': True, 'mobile_no_overflow': True, 'js_errors': errors}))

if __name__ == '__main__':
    main()
