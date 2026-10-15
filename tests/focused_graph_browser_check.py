"""Exercise real graph APIs and UI; only the authenticated interaction summary is stubbed."""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright, expect


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.add_init_script("localStorage.setItem('mmss_token','ui-test'); localStorage.setItem('mmss_role','doctor');")
        page.route("**/auth/me", lambda route: route.fulfill(json={"username": "graph.test@example.invalid", "full_name": "Graph Doctor", "role": "doctor"}))
        page.goto("http://localhost:5173/drug-reference")
        picker = page.get_by_label("Choose a medicine", exact=True)
        expect(picker).to_be_enabled()
        picker.select_option("Celecoxib")
        expect(page.get_by_role("button", name="Medicine: Celecoxib", exact=True)).to_be_visible(timeout=20000)
        expect(page.locator(".reference-details h2")).to_have_text("Celecoxib")
        assert page.locator(".med-graph__node").count() <= 11
        page.get_by_role("button", name="Medicine: Celecoxib", exact=True).click()
        expect(page.get_by_role("complementary", name="Node details")).to_be_visible()
        page.get_by_role("button", name="Close node details").click()
        condition = page.get_by_role("button", name="Condition: Arthritis", exact=True)
        condition.click()
        expect(condition).to_have_attribute("aria-pressed", "true")
        expect(page.locator(".med-graph__edge.is-highlighted")).to_have_count(1)
        expect(page.locator(".med-graph__node.is-connected")).to_have_count(2)
        assert page.locator(".med-graph__node.is-dimmed").count() > 0
        assert page.locator(".med-graph__edge.is-dimmed").first.evaluate("e => getComputedStyle(e).opacity") == "0.12"
        condition.press("Escape")
        expect(page.locator(".med-graph__node.is-dimmed")).to_have_count(0)
        condition.click()
        condition.click()
        expect(condition).to_have_attribute("aria-pressed", "false")
        page.get_by_label("Show connections").select_option("disease")
        assert page.locator(".med-graph__node--sideeffect").count() == 0
        page.get_by_label("Show connections").select_option("all")
        page.get_by_role("button", name="Next connections").click()
        expect(page.locator(".med-graph__footer")).to_contain_text("Showing 11")
        page.get_by_role("button", name="Previous", exact=True).click()
        Path("artifacts").mkdir(exist_ok=True)
        page.screenshot(path="artifacts/drug-reference-graph.png", full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        page.screenshot(path="artifacts/drug-reference-mobile.png", full_page=True)
        page.set_viewport_size({"width": 1440, "height": 1100})
        picker.select_option("Metformin")
        expect(page.get_by_role("button", name="Medicine: Metformin", exact=True)).to_be_visible(timeout=20000)
        expect(page.locator(".reference-details h2")).to_have_text("Metformin")
        page.route(re.compile(r"/interaction\?"), lambda route: route.fulfill(json={"status": "not_found"}))
        page.goto("http://localhost:5173/drug-interaction")
        page.get_by_label("Medicine 1", exact=True).select_option("Celecoxib")
        page.get_by_label("Medicine 2", exact=True).select_option("Metformin")
        page.get_by_role("button", name="Check Interaction", exact=True).click()
        expect(page.get_by_role("button", name="Medicine: Celecoxib", exact=True)).to_be_visible(timeout=20000)
        expect(page.get_by_role("button", name="Medicine: Metformin", exact=True)).to_be_visible()
        assert page.locator(".med-graph__edge--interaction").count() == 0
        page.screenshot(path="artifacts/interaction-graph.png", full_page=True)
        page.get_by_label("Medicine 2", exact=True).select_option("Ibuprofen")
        expect(page.locator(".med-graph")).to_have_count(0)
        page.goto("http://localhost:5173/doctor-dashboard")
        expect(page.get_by_label("Graph medicine")).to_have_value("Acarbose", timeout=20000)
        assert page.locator(".med-graph__node").count() <= 11
        page.get_by_label("Graph medicine").select_option("Celecoxib")
        expect(page.get_by_role("button", name="Medicine: Celecoxib", exact=True)).to_be_visible()
        page.screenshot(path="artifacts/dashboard-graph.png", full_page=True)
        assert not errors, errors
        browser.close()
    print("PASS: real focused graphs, dropdown selection, filters, pagination, node details, mobile containment, pair view and dashboard.")


if __name__ == "__main__":
    main()
