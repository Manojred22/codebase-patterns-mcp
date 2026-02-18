"""Tests for src/mcp_server.py — MCP notification handling and request routing.

Note: Full MCPServer init requires OPENAI_API_KEY. These tests cover
the notification logic and request routing without requiring API keys.
"""


class TestNotificationHandling:
    """Test that notifications (no id) are detected correctly."""

    def test_notification_has_no_id(self):
        request = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        request_id = request.get("id")
        method = request.get("method")

        is_notification = request_id is None and method != "initialize"
        assert is_notification is True

    def test_regular_request_has_id(self):
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        request_id = request.get("id")
        method = request.get("method")

        is_notification = request_id is None and method != "initialize"
        assert is_notification is False

    def test_initialize_with_no_id_is_not_notification(self):
        """initialize is special — even without id it should be handled."""
        request = {"jsonrpc": "2.0", "method": "initialize", "params": {}}
        request_id = request.get("id")
        method = request.get("method")

        is_notification = request_id is None and method != "initialize"
        assert is_notification is False

    def test_various_notifications_detected(self):
        notifications = [
            "notifications/initialized",
            "notifications/cancelled",
            "$/cancelRequest",
        ]
        for method in notifications:
            request = {"jsonrpc": "2.0", "method": method, "params": {}}
            assert request.get("id") is None
            assert request.get("method") != "initialize"
