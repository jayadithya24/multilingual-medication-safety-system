"""Live interaction/ML routes; doctor identity is stubbed, no patient data written."""
from playwright.sync_api import sync_playwright, expect


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        page.add_init_script("localStorage.setItem('mmss_token','review-test'); localStorage.setItem('mmss_role','doctor');")
        page.route('**/auth/me', lambda route: route.fulfill(json={'username': 'review@example.invalid', 'role': 'doctor'}))
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://localhost:5173/drug-interaction')
        expect(page.get_by_label('Medicine 1', exact=True).locator('option')).to_have_count(101)
        page.get_by_label('Medicine 1', exact=True).select_option('Ibuprofen')
        page.get_by_label('Medicine 2', exact=True).select_option('Methotrexate')
        page.get_by_role('button', name='Check Interaction', exact=True).click()
        expect(page.locator('.interaction-card')).to_contain_text('Review required', timeout=20000)
        expect(page.locator('.interaction-card')).to_contain_text('Moderate, Severe')
        page.get_by_role('button', name='Predict with DDInter model', exact=True).click()
        panel = page.get_by_role('region', name='DDInter ML prediction')
        expect(panel).to_contain_text('DDInter recorded label:', timeout=15000)
        expect(panel).to_contain_text('Model scores are not calibrated clinical probabilities.')
        page.get_by_text('Experimental ML comparison', exact=True).click()
        page.get_by_label('ML age', exact=True).fill('62')
        page.get_by_label('ML medicine count', exact=True).fill('3')
        for name, value in [('Gender', 'Female'), ('Condition', 'Hypertension'), ('Kidney function', 'Mild Impairment'), ('Liver function', 'Normal'), ('BMI category', 'Normal')]:
            page.get_by_label('ML ' + name, exact=True).select_option(value)
        page.get_by_role('button', name='Run experimental model').click()
        expect(page.locator('details.experimental-risk')).to_contain_text('Experimental label:', timeout=15000)
        expect(page.locator('details.experimental-risk')).to_contain_text('not a probability of clinical harm')
        page.get_by_label('Medicine 1', exact=True).select_option('Paracetamol')
        page.get_by_role('button', name='Check Interaction', exact=True).click()
        page.get_by_text('Experimental ML comparison', exact=True).click()
        expect(page.locator('details.experimental-risk')).to_contain_text("outside the model's training vocabulary")
        page.get_by_role('button', name='Predict with DDInter model', exact=True).click()
        expect(panel).to_contain_text('Insufficient evidence for a prediction', timeout=15000)
        expect(page.get_by_role('button', name='Run experimental model')).to_have_count(0)
        for width in (1440, 390):
            page.set_viewport_size({'width': width, 'height': 900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        assert not errors, errors
        browser.close()
    print('PASS: 100-drug doctor list, conflict provenance, live ML prediction, unsupported-model abstention, responsive layout.')


if __name__ == '__main__':
    main()
