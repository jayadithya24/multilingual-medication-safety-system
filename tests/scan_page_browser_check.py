"""Browser regression check with mocked APIs; creates no patient records."""
import json
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, expect


def main():
    backend = os.getenv("PATIENT_TEST_API_URL", "http://localhost:8000")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.add_init_script("localStorage.setItem('mmss_token', 'browser-test'); localStorage.setItem('mmss_role', 'patient');")
        page.add_init_script("window.scanSpeech = []; speechSynthesis.speak = utterance => { window.scanSpeech.push(utterance.text); utterance.onstart?.(); };")
        saves = []
        speech = []

        def api(route):
            path = route.request.url
            data = {}
            if '/tts?' in path:
                speech.append(parse_qs(urlparse(path).query))
                route.fulfill(status=200, content_type='audio/mpeg', body=(Path(__file__).parent / 'fixtures/voice/metformin-en.mp3').read_bytes())
                return
            if '/prescription-ocr' in path:
                data = {'ocr_result': {'status': 'success', 'medicine': 'Metformin', 'dosage': '500 mg', 'instructions': 'After food', 'medicine_details': {'drug_name': 'Metformin', 'description': 'Test medicine information'}}}
            elif '/patient-schedule' in path and route.request.method == 'POST':
                saves.append(route.request.post_data_json)
                data = {'status': 'success'}
            elif '/medicines' in path:
                data = {'medicines': []}
            elif '/patient/profile' in path:
                data = {'profile': {'full_name': 'UI Test Patient', 'patient_id': 'TEST', 'age': 50, 'gender': 'Male', 'medical_condition': 'Hypertension'}}
            elif '/neo4j/search' in path:
                data = {'results': [{'drug_name': 'Metformin', 'description': 'Test medicine description. More details.', 'warnings': 'Test warning.'}]}
            route.fulfill(status=200, content_type='application/json', body=json.dumps(data))

        page.route(f'{backend}/**', api)
        page.goto('http://localhost:5173/patient-dashboard')
        expect(page.get_by_role('link', name='Scan & Add Medicines')).to_have_count(1)
        expect(page.get_by_role('button', name='OCR Scan', exact=True)).to_have_count(0)
        page.get_by_placeholder('Type a medicine name').fill('Metformin')
        page.get_by_role('button', name='Search', exact=True).click()
        expect(page.locator('.patient-result audio')).to_have_count(1)
        assert 'More details' not in speech[-1]['text'][0]
        assert 'Test warning' in speech[-1]['text'][0]
        assert page.evaluate('window.scanSpeech.length') == 0
        expect(page.locator('.patient-result audio[controls]')).to_have_count(0)
        page.evaluate('window.scanSpeech = []')
        page.get_by_role('link', name='My Profile', exact=True).click()
        expect(page.get_by_label('Full Name', exact=True)).to_have_value('UI Test Patient')
        expect(page.get_by_role('link', name='My Profile', exact=True)).to_have_attribute('aria-current', 'page')
        expect(page.get_by_role('link', name='Back to dashboard')).to_be_visible()
        page.set_viewport_size({'width': 390, 'height': 844})
        expect(page.get_by_role('link', name='My Medicines', exact=True)).to_be_visible()
        page.get_by_role('link', name='My Medicines', exact=True).click()
        expect(page).to_have_url('http://localhost:5173/patient-dashboard?tab=medicines')
        expect(page.get_by_role('link', name='My Medicines', exact=True)).to_have_attribute('aria-current', 'page')
        page.get_by_role('link', name='Voice Search', exact=True).click()
        expect(page.get_by_role('button', name='Record', exact=True)).to_be_visible()
        expect(page.get_by_role('heading', name='Speak or upload an audio clip to find a medicine')).to_be_visible()
        expect(page.get_by_role('combobox')).to_have_count(1)
        expect(page.get_by_role('combobox')).to_have_value('auto')
        expect(page.locator('.voice-search-page--embedded')).to_be_visible()
        page.set_viewport_size({'width': 1280, 'height': 800})
        page.get_by_role('link', name='Scan & Add Medicines').click()
        expect(page.get_by_role('heading', name='Scan & Add Medicines')).to_be_visible()
        page.locator('input[type=file]').set_input_files({'name': 'test.png', 'mimeType': 'image/png', 'buffer': b'test-image'})
        page.get_by_role('button', name='Scan Image', exact=True).click()
        expect(page.get_by_placeholder('e.g. Metformin')).to_have_value('Metformin')
        expect(page.get_by_placeholder('e.g. 500 mg')).to_have_value('500 mg')
        expect(page.get_by_label('Spoken medicine response')).to_be_visible()
        assert 'Metformin. 500 mg. After food' in speech[-1]['text'][0]
        page.get_by_role('button', name='Read scan aloud again').click()
        expect(page.get_by_label('Spoken medicine response')).to_be_visible()
        page.get_by_role('button', name='Stop reading', exact=True).click()
        expect(page.get_by_role('button', name='Read scan aloud again')).to_have_count(0)
        assert not saves, 'Scanning must not save a schedule'
        page.get_by_placeholder('e.g. 500 mg').fill('250 mg')
        page.locator('.prescription-switch').click()
        page.get_by_role('button', name='Add to Schedule', exact=True).click()
        expect(page.locator('.prescription-success')).to_be_visible()
        assert len(saves) == 1 and saves[0]['dosage'] == '250 mg'
        assert saves[0]['reminder_enabled'] is False
        page.get_by_label('Language', exact=True).select_option('tulu')
        page.locator('input[type=file]').set_input_files({'name': 'tulu-test.png', 'mimeType': 'image/png', 'buffer': b'test-image'})
        page.get_by_role('button', name='Scan Image', exact=True).click()
        expect(page.get_by_label('Spoken medicine response')).to_be_visible()
        assert speech[-1]['lang'] == ['tulu']
        assert 'ಬಳಕೆ ಮಲ್ಪುನ ದುಂಬು ಈ ವಿವರನ್ ಈರ್ನ ಔಷಧ ಚೀಟಿದ ಒಟ್ಟು ಪರಿಶೀಲನೆ ಮಲ್ಪುಲೆ.' in speech[-1]['text'][0]
        page.get_by_placeholder('e.g. Metformin').fill('Manual test')
        expect(page.get_by_role('button', name='Add to Schedule', exact=True)).to_be_enabled()
        for legacy in ('ocr', 'prescription'):
            page.goto('http://localhost:5173/' + legacy)
            expect(page).to_have_url('http://localhost:5173/scan-medicines')
        page = browser.new_page()
        page.goto('http://localhost:5173/scan-medicines')
        expect(page).to_have_url('http://localhost:5173/public')
        expect(page.get_by_role('button', name='Register', exact=True).first).to_be_visible()
        browser.close()
        print('PASS: unified navigation, scan review, explicit save, corrected dosage, manual entry, legacy redirects, guest profile guard')


if __name__ == '__main__':
    main()
