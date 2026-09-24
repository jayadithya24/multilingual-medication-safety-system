"""Admin approval/rejection, retry and role boundaries with synthetic API data."""
import re
from playwright.sync_api import sync_playwright, expect


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.add_init_script("localStorage.setItem('mmss_token','admin-ui-test');localStorage.setItem('mmss_role','admin');")
        requests = [{"request_id": f"TEST-{i}", "full_name": f"Review Doctor {i}", "email": f"review{i}@example.invalid", "medical_registration_no": f"TEST-REG-{i}", "specialization": "Test", "hospital": "Test Clinic", "status": "pending"} for i in (1, 2)]
        decisions = []
        fail_next = [True]
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        def respond(route):
            if route.request.method == "GET":
                route.fulfill(json={"requests": requests})
            elif fail_next[0]:
                fail_next[0] = False
                route.fulfill(status=503, json={"detail": "Temporary review failure"})
            else:
                parts = route.request.url.split("/")
                decisions.append(parts[-1])
                requests[:] = [item for item in requests if item["request_id"] != parts[-2]]
                route.fulfill(json={"status": parts[-1]})
        page.route(re.compile(r"/admin/doctor-requests(?:/|$)"), respond)
        page.goto("http://localhost:5173/admin-dashboard")
        expect(page.get_by_role("heading", name="Admin Dashboard", exact=True)).to_be_visible()
        page.get_by_role("button", name="Approve", exact=True).filter(visible=True).first.click()
        expect(page.get_by_text("Temporary review failure", exact=True)).to_be_visible()
        assert len(requests) == 2
        page.get_by_role("button", name="Approve", exact=True).filter(visible=True).first.click()
        expect(page.get_by_text("Temporary review failure", exact=True)).to_have_count(0)
        page.set_viewport_size({"width": 390, "height": 844})
        page.get_by_role("button", name="Reject", exact=True).filter(visible=True).first.click()
        expect(page.get_by_text("No pending doctor requests require attention right now.")).to_be_visible()
        assert decisions == ["approve", "reject"]
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        for role in ("patient", "doctor"):
            guest = browser.new_page()
            guest.add_init_script(f"localStorage.setItem('mmss_token','wrong-role');localStorage.setItem('mmss_role','{role}');")
            guest.goto("http://localhost:5173/admin-dashboard")
            expect(guest).to_have_url("http://localhost:5173/")
            guest.close()
        assert not errors, errors
        browser.close()
    print("PASS: admin approval, failure retry, rejection, empty queue, mobile layout and role guards.")


if __name__ == "__main__":
    main()
