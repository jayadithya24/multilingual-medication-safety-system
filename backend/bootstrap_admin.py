"""Create or reset the local administrator account in MongoDB.

Usage:
    python -m backend.bootstrap_admin --username admin123 --password jay

The password is supplied at invocation time and is never stored in this file.
"""

import argparse
import getpass

from backend.app.auth import get_password_hash
from backend.app.database import users_collection


def bootstrap_admin(username: str, password: str) -> None:
    normalized_username = username.strip().lower()
    if not normalized_username or not password:
        raise ValueError("Username and password are required")

    users_collection.update_one(
        {"username": normalized_username},
        {
            "$set": {
                "username": normalized_username,
                "email": normalized_username,
                "role": "admin",
                "full_name": "System Administrator",
                "hashed_password": get_password_hash(password),
                "disabled": False,
            },
            "$setOnInsert": {"admin_bootstrapped": True},
        },
        upsert=True,
    )
    print(f"Admin account ready: {normalized_username}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="admin123")
    parser.add_argument("--password")
    args = parser.parse_args()
    password = args.password or getpass.getpass("Admin password: ")
    bootstrap_admin(args.username, password)


if __name__ == "__main__":
    main()
