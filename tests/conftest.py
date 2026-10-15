"""Ensure test collection never connects to the application's MongoDB."""
import os

os.environ["USE_MONGOMOCK"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["MONGO_DB"] = "mmss_test"
os.environ["JWT_SECRET_KEY"] = "isolated-test-secret-not-for-production-123456"
os.environ["WARM_UP_OCR"] = "false"
