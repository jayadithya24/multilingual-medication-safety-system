"""Ensure test collection never connects to the application's MongoDB."""
import os

os.environ["USE_MONGOMOCK"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["MONGO_DB"] = "mmss_test"
os.environ["JWT_SECRET_KEY"] = "isolated-test-secret-not-for-production-123456"
os.environ["WARM_UP_OCR"] = "false"

import pytest


@pytest.fixture(autouse=True)
def isolated_application_rate_windows():
    """Test cases share an imported app, but must not share a simulated hour's quota.

    Limits remain enabled within each case, including cross-client/worker tests.
    """
    from backend.main import app
    from backend.app.request_limits import RequestLimits
    layer = app.middleware_stack
    while layer is not None:
        if isinstance(layer, RequestLimits):
            layer.windows.clear()
        layer = getattr(layer, 'app', None)
