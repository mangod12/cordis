"""Playwright e2e tests for Cordis dashboard."""
import re

import pytest
from playwright.sync_api import Page, expect


class TestDashboardLoads:
    def test_page_title(self, authenticated_page: Page):
        """Dashboard page should have correct title."""
        expect(authenticated_page).to_have_title("Cordis Dispatch Dashboard")

    def test_header_visible(self, authenticated_page: Page):
        """Cordis header should be visible."""
        header = authenticated_page.locator("h1")
        expect(header).to_have_text("Cordis")

    def test_system_status_active(self, authenticated_page: Page):
        """System status indicator should show Active."""
        status = authenticated_page.locator("#system-status")
        expect(status).to_contain_text("System Active")

    def test_stats_cards_visible(self, authenticated_page: Page):
        """All 5 stat cards should be visible."""
        expect(authenticated_page.locator("#stat-total")).to_be_visible()
        expect(authenticated_page.locator("#stat-critical")).to_be_visible()
        expect(authenticated_page.locator("#stat-high")).to_be_visible()
        expect(authenticated_page.locator("#stat-latency")).to_be_visible()
        expect(authenticated_page.locator("#stat-fallback")).to_be_visible()


class TestCrisisMap:
    def test_map_container_visible(self, authenticated_page: Page):
        """Leaflet map should be rendered."""
        map_div = authenticated_page.locator("#map")
        expect(map_div).to_be_visible()

    def test_map_has_expected_dimensions(self, authenticated_page: Page):
        """Map container should have non-zero height (ready for Leaflet)."""
        map_box = authenticated_page.locator("#map").bounding_box()
        assert map_box is not None, "Map element has no bounding box"
        assert map_box["height"] > 0, "Map height should be > 0"
        assert map_box["width"] > 0, "Map width should be > 0"


class TestEmergencyInput:
    def test_transcript_input_visible(self, authenticated_page: Page):
        """Text input area should be visible."""
        textarea = authenticated_page.locator("#transcript-input")
        expect(textarea).to_be_visible()

    def test_audio_input_visible(self, authenticated_page: Page):
        """Audio upload input should be visible."""
        audio = authenticated_page.locator("#audio-input")
        expect(audio).to_be_visible()

    def test_submit_button_visible(self, authenticated_page: Page):
        """Submit button should be visible and enabled."""
        btn = authenticated_page.locator("#submit-btn")
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        expect(btn).to_have_text("Process Emergency")

    def test_submit_empty_shows_alert(self, authenticated_page: Page):
        """Submitting with no input should show alert."""
        authenticated_page.on("dialog", lambda dialog: dialog.accept())
        authenticated_page.locator("#submit-btn").click()
        # After alert, button should still be enabled
        expect(authenticated_page.locator("#submit-btn")).to_be_enabled()


class TestAgentPipeline:
    def test_pipeline_hidden_initially(self, authenticated_page: Page):
        """Pipeline visualization should have the 'hidden' class before submission."""
        pipeline = authenticated_page.locator("#pipeline-viz")
        expect(pipeline).to_have_class(re.compile(r"\bhidden\b"))

    def test_pipeline_steps_exist(self, authenticated_page: Page):
        """All 5 pipeline step elements should exist in DOM."""
        for step in ["stt", "intent", "emotion", "severity", "dispatch"]:
            expect(authenticated_page.locator(f"#step-{step}")).to_be_attached()


class TestCallsTable:
    def test_table_visible(self, authenticated_page: Page):
        """Calls table should be visible."""
        table = authenticated_page.locator("table")
        expect(table).to_be_visible()

    def test_table_headers(self, authenticated_page: Page):
        """Table should have correct column headers."""
        headers = authenticated_page.locator("thead th")
        expect(headers).to_have_count(7)

    def test_empty_state(self, authenticated_page: Page):
        """Empty table should show waiting message."""
        body = authenticated_page.locator("#calls-body")
        expect(body).to_contain_text("Waiting for calls")


class TestResponsiveLayout:
    def test_mobile_layout(self, authenticated_page: Page):
        """Dashboard should work at mobile width."""
        authenticated_page.set_viewport_size({"width": 375, "height": 812})
        expect(authenticated_page.locator("h1")).to_be_visible()
        expect(authenticated_page.locator("#map")).to_be_visible()
        expect(authenticated_page.locator("#submit-btn")).to_be_visible()

    def test_desktop_layout(self, authenticated_page: Page):
        """Dashboard should work at desktop width."""
        authenticated_page.set_viewport_size({"width": 1920, "height": 1080})
        expect(authenticated_page.locator("h1")).to_be_visible()
        expect(authenticated_page.locator("#map")).to_be_visible()

    def test_screenshot(self, authenticated_page: Page):
        """Take a screenshot for visual verification."""
        authenticated_page.set_viewport_size({"width": 1400, "height": 900})
        authenticated_page.screenshot(path="D:/Cordis/docs/dashboard-screenshot.png", full_page=True)
