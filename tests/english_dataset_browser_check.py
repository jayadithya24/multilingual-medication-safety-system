"""Exercise English frontend searches against real CSV-backed API routes.

Start Vite on 5173, then run this script with Playwright, uvicorn and backend
dataset dependencies installed. Account and speech endpoints are stubbed;
medicine searches and disease lists use the real FastAPI routes and services.
No database or patient records are written.
"""
import csv
import json
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import uvicorn
from fastapi import FastAPI
from playwright.sync_api import sync_playwright, expect
from backend.app.routes.medicine import router as medicine_router
from backend.app.routes.neo4j import router as graph_router
from backend.app.services import neo4j_service


def main():
    def offline():
        raise RuntimeError("English dataset test uses local CSVs only")

    neo4j_service._get_driver = offline
    app = FastAPI()
    app.include_router(medicine_router)
    app.include_router(graph_router)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8017, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("Dataset test API did not start")
        time.sleep(.05)
    records = list(csv.DictReader((ROOT / "datasets/english_master_dataset.csv").open(encoding="utf-8-sig")))
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            page.add_init_script("localStorage.setItem('mmss_token','dataset-test'); localStorage.setItem('mmss_role','patient');")
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            def api(route):
                parsed = urlsplit(route.request.url)
                if route.request.resource_type not in ("xhr", "fetch", "media"):
                    route.continue_()
                elif parsed.path.startswith(("/medicines", "/medicine/", "/neo4j/")):
                    response = route.fetch(url="http://127.0.0.1:8017" + parsed.path + ("?" + parsed.query if parsed.query else ""))
                    route.fulfill(response=response)
                elif parsed.path == "/tts":
                    route.fulfill(status=200, content_type="audio/mpeg", body=b"")
                elif parsed.path.startswith(("/patient", "/auth", "/fcm")):
                    route.fulfill(status=200, content_type="application/json", body="{}")
                else:
                    route.continue_()

            page.route("**/*", api)
            page.goto("http://localhost:5173/patient-dashboard")
            expect(page.locator("#patient-medicine-options option")).to_have_count(100)
            search = page.get_by_placeholder("Search disease or drug")
            for record in records:
                search.fill(record["drug_name"])
                page.get_by_role("button", name="Search", exact=True).click()
                card = page.locator(".medicine-card")
                expect(card.get_by_role("heading", name=record["drug_name"], exact=True)).to_be_visible()
                expect(card).to_contain_text(record["description"])
                expect(card).to_contain_text(record["warnings"])
                expect(card).to_contain_text(record["disease"])
            for disease in sorted({row["disease"] for row in records}):
                search.fill(disease)
                page.get_by_role("button", name="Search", exact=True).click()
                expect(page.locator(".patient-result__diseases")).to_contain_text(disease)
            page.set_viewport_size({"width": 390, "height": 844})
            search.fill("Paracetamol")
            page.get_by_role("button", name="Search", exact=True).click()
            expect(page.locator(".medicine-card")).to_contain_text("Paracetamol")
            assert not errors, errors
            output = ROOT / "artifacts/english-dataset-browser"
            output.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output / "mobile.png"), full_page=True)
            page.set_viewport_size({"width": 1280, "height": 900})
            page.screenshot(path=str(output / "desktop.png"), full_page=True)
            report = {"english_medicine_searches": len(records), "disease_searches": 10,
                      "dropdown_options": 100, "page_errors": errors, "mobile": "passed",
                      "api": "real CSV-backed routes; account and speech endpoints stubbed"}
            (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps(report))
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
