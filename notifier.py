from datetime import datetime
from typing import Optional


async def send_alert(
    text: str,
    channel: str,
    sender: str,
    timestamp: datetime,
    llm_result: Optional[str],
) -> None:
    """
    Send an alert for a classified message.

    Args:
        text: Message content
        channel: Telegram channel name
        sender: Sender display name
        timestamp: Message timestamp (UTC)
        llm_result: Classification result ("offer" or None)
    """
    alert_msg = (
        f"[ALERT] Offer detected!\n"
        f"Channel: {channel}\n"
        f"Sender: {sender}\n"
        f"Time (UTC): {timestamp}\n"
        f"Message: {text}\n"
        f"LLM Result: {llm_result}\n"
    )
    print(alert_msg)