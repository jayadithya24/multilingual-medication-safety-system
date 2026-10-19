"""Check both dashboards against live dataset APIs; identity and speech are stubbed."""
import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        def route_api(route):
            path = urlsplit(route.request.url).path
            if route.request.resource_type not in ("xhr", "fetch", "media"):
                route.continue_()
            elif path.startswith(("/patient", "/auth", "/fcm")):
                route.fulfill(status=200, content_type="application/json", body="{}")
            elif path == "/tts":
                route.fulfill(status=200, content_type="audio/mpeg", body=b"")
            else:
                route.continue_()

        page.route("**/*", route_api)
        page.goto("http://localhost:5173")
        page.evaluate("localStorage.setItem('mmss_token','scope-test'); localStorage.setItem('mmss_role','patient')")
        page.goto("http://localhost:5173/patient-dashboard")
        records = {}
        for lang, name in (("en", "english"), ("kn", "kannada"), ("tulu", "tulu")):
            records[lang] = list(csv.DictReader((ROOT / f"datasets/{name}_master_dataset.csv").open(encoding="utf-8-sig")))
            page.locator(".patient-language select").select_option(lang)
            expect(page.locator("#patient-medicine-options option")).to_have_count(100)
            for row in ([] if '--doctor-only' in sys.argv else records[lang]):
                page.get_by_placeholder("Search disease or drug").fill(row["drug_name"])
                page.get_by_role("button", name="Search", exact=True).click()
                card = page.locator(".medicine-card")
                expect(card.get_by_role("heading", name=row["drug_name"], exact=True)).to_be_visible()
                expect(card).to_contain_text(row["description"])
            print(f"Patient {lang} checked", flush=True)
        page.evaluate("localStorage.setItem('mmss_role','doctor')")
        page.goto("http://localhost:5173/doctor-dashboard")
        expect(page.locator(".doctor-dashboard__scope")).to_contain_text("100 medicines across 10 diseases")
        page.goto("http://localhost:5173/disease-protocols")
        for lang, name in (("en", "English"), ("kn", "Kannada"), ("tulu", "Tulu")):
            if lang != "en":
                page.locator(".language-selector__button").click()
                page.get_by_role("option", name=name, exact=False).click()
            expect(page.locator("#disease-select option")).to_have_count(11)
            for disease in sorted({r["disease"] for r in records[lang]}):
                page.locator("#disease-select").select_option(disease)
                expected = [r for r in records[lang] if r["disease"] == disease]
                expect(page.locator(".disease-drug-card")).to_have_count(len(expected))
                for row in expected:
                    expect(page.locator(".disease-drug-card").filter(has=page.get_by_role("heading", name=row["drug_name"], exact=True))).to_contain_text(row["description"])
            print(f"Doctor {lang}: 10 disease lists checked", flush=True)
        assert not errors, errors
        print(json.dumps({"patient_medicine_searches": 0 if '--doctor-only' in sys.argv else 300, "doctor_disease_lists": 30, "page_errors": errors,
                          "identity_and_speech": "stubbed; live dataset APIs"}))
        browser.close()


if __name__ == "__main__":
    main()
