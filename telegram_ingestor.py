import asyncio
from telethon import TelegramClient, events
from config import TARGET_CHANNELS, API_ID, API_HASH
from text_processor import normalize_text, needs_llm_decision, message_hash


async def main():
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
            # check for duplicates
            chat_hash = message_hash(chat_text)
            # # Exact duplicate
            # exact = get_exact_duplicate(conn, message_hash)
            # if exact:
            #     row_id, extracted_json = exact
            #     update_last_seen(conn, row_id)
            #     return extracted_json  # reuse cached result

            decision = await needs_llm_decision(chat_text)
            print(f"chat_text: {chat_text}")
            print(decision)
            # if decision:
            #     row_id, extracted_json = decision
            # check if the message needs llm
            # if decision["needs_llm"]:
            #     llm_result = await classify_with_llm(chat_text)
            #
            # if decision["is_relevant"] or llm_result == "offer":
            #     send_alert()

            # insert_message(
            #     conn,
            #     message_hash,
            #     simhash,
            #     medication,
            #     intent,
            #     extracted_json,
            # )
            #
            # cleanup_old_messages(conn)
            #
        except Exception as e:
            print(f"Error handling message: {e}")

    await client.start()
    print("Listening to Telegram channels...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
