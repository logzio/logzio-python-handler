import threading
import time
from unittest import TestCase
from unittest.mock import patch, MagicMock

from logzio.sender import LogzioSender


class TestThreadSafety(TestCase):
    """Tests for thread-safety fixes in LogzioSender.
    
    These tests verify that:
    1. queue.get() doesn't block indefinitely when queue becomes empty
    2. Concurrent flush calls from multiple threads work correctly
    3. The flush lock prevents race conditions
    """

    @patch('logzio.sender.requests.Session')
    def setUp(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.return_value.post.return_value = mock_response
        
        self.sender = LogzioSender(
            token='test-token',
            url='http://localhost:8080',
            logs_drain_timeout=1,
            debug=False,
            backup_logs=False
        )
        self.sender.sending_thread.join(timeout=0.1)

    def test_get_messages_does_not_block_on_empty_queue(self):
        """Test that _get_messages_up_to_max_allowed_size returns immediately on empty queue."""
        while not self.sender.queue.empty():
            self.sender.queue.get(block=False)
        
        start_time = time.time()
        result = self.sender._get_messages_up_to_max_allowed_size()
        elapsed = time.time() - start_time
        
        self.assertEqual(result, [])
        self.assertLess(elapsed, 0.1, "Method should return immediately, not block")

    def test_get_messages_returns_available_messages(self):
        """Test that _get_messages_up_to_max_allowed_size returns queued messages."""
        self.sender.queue.put('{"message": "test1"}')
        self.sender.queue.put('{"message": "test2"}')
        self.sender.queue.put('{"message": "test3"}')
        
        result = self.sender._get_messages_up_to_max_allowed_size()
        
        self.assertEqual(len(result), 3)
        self.assertIn('{"message": "test1"}', result)

    @patch('logzio.sender.requests.Session')
    def test_concurrent_flush_calls_are_thread_safe(self, mock_session):
        """Test that multiple threads can call flush() without race conditions."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.return_value.post.return_value = mock_response
        
        for i in range(100):
            self.sender.queue.put(f'{{"message": "test{i}"}}')
        
        errors = []
        
        def flush_worker():
            try:
                self.sender.flush()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=flush_worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        
        self.assertEqual(errors, [], f"Flush raised errors: {errors}")
        self.assertTrue(self.sender.queue.empty(), "Queue should be empty after flush")

    @patch('logzio.sender.requests.Session')
    def test_flush_completes_without_blocking(self, mock_session):
        """Test that flush() completes in reasonable time even with concurrent access."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.return_value.post.return_value = mock_response
        
        self.sender.queue.put('{"message": "test"}')
        
        start_time = time.time()
        self.sender.flush()
        elapsed = time.time() - start_time
        
        self.assertLess(elapsed, 5, "Flush should complete without blocking indefinitely")

    def test_flush_lock_exists(self):
        """Test that the sender has a flush lock for thread synchronization."""
        self.assertTrue(hasattr(self.sender, '_flush_lock'))
        self.assertIsInstance(self.sender._flush_lock, type(threading.Lock()))

    @patch('logzio.sender.requests.Session')
    def test_race_condition_empty_check_then_get(self, mock_session):
        """Test the specific race condition: empty() returns False but get() would block.
        
        This simulates the scenario where:
        1. Thread A checks queue.empty() -> False
        2. Thread B consumes the last item
        3. Thread A calls queue.get() -> would block forever without fix
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.return_value.post.return_value = mock_response
        
        results = {'completed': False, 'error': None}
        
        def consumer():
            try:
                time.sleep(0.05)
                while not self.sender.queue.empty():
                    try:
                        self.sender.queue.get(block=False)
                    except:
                        pass
            except Exception as e:
                results['error'] = e
        
        def flusher():
            try:
                self.sender.flush()
                results['completed'] = True
            except Exception as e:
                results['error'] = e
        
        self.sender.queue.put('{"message": "test"}')
        
        consumer_thread = threading.Thread(target=consumer)
        flusher_thread = threading.Thread(target=flusher)
        
        consumer_thread.start()
        flusher_thread.start()
        
        flusher_thread.join(timeout=5)
        consumer_thread.join(timeout=1)
        
        self.assertFalse(flusher_thread.is_alive(), 
                        "Flush should complete, not block indefinitely")
        self.assertIsNone(results['error'], f"Error occurred: {results['error']}")

