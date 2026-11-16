"""Read-only login connectivity checks; never prints credentials or user records."""
import json
import os
from pathlib import Path
import socket
import sys
from time import perf_counter
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.env_loader import load_project_env


def main():
    load_project_env()
    report = {}
    for port in (8000, 5173):
        listeners = []
        for family, address in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
            try:
                with socket.socket(family, socket.SOCK_STREAM) as connection:
                    connection.settimeout(2)
                    if connection.connect_ex((address, port)) == 0:
                        listeners.append(address)
            except OSError:
                pass
        report[f"localhost_{port}"] = (
            "listening on " + ", ".join(listeners) if listeners else "not listening"
        )
    try:
        with urlopen("http://127.0.0.1:8000/health", timeout=5) as response:
            report["backend_health_http"] = response.status
    except Exception as error:
        report["backend_health_error"] = type(error).__name__
    report["jwt_secret_configured"] = len(os.getenv("JWT_SECRET_KEY", "")) >= 32
    report["ocr_startup_warmup"] = os.getenv("WARM_UP_OCR", "true").lower() == "true"
    uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
    report["mongo_configured"] = bool(uri)
    report["mongo_uses_srv_dns"] = bool(uri and uri.startswith("mongodb+srv://"))
    if uri:
        from pymongo import MongoClient
        started = perf_counter()
        client = None
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000,
                                 socketTimeoutMS=5000)
            client.admin.command("ping")
            report["mongo_ping"] = "ok"
        except Exception as error:
            report["mongo_ping"] = "failed"
            report["mongo_error"] = type(error).__name__
            # Classify without exposing connection strings, hosts, or credentials.
            message = str(error).lower()
            report["mongo_error_signals"] = [
                label for label, marker in (
                    ("dns", "dns"), ("timeout", "timed out"),
                    ("tls", "ssl"), ("authentication", "authentication failed"),
                    ("connection refused", "refused"),
                ) if marker in message
            ]
        finally:
            if client is not None:
                client.close()
        report["mongo_check_seconds"] = round(perf_counter() - started, 2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
