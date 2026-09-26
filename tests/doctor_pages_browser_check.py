"""Doctor consent and report navigation checks; API data is mocked."""
from playwright.sync_api import sync_playwright, expect


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        history = []
        page.add_init_script("localStorage.setItem('mmss_token','ui-test'); localStorage.setItem('mmss_role','doctor');")
        page.route("**/auth/me", lambda route: route.fulfill(json={"username": "doctor.test@example.invalid", "full_name": "Alex Doctor", "role": "doctor"}))
        def respond(route):
            if route.request.resource_type not in {"fetch", "xhr"}:
                route.continue_()
                return
            if route.request.url.endswith("/report"):
                route.fulfill(json={"generated_at": "2026-09-25T08:00:00+00:00", "doctor": "Test Doctor", "patient": {"username": "review@example.invalid", "full_name": "Test Patient", "patient_id": "TEST"}, "prescriptions": [{"medicine_name": "Prescription medicine", "dosage": "Saved dose", "frequency": "Daily", "instructions": "Complete saved instructions <script>alert(1)</script>", "scheduled_times": ["08:00"], "status": "active"}], "history": history})
            elif "/doctor/patients" in route.request.url:
                route.fulfill(json={"patients": [{"patient_id": "TEST", "name": "Test Patient", "status": "PENDING"}]})
            elif "/doctor/medication-history" in route.request.url:
                route.fulfill(json={"history": history})
            else:
                route.fulfill(json={})
        page.route("**/doctor/**", respond)
        page.goto("http://localhost:5173/doctor-patients")
        expect(page.get_by_text("Awaiting patient approval", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="(Demo: Grant Consent)", exact=True)).to_have_count(0)
        page.locator('a[href="/reports"]').click()
        expect(page).to_have_url("http://localhost:5173/reports")
        expect(page.get_by_role("heading", name="Reports", exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="No medication history to display")).to_be_visible()
        expect(page.get_by_text("Safety alerts", exact=True)).to_have_count(0)
        history.append({"history_id": "H-TEST", "patient_username": "review@example.invalid", "medicine_name": "Test medicine", "dosage": "Test dose", "scheduled_time": "08:00", "taken_at": "2026-09-24T08:00:00+00:00"})
        page.get_by_role("button", name="Refresh", exact=True).click()
        expect(page.get_by_role("cell", name="Test medicine", exact=True)).to_be_visible()
        expect(page.get_by_role("cell", name="Test dose", exact=True)).to_be_visible()
        expect(page.get_by_label("Filter history by patient")).to_be_visible()
        page.get_by_label("Report patient", exact=True).select_option("review@example.invalid")
        page.get_by_role("button", name="Generate report", exact=True).click()
        expect(page.get_by_role("heading", name="Prescription report", exact=True)).to_be_visible()
        expect(page.get_by_text("Complete saved instructions <script>alert(1)</script>", exact=True)).to_be_visible()
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download report (HTML)").click()
        download = download_info.value
        assert download.suggested_filename == "prescription-report-TEST.html"
        from pathlib import Path
        content = Path(download.path()).read_text(encoding="utf-8")
        assert "Saved dose" in content and "Daily" in content and "&lt;script&gt;" in content
        page.get_by_role("button", name="Print / Save as PDF").click()
        expect(page.frame_locator('iframe[title="Print prescription report"]').get_by_role("heading", name="Prescription report", exact=True)).to_be_attached()
        for width in (1440, 390):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        page.set_viewport_size({"width": 1440, "height": 900})
        page.screenshot(path="artifacts/reports-reviewed.png", full_page=True)
        guest = browser.new_page()
        guest.goto("http://localhost:5173/reports")
        expect(guest).to_have_url("http://localhost:5173/")
        browser.close()
    print("PASS: pending access cannot be granted locally; Reports is reachable for doctors and redirects guests.")


if __name__ == "__main__":
    main()
