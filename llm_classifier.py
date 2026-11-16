import openai
from pathlib import Path
from typing import Literal
from abc import ABC, abstractmethod
from enum import Enum
from openai import AsyncOpenAI
from config import GPT_API_KEY

# Set API key
openai.api_key = GPT_API_KEY

class LLMProvider(Enum):
    """Enumeration of supported LLM providers."""
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"


JobLabel = Literal["relevant", "not_relevant", "borderline"]
JOB_LABELS = ("relevant", "not_relevant", "borderline")

# The candidate profile is personal, so it lives in a gitignored file read at runtime
PROFILE_PATH = Path(__file__).parent / "profile.txt"

SYSTEM_PROMPT_TEMPLATE = (
    "You are a job-post classifier for one candidate.\n"
    "Candidate profile:\n{profile}\n\n"
    "The message comes from a Telegram tech-jobs channel. It may be in Hebrew or English and "
    "has been lowercased with punctuation removed.\n"
    "Labels:\n"
    "- relevant: a job opening that fits the candidate profile (role, location and seniority).\n"
    "- borderline: a job opening that only partly fits, e.g. an adjacent role, an unclear "
    "location, or seniority slightly off from the profile.\n"
    "- not_relevant: not a job opening (questions, courses, ads, chatter), an unrelated role, "
    "a location the profile excludes, or a clear seniority mismatch.\n"
    "Respond with ONLY one word: relevant, not_relevant or borderline."
)


def load_profile(path: str | Path = PROFILE_PATH) -> str:
    """Read the candidate profile from a local text file.

    Raises:
        FileNotFoundError: if the file is missing, with setup instructions.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Candidate profile not found at {path}. "
            "Copy profile.example.txt to profile.txt and describe yourself there."
        )
    return path.read_text(encoding="utf-8").strip()


def build_system_prompt(profile: str) -> str:
    """Insert the candidate profile into the classification prompt."""
    return SYSTEM_PROMPT_TEMPLATE.format(profile=profile)


class LLMClassifier(ABC):
    """Abstract base class for LLM-based classifiers.

    Defines the interface that all LLM classifier implementations must follow.
    """

    @abstractmethod
    async def classify(self, text: str) -> JobLabel:
        """Classify a job post against the candidate profile.

        Args:
            text: The normalized message text to classify.

        Returns:
            "relevant", "not_relevant" or "borderline".
        """
        pass

class OpenAIClassifier(LLMClassifier):
    """LLM classifier using OpenAI's GPT models (v1.0.0+ SDK)."""
    
    def __init__(self):
        # Initialize the Async client once when the classifier is created
        self.client = AsyncOpenAI(api_key=GPT_API_KEY)
        self.system_prompt = build_system_prompt(load_profile())
    
    async def classify(self, text: str) -> JobLabel:
        """Classify a job post using OpenAI GPT-4."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f'Message: "{text}"'}
                ],
                temperature=0,
                max_tokens=5,  # labels span several tokens ("not_relevant")
            )

            # FIX 1: Safely handle potential None value for content
            raw_content = response.choices[0].message.content
            if not raw_content:
                return "not_relevant"

            result = raw_content.strip().lower()

            if result in JOB_LABELS:
                return result

            return "not_relevant"

        except Exception as e:
            print(f"Error in LLM classification: {e}")
            return "not_relevant"

class AnthropicClassifier(LLMClassifier):
    """LLM classifier using Anthropic's Claude models. Stub."""
    async def classify(self, text: str) -> JobLabel:
        raise NotImplementedError("Anthropic classification not yet implemented")


async def classify_with_llm(text: str) -> JobLabel:
    """
    Convenience function. 
    Note: For production efficiency, you might want to reuse a 
    single OpenAIClassifier instance rather than creating a new client 
    per request.
    """
    classifier = OpenAIClassifier()
    return await classifier.classify(text)