"""
E2E Integration Tests for logzio-python-handler

Sends logs using the handler and validates they arrive via Logz.io API.

Required Environment Variables:
    LOGZIO_TOKEN: Shipping token for sending logs
    LOGZIO_API_KEY: API token for querying logs
    ENV_ID: Unique identifier for this test run
"""

import atexit
import json
import logging
import os
import re
import time
import requests
import pytest

from logzio.handler import LogzioHandler

BASE_LOGZIO_API_URL = os.getenv("LOGZIO_API_URL", "https://api.logz.io/v1")

# Track handlers to close them properly at exit
_handlers_to_close = []


def _cleanup_handlers():
    """Close all handlers at exit to prevent logging errors."""
    for handler in _handlers_to_close:
        try:
            handler.close()
        except Exception:
            pass


atexit.register(_cleanup_handlers)


def get_env_or_fail(var_name: str) -> str:
    """Get environment variable or fail test if not set."""
    value = os.environ.get(var_name)
    if not value:
        pytest.fail(f"Required environment variable {var_name} is not set. Configure GitHub secret.")
    return value


def format_query(query: str) -> str:
    """Format query for Logz.io search API."""
    return json.dumps({
        "query": {
            "query_string": {
                "query": query
            }
        },
        "from": 0,
        "size": 100,
        "sort": [{"@timestamp": {"order": "desc"}}]
    })


def fetch_logs(api_key: str, query: str):
    """Fetch logs from Logz.io API."""
    url = f"{BASE_LOGZIO_API_URL}/search"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-API-TOKEN": api_key
    }

    print(f"Sending API request to {url}")
    print(f"Query: {query}")

    response = requests.post(
        url,
        headers=headers,
        data=format_query(query),
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(f"Unexpected status code: {response.status_code}, body: {response.text}")

    return response.json()


def send_test_log(token: str, env_id: str, message: str):
    """Send a test log using the logzio handler."""
    handler = LogzioHandler(
        token=token,
        logzio_type=env_id,
        logs_drain_timeout=2,
        debug=True,
        backup_logs=False
    )
    _handlers_to_close.append(handler)

    logger = logging.getLogger(f"e2e-test-{env_id}")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    logger.addHandler(handler)

    logger.info(message, extra={"env_id": env_id, "test_source": "python-handler-e2e"})

    handler.flush()
    time.sleep(3)


class TestLogzioLogs:
    """E2E tests for logzio-python-handler."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.token = get_env_or_fail("LOGZIO_TOKEN")
        self.api_key = get_env_or_fail("LOGZIO_API_KEY")
        self.env_id = get_env_or_fail("ENV_ID")

    def test_logs_received(self):
        """Test that logs are received and have required fields."""
        test_message = f"E2E test message from python handler - {self.env_id}"
        send_test_log(self.token, self.env_id, test_message)

        print("Waiting for log ingestion...")
        time.sleep(240)

        query = f"env_id:{self.env_id} AND type:{self.env_id}"
        response = fetch_logs(self.api_key, query)

        total = response.get("hits", {}).get("total", 0)
        if total == 0:
            pytest.fail("No logs found")

        hits = response.get("hits", {}).get("hits", [])
        for hit in hits:
            source = hit.get("_source", {})

            required_fields = ["message", "logger", "log_level", "type", "@timestamp"]
            missing_fields = [f for f in required_fields if not source.get(f)]

            if missing_fields:
                print(f"Log missing fields: {missing_fields}")
                print(f"Log content: {json.dumps(source, indent=2)}")
                pytest.fail(f"Missing required log fields: {missing_fields}")

        print(f"✅ Found {total} logs with all required fields")

    def test_log_content_matches(self):
        """Test that log content matches what was sent."""
        test_message = f"Content validation test - {self.env_id}"
        send_test_log(self.token, self.env_id, test_message)

        print("Waiting for log ingestion...")
        time.sleep(240)

        query = f"env_id:{self.env_id}"
        response = fetch_logs(self.api_key, query)

        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            pytest.fail("No logs found for env_id")

        # Find the log with matching message using regex
        pattern = re.compile(r"Content\s+validation\s+test")
        matching_log = None
        for hit in hits:
            source = hit.get("_source", {})
            message = source.get("message", "")
            if pattern.search(message):
                matching_log = source
                break

        if not matching_log:
            print("Available logs:")
            for hit in hits[:5]:
                print(f"  - {hit.get('_source', {}).get('message', 'N/A')}")
            pytest.fail("Test log with 'Content validation test' not found in message field")

        assert matching_log.get("env_id") == self.env_id, "env_id mismatch"
        assert matching_log.get("test_source") == "python-handler-e2e", "test_source mismatch"

        print("✅ Log content matches expected values")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
