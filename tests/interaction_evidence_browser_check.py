"""Real interaction/graph APIs; only the browser's doctor identity is stubbed."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.add_init_script("localStorage.setItem('mmss_token','ui-test'); localStorage.setItem('mmss_role','doctor');")
        page.route("**/auth/me", lambda route: route.fulfill(json={"username": "interaction.test@example.invalid", "full_name": "Test Doctor", "role": "doctor"}))
        page.goto("http://localhost:5173/drug-interaction")
        Path("artifacts").mkdir(exist_ok=True)
        examples = [
            ("Acarbose", "Chlorthalidone", "Not graded", "blood glucose"),
            ("Atenolol", "Clonidine", "Mild", "stopped abruptly"),
            ("Naproxen", "Methotrexate", "Moderate", "toxicity"),
            ("Diclofenac", "Methotrexate", "Severe", "toxicity"),
            ("Ibuprofen", "Losartan", "Moderate", "Kidney"),
            ("Telmisartan", "Ramipril", "Review required", "kidney dysfunction"),
        ]
        for first, second, severity, effect in examples:
            page.get_by_label("Medicine 1", exact=True).select_option(first)
            page.get_by_label("Medicine 2", exact=True).select_option(second)
            page.get_by_role("button", name="Check Interaction", exact=True).click()
            card = page.locator(".interaction-card")
            expect(card.locator("h2")).to_have_text(severity, timeout=20000)
            expect(card).to_contain_text(effect)
            assert card.get_by_role("link").count() >= 1
            expect(page.locator(".med-graph__source").first).to_contain_text("Neo4j database", timeout=20000)
            expect(page.locator(".med-graph__edge--interaction")).to_have_count(1)
            page.screenshot(path=f"artifacts/interaction-{first.lower()}-{second.lower()}.png", full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        page.get_by_label("Medicine 1", exact=True).select_option("Acarbose")
        page.get_by_label("Medicine 2", exact=True).select_option("Metformin")
        page.get_by_role("button", name="Check Interaction", exact=True).click()
        expect(page.locator(".interaction-card")).to_contain_text("No interaction record found", timeout=20000)
        expect(page.locator(".med-graph__source").first).to_contain_text("Neo4j database", timeout=20000)
        expect(page.locator(".med-graph__edge--interaction")).to_have_count(0)
        assert not errors, errors
        browser.close()
    print("PASS: live effects, citations, severity provenance, Neo4j pair edges, unknown pair and mobile layout.")


if __name__ == "__main__":
    main()
