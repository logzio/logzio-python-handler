"""
E2E Integration Tests for logzio-python-handler

Sends logs using the handler and validates they arrive via Logz.io API.

Required Environment Variables:
    LOGZIO_TOKEN: Shipping token for sending logs
    LOGZIO_LOGS_API_KEY: API token for querying logs
    ENV_ID: Unique identifier for this test run
"""

import json
import logging
import os
import time
import requests
import pytest

from logzio.handler import LogzioHandler

# Logz.io API URL
BASE_LOGZIO_API_URL = os.getenv("LOGZIO_API_URL", "https://api.logz.io/v1")


def get_env_or_skip(var_name: str) -> str:
    """Get environment variable or skip test if not set."""
    value = os.environ.get(var_name)
    if not value:
        pytest.skip(f"Environment variable {var_name} is not set")
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

    logger = logging.getLogger(f"e2e-test-{env_id}")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    logger.addHandler(handler)

    logger.info(message, extra={"env_id": env_id, "test_source": "python-handler-e2e"})

    # Flush to ensure log is sent
    handler.flush()
    time.sleep(3)  # Wait for log to be processed


class TestLogzioLogs:
    """E2E tests for logzio-python-handler."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.token = get_env_or_skip("LOGZIO_TOKEN")
        self.api_key = get_env_or_skip("LOGZIO_LOGS_API_KEY")
        self.env_id = get_env_or_skip("ENV_ID")

    def test_logs_received(self):
        """Test that logs are received and have required fields."""
        # Send a test log
        test_message = f"E2E test message from python handler - {self.env_id}"
        send_test_log(self.token, self.env_id, test_message)

        # Wait for ingestion
        print("Waiting for log ingestion...")
        time.sleep(30)

        # Query logs
        query = f"env_id:{self.env_id} AND type:{self.env_id}"
        response = fetch_logs(self.api_key, query)

        total = response.get("hits", {}).get("total", 0)
        if total == 0:
            pytest.fail("No logs found")

        hits = response.get("hits", {}).get("hits", [])
        for hit in hits:
            source = hit.get("_source", {})

            # Verify required fields are present
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

        # Wait for ingestion
        print("Waiting for log ingestion...")
        time.sleep(30)

        # Query for specific message
        query = f"env_id:{self.env_id} AND message:*Content*validation*"
        response = fetch_logs(self.api_key, query)

        total = response.get("hits", {}).get("total", 0)
        if total == 0:
            pytest.fail("Test log not found")

        # Verify the message content
        hit = response["hits"]["hits"][0]["_source"]
        assert "Content validation test" in hit.get("message", ""), "Message content mismatch"
        assert hit.get("env_id") == self.env_id, "env_id mismatch"
        assert hit.get("test_source") == "python-handler-e2e", "test_source mismatch"

        print("✅ Log content matches expected values")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
