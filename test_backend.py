import requests

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("\n🔍 --- STARTING FASTAPI BACKEND VERIFICATION ---\n")

    # 1. Health Check
    try:
        r = requests.get(f"{BASE_URL}/docs")
        if r.status_code == 200:
            print("✅ Server is running and Swagger docs are accessible.")
        else:
            print(f"❌ Server returned status code: {r.status_code}")
    except Exception as e:
        print(f"❌ Could not connect to server. Is FastAPI running? Error: {e}")
        return

    test_cases = [
        {
            "name": "TEST 1: Safe Tablet (GREEN Status) - Metformin",
            "params": {"patient_id": "P101", "scanned_medicine": "Metformin", "lang": "kn", "return_audio": False},
            "expected_status": "GREEN"
        },
        {
            "name": "TEST 2: Already Taken Tablet (YELLOW Status)",
            "params": {"patient_id": "P101", "scanned_medicine": "Metformin", "lang": "kn", "return_audio": False},
            "expected_status": "YELLOW"
        },
        {
            "name": "TEST 3: Wrong Time Slot Tablet (RED Status + Caretaker Alert)",
            "params": {"patient_id": "P101", "scanned_medicine": "Amlodipine", "lang": "tlu", "return_audio": False},
            "expected_status": "RED"
        },
        {
            "name": "TEST 4: Unprescribed Tablet (RED Status + Caretaker Alert)",
            "params": {"patient_id": "P101", "scanned_medicine": "Crocin", "lang": "en", "return_audio": False},
            "expected_status": "RED"
        },
        {
            "name": "TEST 5: Audio Stream Response (MP3 Voice Output)",
            "params": {"patient_id": "P101", "scanned_medicine": "Metformin", "lang": "kn", "return_audio": True},
            "check_audio": True
        }
    ]

    for test in test_cases:
        print(f"\n--------------------------------------------------")
        print(f"▶ Running {test['name']}")
        
        response = requests.post(f"{BASE_URL}/patient/verify-and-speak", params=test['params'])

        if test.get("check_audio"):
            content_type = response.headers.get("content-type", "")
            if response.status_code == 200 and "audio/mpeg" in content_type:
                status_hdr = response.headers.get("X-Status-Code")
                print(f"✅ Audio stream received! (Header Status: {status_hdr}, Bytes: {len(response.content)})")
            else:
                print(f"❌ Failed to retrieve audio. Content-Type: {content_type}")
        else:
            data = response.json()
            actual_status = data.get("status_code")
            print(f"Response Payload: {data}")
            
            if actual_status == test["expected_status"]:
                print(f"✅ PASSED (Status Code: {actual_status})")
            else:
                print(f"❌ FAILED (Expected {test['expected_status']}, got {actual_status})")

    print("\n🎉 --- ALL TESTS COMPLETED ---\n")

if __name__ == "__main__":
    run_tests()