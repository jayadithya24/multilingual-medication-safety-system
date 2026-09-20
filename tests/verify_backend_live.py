"""Verify local patient APIs using disposable records; never print credentials.

Run with the backend listening on 127.0.0.1:8000.
The synthetic token verifies storage only, not Firebase delivery.
"""
import json
import secrets
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.database import db


def main():
    base = "http://127.0.0.1:8000"
    username = f"verification-{secrets.token_hex(8)}@example.invalid"
    password = secrets.token_urlsafe(24)
    results = {}

    def call(method, path, **kwargs):
        response = requests.request(method, base + path, timeout=20, **kwargs)
        results[f"{method} {path}"] = response.status_code
        return response

    try:
        assert call("GET", "/health").status_code == 200
        schema = call("GET", "/openapi.json").json()
        results["fcm_routes"] = {
            path: list(operations) for path, operations in schema["paths"].items()
            if "fcm" in path
        }
        response = call("POST", "/auth/register", json={
            "name": "Disposable verification patient", "email": username,
            "password": password, "confirm_password": password,
        })
        assert response.status_code == 200
        response = call("POST", "/auth/token", data={"username": username, "password": password})
        assert response.status_code == 200
        headers = {"Authorization": "Bearer " + response.json()["access_token"]}
        assert call("GET", "/auth/me", headers=headers).status_code == 200
        profile_response = call("GET", "/patient/profile", headers=headers)
        assert "hashed_password" not in profile_response.json()["profile"]
        results["profile_hash_excluded"] = True
        from playwright.sync_api import sync_playwright, expect
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            page.goto("http://localhost:5173/public")
            page.get_by_role("button", name="Login", exact=True).click()
            page.get_by_label("Email or username", exact=True).fill(username)
            page.get_by_label("Password", exact=True).fill(password)
            page.get_by_label("Password", exact=True).press("Enter")
            expect(page).to_have_url("http://localhost:5173/patient-dashboard")
            results["browser_password_login"] = True
            page.get_by_role("link", name="My Profile", exact=True).click()
            expect(page.get_by_label("Full Name", exact=True)).to_have_value("Disposable verification patient")
            page.get_by_label("Age", exact=True).fill("45")
            page.locator('select[name="gender"]').select_option("Other")
            page.locator('select[name="condition"]').select_option("Hypertension")
            page.get_by_label("Age", exact=True).fill("45")
            expect(page.get_by_label("Age", exact=True)).to_have_value("45")
            page.get_by_role("button", name="Save Profile", exact=True).click()
            expect(page.locator(".patient-profile__saved")).to_be_visible()
            assert db.users.find_one({"username": username})["age"] == 45
            results["browser_profile_persisted"] = True
            page.get_by_role("link", name="Scan & Add Medicines", exact=True).click()
            page.get_by_placeholder("e.g. Metformin").fill("Integration verification only")
            page.get_by_placeholder("e.g. 500 mg").fill("Test only")
            page.locator(".prescription-switch").click()
            page.get_by_role("button", name="Add to Schedule", exact=True).click()
            expect(page.locator(".prescription-success")).to_be_visible()
            assert db.patient_schedules.count_documents({"patient_username": username}) == 1
            results["browser_schedule_persisted"] = True
            page.get_by_role("link", name="My Medicines", exact=True).click()
            expect(page.get_by_text("Integration verification only", exact=True).first).to_be_visible()
            page.get_by_role("button", name="Mark as Taken").click()
            expect(page.get_by_role("button", name="Taken", exact=False).first).to_be_visible()
            assert db.medication_history.count_documents({"patient_username": username}) == 1
            results["browser_taken_persisted"] = True
            page.on("dialog", lambda dialog: dialog.accept())
            page.get_by_role("button", name="Remove from schedule", exact=True).click()
            expect(page.get_by_role("button", name="Remove from schedule", exact=True)).to_have_count(0)
            assert db.patient_schedules.count_documents({"patient_username": username, "status": "active"}) == 0
            assert db.medication_history.count_documents({"patient_username": username}) == 1
            results["browser_removal_preserves_history"] = True
            page.get_by_role("button", name="Sign out", exact=True).click()
            expect(page).to_have_url("http://localhost:5173/public")
            assert page.evaluate("localStorage.getItem('mmss_token')") is None
            results["browser_signout"] = True
            browser.close()
        token = "synthetic-verification-not-a-real-fcm-token-" + secrets.token_hex(16)
        assert call("POST", "/patient/fcm-token", headers=headers,
                    json={"token": token}).status_code == 200
        results["synthetic_token_stored"] = db.fcm_tokens.count_documents({
            "patient_username": username, "token": token,
        }) == 1
        response = call("POST", "/patient-schedule", headers=headers, json={
            "medicine_name": "Verification only", "dosage": "Verification only",
            "frequency": "daily", "scheduled_times": ["12:00"],
            "reminder_enabled": False,
        })
        assert response.status_code == 200
        schedule_id = response.json()["schedule"]["schedule_id"]
        assert call("POST", f"/patient-schedule/{schedule_id}/taken", headers=headers).status_code == 200
        results["history_stored"] = db.medication_history.count_documents({"patient_username": username}) == 2
        response = call("POST", "/patient/fcm-test", headers=headers)
        results["test_notification_delivered"] = False
        results["test_notification_missing_credentials"] = (
            response.status_code == 503 and
            response.json().get("detail") == "Firebase Admin credentials are not configured"
        )
    finally:
        for collection in ("fcm_tokens", "patient_schedules", "medication_history"):
            db[collection].delete_many({"patient_username": username})
        db.users.delete_one({"username": username})
        results["disposable_records_cleaned"] = True
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
