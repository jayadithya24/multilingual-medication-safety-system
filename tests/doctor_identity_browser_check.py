"""Doctor identity and expired-session handling with synthetic API responses."""
from playwright.sync_api import sync_playwright, expect


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.add_init_script("localStorage.setItem('mmss_token','test-token'); localStorage.setItem('mmss_role','doctor');")
        page.route("**/auth/me", lambda route: route.fulfill(json={"username": "alex@example.invalid", "full_name": "Alex Rao", "role": "doctor"}))
        page.route("**/doctor/patients", lambda route: route.fulfill(json={"patients": []}))
        page.goto("http://localhost:5173/doctor-patients")
        expect(page.locator(".doctor-topbar__user")).to_contain_text("Alex Rao")
        expect(page.locator(".doctor-sidebar__profile")).to_contain_text("alex@example.invalid")
        expect(page.locator(".doctor-sidebar__language")).to_have_count(0)
        expect(page.get_by_text("Clinical User", exact=True)).to_have_count(0)
        expect(page.get_by_text("Medical Professional", exact=True)).to_have_count(0)
        page.unroute("**/doctor/patients")
        page.route("**/doctor/patients", lambda route: route.fulfill(status=401, json={"detail": "Could not validate credentials"}))
        page.reload()
        expect(page).to_have_url("http://localhost:5173/research?session=expired")
        expect(page.get_by_text("Your session has expired or is no longer valid. Please sign in again.")).to_be_visible()
        browser.close()
    print("PASS: authenticated name/username, removed duplicate language controls, doctor session expiry redirect")


if __name__ == "__main__":
    main()
