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
        test_time = datetime(2026, 11, 16, 13, 2, 45)
        asyncio.run(send_alert(
            text="computer vision algorithm engineer pytorch tel aviv",
            channel="@secretmachinelearningjobs",
            sender="Recruiter",
            timestamp=test_time,
            llm_result="relevant"
        ))

        # Get the printed output
        output = self.captured_output.getvalue()

        # Verify the alert contains expected fields
        self.assertIn("[ALERT] Relevant job in @secretmachinelearningjobs, posted 16.11 13:02", output)
        self.assertIn("Sender: Recruiter", output)
        self.assertIn("Message: computer vision algorithm engineer pytorch tel aviv", output)
        self.assertNotIn("Offer", output)

    def test_send_alert_borderline_label(self):
        """
        Test that the borderline label is shown in the headline.
        """
        test_time = datetime(2026, 1, 5, 9, 7, 0)
        asyncio.run(send_alert(
            text="Some message",
            channel="test_channel",
            sender="test_sender",
            timestamp=test_time,
            llm_result="borderline"
        ))

        output = self.captured_output.getvalue()

        self.assertIn("[ALERT] Borderline job in test_channel, posted 05.01 09:07", output)

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

        self.assertIn("[ALERT] Matching job in test_channel, posted 10.02 15:45", output)


if __name__ == '__main__':
    unittest.main()
