from pathlib import Path
import os
import json


def load_project_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    lines = env_path.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            index += 1
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # Service-account JSON is commonly pasted as a multiline object.
        # Consume its continuation lines before storing the environment value.
        if key == "FIREBASE_SERVICE_ACCOUNT_JSON" and value.startswith("{"):
            json_parts = [value]
            while index + 1 < len(lines):
                candidate = "\n".join(json_parts)
                try:
                    json.loads(candidate)
                    break
                except json.JSONDecodeError:
                    index += 1
                    json_parts.append(lines[index].strip())
            value = "\n".join(json_parts)

        if key and key not in os.environ:
            os.environ[key] = value
        index += 1
