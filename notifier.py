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
    Send an alert for a classified job post.

    Args:
        text: Message content
        channel: Telegram channel name
        sender: Sender display name
        timestamp: Time the message was posted (local time)
        llm_result: Classification label ("relevant", "borderline" or None)
    """
    label = llm_result.capitalize() if llm_result else "Matching"
    alert_msg = (
        f"[ALERT] {label} job in {channel}, posted {timestamp:%d.%m %H:%M}\n"
        f"Sender: {sender}\n"
        f"Message: {text}\n"
    )
    print(alert_msg)