import unittest
import sqlite3
from datetime import datetime
from hashlib import sha256
from db import (
    get_connection,
    init_db,
    compute_message_hash,
    get_cached_message,
    touch_message,
    insert_message,
    cleanup_old_messages
)

class TestDatabaseFunctions(unittest.TestCase):
    def setUp(self):
        """
        Set up an in-memory SQLite database before each test.
        """
        self.conn = get_connection(":memory:")  # Use in-memory database for tests
        init_db(self.conn)

    def tearDown(self):
        """
        Close the database connection after each test.
        """
        self.conn.close()

    def test_init_db_creates_table(self):
        """
        Test that the database initializes the table correctly.
        """
        cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages_cache';")
        table = cursor.fetchone()
        self.assertIsNotNone(table, "The table 'messages_cache' was not created.")

    def test_compute_message_hash(self):
        """
        Test that the message hash function works as expected.
        """
        text = "This is a test message."
        expected_hash = sha256(text.encode('utf-8')).hexdigest()
        self.assertEqual(compute_message_hash(text), expected_hash)

    def test_insert_message(self):
        """
        Test inserting a message into the database.
        """
        message_text = "Test message for insertion."
        message_hash = compute_message_hash(message_text)
        extracted_json = '{"text": "Test message for insertion."}'

        # Insert the message
        insert_message(self.conn, message_hash, extracted_json)

        # Verify that the message can be retrieved
        cached_message = get_cached_message(self.conn, message_hash)
        self.assertIsNotNone(cached_message, "Message should have been inserted.")
        self.assertEqual(cached_message[1], extracted_json, "The extracted JSON should match the inserted value.")

    def test_touch_message(self):
        """
        Test the touch_message function updates the 'last_seen' timestamp.
        """
        message_text = "Message to be touched."
        message_hash = compute_message_hash(message_text)
        extracted_json = '{"text": "Message to be touched."}'

        # Insert the message
        insert_message(self.conn, message_hash, extracted_json)

        # Get the ID of the inserted message
        cached_message = get_cached_message(self.conn, message_hash)
        message_id = cached_message[0]

        # Get the original last_seen timestamp
        cursor = self.conn.execute("SELECT last_seen FROM messages_cache WHERE id = ?", (message_id,))
        original_last_seen = str(cursor.fetchone()[0])

        # Call touch_message to update last_seen
        touch_message(self.conn, message_id)

        # Verify that the last_seen timestamp has been updated
        cursor = self.conn.execute("SELECT last_seen FROM messages_cache WHERE id = ?", (message_id,))
        updated_last_seen = str(cursor.fetchone()[0])

        self.assertNotEqual(updated_last_seen, original_last_seen, "last_seen should be updated.")

    def test_cleanup_old_messages(self):
        """
        Test that the cleanup function deletes old messages.
        """
        # Insert a message with today's date
        message1_text = "Message 1"
        message1_hash = compute_message_hash(message1_text)
        message1_json = '{"text": "Message 1"}'
        insert_message(self.conn, message1_hash, message1_json)

        # Insert a message with a date 10 days ago
        message2_text = "Message 2"
        message2_hash = compute_message_hash(message2_text)
        message2_json = '{"text": "Message 2"}'
        insert_message(self.conn, message2_hash, message2_json)

        # Manually update last_seen for message 2 to be older than 5 days
        cursor = self.conn.execute(
            "UPDATE messages_cache SET last_seen = datetime('now', '-10 days') WHERE message_hash = ?",
            (message2_hash,)
        )
        self.conn.commit()

        # Clean up old messages (older than 5 days)
        cleanup_old_messages(self.conn, days=5)

        # Verify that the old message was deleted
        cached_message = get_cached_message(self.conn, message2_hash)
        self.assertIsNone(cached_message, "Message 2 should have been deleted.")

        # Verify that the recent message is still there
        cached_message = get_cached_message(self.conn, message1_hash)
        self.assertIsNotNone(cached_message, "Message 1 should not have been deleted.")

