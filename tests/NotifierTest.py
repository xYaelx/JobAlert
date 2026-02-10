import unittest
import asyncio
from datetime import datetime
from io import StringIO
import sys
from notifier import send_alert


class TestNotifierFunctions(unittest.TestCase):
    def setUp(self):
        """
        Set up before each test: capture stdout.
        """
        self.captured_output = StringIO()
        self.original_stdout = sys.stdout
        sys.stdout = self.captured_output

    def tearDown(self):
        """
        Restore stdout after each test.
        """
        sys.stdout = self.original_stdout

    def test_send_alert_prints_correctly(self):
        """
        Test that send_alert prints the alert message with correct format.
        """
        # Run the async function
        test_time = datetime(2026, 2, 10, 12, 30, 45)
        asyncio.run(send_alert(
            text="גוּנָל F-75 עם מחט",
            channel="קבוצת מסירה",
            sender="יוסי כהן",
            timestamp=test_time,
            llm_result="offer"
        ))

        # Get the printed output
        output = self.captured_output.getvalue()

        # Verify the alert contains expected fields
        self.assertIn("[ALERT] Offer detected!", output)
        self.assertIn("Channel: קבוצת מסירה", output)
        self.assertIn("Sender: יוסי כהן", output)
        self.assertIn("Time (UTC): 2026-02-10 12:30:45", output)
        self.assertIn("Message: גוּנָל F-75 עם מחט", output)
        self.assertIn("LLM Result: offer", output)

    def test_send_alert_with_none_llm_result(self):
        """
        Test that send_alert works with None llm_result.
        """
        test_time = datetime(2026, 2, 10, 15, 45, 30)
        asyncio.run(send_alert(
            text="Some message",
            channel="test_channel",
            sender="test_sender",
            timestamp=test_time,
            llm_result=None
        ))

        output = self.captured_output.getvalue()

        self.assertIn("[ALERT] Offer detected!", output)
        self.assertIn("LLM Result: None", output)


if __name__ == '__main__':
    unittest.main()
