import asyncio
from telethon import TelegramClient, events
import json
from config import TARGET_CHANNELS, API_ID, API_HASH
from llm_classifier import classify_with_llm
from text_processor import normalize_text, needs_llm_decision
from db import (
    get_connection,
    init_db,
    compute_message_hash,
    get_cached_message,
    touch_message,
    insert_message,
    cleanup_old_messages,
)
from notifier import send_alert

async def main() -> None:
    """Initialize and run the Telegram message ingestion pipeline.
    
    Establishes database connection, creates Telegram client, registers
    message event handler, and listens for new messages in configured channels.
    Processes each message through heuristic filtering and optional LLM
    classification, caching results and sending alerts for offers.
    """
    # database setup
    conn = get_connection()
    init_db(conn)

    client = TelegramClient("session", API_ID, API_HASH)

    @client.on(events.NewMessage(chats=TARGET_CHANNELS))
    async def handler(event):
        try:
            if not event.text:
                return

            chat = event.chat
            channel_name = (
                    getattr(chat, "title", None)
                    or getattr(chat, "first_name", None)
                    or f"Chat {chat.id}"
            )

            sender = event.sender
            sender_name = (
                sender.first_name
                if sender and sender.first_name
                else sender.username
                if sender and sender.username
                else "Channel"
            )

            msg_date = event.date.astimezone()

            chat_text = normalize_text(event.text)
            if not chat_text:
                return

            #  Check for exact duplicate
            chat_hash = compute_message_hash(chat_text)
            cached = get_cached_message(conn, chat_hash)
            if cached:
                row_id, extracted_json = cached
                touch_message(conn, row_id)
                return # skip LLM & alerts entirely

            #  Decide if LLM is needed
            decision = needs_llm_decision(chat_text)

            # Check if the message needs llm
            llm_result = None

            if decision["needs_llm"]:
                llm_result = await classify_with_llm(chat_text)

            # Alert llogic
            if decision["is_relevant"] or llm_result == "offer":
                send_alert(
                    text=chat_text,
                    channel=channel_name,
                    sender=sender_name,
                    timestamp=msg_date,
                    llm_result=llm_result,
                )
            final_status = (
                "offer"
                if decision["is_relevant"] or llm_result == "offer"
                else "ignored"
            )
            # Store result in cache
            insert_message(
                conn,
                chat_hash,
                final_status,
            )

            # Cleanup old cache entries
            cleanup_old_messages(conn)

        except Exception as e:
            print(f"Error handling message: {e}")

    await client.start()
    print("Listening to Telegram channels...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
