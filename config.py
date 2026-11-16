# Define the target channels/groups with their friendly names
# Format: {channel_id: 'friendly_name'}
import os
from dotenv import load_dotenv

load_dotenv()
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
GPT_API_KEY = os.getenv("OPENAI_API_KEY")

TARGET_CHANNELS = {
    '@secretmachinelearningjobs': 'Secret Machine Learning Jobs 🕵🏻‍♂️',
    '@hitechjobsdatascience': 'Hi-Tech Jobs - Data Science',
}

# Job-post prefilter keywords, as plain phrases matched against normalized text
JOB_KEYWORDS = [
    "computer vision", "deep learning", "machine learning",
    "pytorch", "opencv", "tensorflow",
    "algorithm", "algorithms", "image processing", "object detection", "segmentation", "perception",
    "ml", "dl", "mlops",
    "ראייה ממוחשבת", "ראיה ממוחשבת", "למידה עמוקה", "למידת מכונה", "אלגוריתמיקאי", "אלגוריתמים",
]




