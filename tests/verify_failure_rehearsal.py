"""Fault-injected UI rehearsal, explicitly separate from real-service acceptance.

No database or network is stopped. Fake identity is used only for UI navigation;
no patient schedules are sent to the real backend.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.env_loader import load_project_env
load_project_env()
from backend.app.services import neo4j_service


def main():
    output = ROOT / 'artifacts' / 'fallback-rehearsal'
    output.mkdir(parents=True, exist_ok=True)
    # Exercise the service's real CSV fallback, with only its driver failing.
    with patch.object(neo4j_service, '_get_driver', side_effect=ConnectionError('Simulated unavailable graph')):
        graph = neo4j_service.get_knowledge_graph()
    assert graph['source'] == 'local_csv'
    assert len([node for node in graph['nodes'] if node['type'] == 'drug']) == 100
    saves = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.add_init_script("sessionStorage.setItem('mmss_session','active'); sessionStorage.setItem('mmss_role','patient');")

        def respond(route):
            path = urlparse(route.request.url).path
            if path == '/voice-search' and route.request.method == 'POST':
                route.abort('internetdisconnected')
                return
            if path == '/neo4j/graph':
                data = graph
            elif path == '/prescription-ocr':
                data = {'ocr_result': {'status': 'partial', 'medicine': None, 'dosage': None,
                    'instructions': None, 'raw_text': '', 'message': 'No prescription text could be detected. Please enter the details manually.'}}
            elif path == '/patient/profile':
                data = {'profile': {'full_name': 'Fictional fallback patient', 'patient_id': 'FALLBACK', 'age': 40}}
            elif path == '/patient-schedule' and route.request.method == 'POST':
                saves.append(route.request.post_data_json)
                data = {'status': 'success'}
            elif path.startswith('/patient-schedule'):
                data = {'schedules': []}
            elif path == '/auth/me':
                data = {'username': 'fallback@example.invalid', 'role': 'patient'}
            elif path == '/health':
                data = {'status': 'running', 'graph_check': {'status': 'unavailable', 'message': 'Simulated Neo4j outage'}}
            elif path == '/neo4j/search':
                data = {'results': [{'drug_name': 'Metformin', 'description': 'Fictional test response', 'warnings': 'Test only'}]}
            elif path == '/tts':
                route.fulfill(status=503, content_type='application/json', body='{"detail":"Simulated speech outage"}')
                return
            elif path in ('/medicines', '/neo4j/diseases'):
                data = {'medicines': [], 'diseases': []}
            else:
                data = {}
            route.fulfill(status=200, content_type='application/json', body=json.dumps(data))

        # Only API requests, never page navigation or frontend modules.
        def intercept(route):
            if route.request.resource_type in ('xhr', 'fetch'):
                respond(route)
            else:
                route.continue_()

        page.route('**/*', intercept)
        page.goto('http://localhost:5173/knowledge-graph')
        expect(page.get_by_text('Source: Local dataset (Neo4j unavailable)', exact=True)).to_be_visible()
        expect(page.get_by_role('button', name='Retry Neo4j connection')).to_be_visible()
        page.screenshot(path=str(output / 'graph-fallback.png'))

        page.goto('http://localhost:5173/scan-medicines')
        page.locator('input[type=file]').set_input_files({'name': 'blank.png', 'mimeType': 'image/png', 'buffer': b'simulated'})
        page.get_by_role('button', name='Scan Image', exact=True).click()
        expect(page.get_by_text('No prescription text could be detected. Please enter the details manually.', exact=True)).to_be_visible()
        expect(page.get_by_placeholder('e.g. Metformin')).to_have_value('')
        expect(page.get_by_placeholder('e.g. 500 mg')).to_have_value('')
        assert saves == []
        page.get_by_placeholder('e.g. Metformin').fill('Manually reviewed test medicine')
        page.get_by_placeholder('e.g. 500 mg').fill('TEST ONLY')
        page.locator('.prescription-switch').click()
        page.get_by_role('button', name='Add to Schedule', exact=True).click()
        expect(page.locator('.prescription-success')).to_be_visible()
        assert len(saves) == 1 and saves[0]['reminder_enabled'] is False
        page.screenshot(path=str(output / 'ocr-manual-recovery.png'))

        page.goto('http://localhost:5173/voice-search')
        page.locator('input[accept="audio/*"]').set_input_files(str(ROOT / 'tests/fixtures/voice/metformin-en.wav'))
        page.get_by_role('button', name='Search Medicine', exact=True).click()
        expect(page.locator('.voice-error')).to_be_visible()
        expect(page.get_by_role('link', name='use typed medicine search')).to_be_visible()
        expect(page.locator('.voice-result')).to_have_count(0)
        page.screenshot(path=str(output / 'voice-network-error.png'))
        page.get_by_role('link', name='use typed medicine search').click()
        page.get_by_placeholder('Search disease or drug').fill('Metformin')
        page.get_by_role('button', name='Search', exact=True).click()
        expect(page.locator('.patient-result')).to_contain_text('Metformin')
        assert not errors, errors
        browser.close()
    result = {'fault_injected': True, 'real_phone_test': False, 'live_services_stopped': False,
              'checks': ['Real CSV fallback with failing graph driver', 'Graph fallback labelled in UI',
                         'Empty OCR does not autofill/save; manual correction works',
                         'Voice network failure has no invented result; typed search recovery works'],
              'browser_js_errors': errors, 'passed': True}
    (output / 'results.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
