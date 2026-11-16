import openai
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


class LLMClassifier(ABC):
    """Abstract base class for LLM-based classifiers.
    
    Defines the interface that all LLM classifier implementations must follow.
    """
    
    @abstractmethod
    async def classify(self, text: str) -> Literal["offer", "not_offer"]:
        """Classify a message as an offer or non-offer.
        
        Args:
            text: The normalized message text to classify.
            
        Returns:
            "offer" if message indicates availability of fertility medication,
            "not_offer" otherwise.
        """
        pass

class OpenAIClassifier(LLMClassifier):
    """LLM classifier using OpenAI's GPT models (v1.0.0+ SDK)."""
    
    def __init__(self):
        # Initialize the Async client once when the classifier is created
        self.client = AsyncOpenAI(api_key=GPT_API_KEY)
    
    async def classify(self, text: str) -> Literal["offer", "not_offer"]:
        """Classify a message using OpenAI GPT-4."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": (
                        "You are a classifier. "
                        "Decide whether the message is an offer to give or sell fertility medication. "
                        "Respond with ONLY one word: 'offer' or 'not_offer'."
                    )},
                    {"role": "user", "content": f'Message: "{text}"'}
                ],
                temperature=0,
                max_tokens=1,
            )

            # FIX 1: Safely handle potential None value for content
            raw_content = response.choices[0].message.content
            if not raw_content:
                return "not_offer"

            result = raw_content.strip().lower()

            if result == "offer":
                return "offer"
            
            return "not_offer"

        except Exception as e:
            print(f"Error in LLM classification: {e}")
            return "not_offer"

class AnthropicClassifier(LLMClassifier):
    """LLM classifier using Anthropic's Claude models. Stub."""
    async def classify(self, text: str) -> Literal["offer", "not_offer"]:
        raise NotImplementedError("Anthropic classification not yet implemented")
 

async def classify_with_llm(text: str) -> Literal["offer", "not_offer"]:
    """
    Convenience function. 
    Note: For production efficiency, you might want to reuse a 
    single OpenAIClassifier instance rather than creating a new client 
    per request.
    """
    classifier = OpenAIClassifier()
    return await classifier.classify(text)