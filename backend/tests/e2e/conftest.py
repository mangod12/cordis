"""Playwright e2e test configuration."""
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from playwright.sync_api import Page

SECRET_KEY = "d7B2UWU6CdxxDHsQU0mm3hoZ3ogHbrJ7PwXw58MthNQ"
ALGORITHM = "HS256"


@pytest.fixture(scope="session")
def jwt_token():
    """Generate a valid JWT token for e2e tests."""
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "exp": expire,
        "sub": "e2e-test",
        "tenant_id": "demo",
        "role": "admin",
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def authenticated_page(page: Page, jwt_token: str):
    """Navigate to dashboard with JWT token pre-set."""
    # Set Authorization header for server-side JWT check
    page.set_extra_http_headers({"Authorization": f"Bearer {jwt_token}"})

    # Handle the localStorage prompt dialog by providing the token
    def handle_dialog(dialog):
        dialog.accept(jwt_token)

    page.on("dialog", handle_dialog)

    page.goto("http://localhost:8000/dashboard")
    page.wait_for_load_state("networkidle")
    return page
