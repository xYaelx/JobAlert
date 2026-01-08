import openai
import asyncio
from typing import Literal
from abc import ABC, abstractmethod
from enum import Enum
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
    """LLM classifier using OpenAI's GPT models.
    
    Communicates with OpenAI API to classify fertility medication offer messages.
    Uses GPT-4 with temperature=0 for deterministic binary classification.
    """
    
    async def classify(self, text: str) -> Literal["offer", "not_offer"]:
        """Classify a message using OpenAI GPT-4.
        
        Args:
            text: The normalized message text to classify.
            
        Returns:
            "offer" if message indicates availability of fertility medication,
            "not_offer" otherwise.
            
        Defaults to "not_offer" if response is invalid or raises exception.
        """
        try:
            # Call the OpenAI API with the classification request
            response = await openai.ChatCompletion.create(
                model="gpt-4",  # Use a cheaper and faster model if needed like gpt-3.5 or gpt-4 if available
                messages=[
                    {"role": "system", "content": (
                        "You are a classifier. "
                        "Decide whether the message is an offer to give or sell fertility medication. "
                        "Respond with ONLY one word: 'offer' or 'not_offer'."
                    )},
                    {"role": "user", "content": f'Message: "{text}"'}
                ],
                temperature=0,
                max_tokens=1,  # Only one word response
            )

            # Extract the result
            result = response['choices'][0]['message']['content'].strip().lower()

            # Check that the response is either 'offer' or 'not_offer'
            if result not in {"offer", "not_offer"}:
                return "not_offer"  # Default to "not_offer" if response is invalid
            
            return result

        except Exception as e:
            print(f"Error in LLM classification: {e}")
            return "not_offer"  # Default to "not_offer" in case of any error

class AnthropicClassifier(LLMClassifier):
    """LLM classifier using Anthropic's Claude models.
    
    Stub implementation for future integration with Anthropic API.
    """
    
    async def classify(self, text: str) -> Literal["offer", "not_offer"]:
        """Classify a message using Anthropic Claude.
        
        Args:
            text: The normalized message text to classify.
            
        Returns:
            "offer" if message indicates availability of fertility medication,
            "not_offer" otherwise.
        """
        pass  # TODO: Implement Claude integration

async def classify_with_llm(text: str) -> Literal["offer", "not_offer"]:
    """Classify a message using the default LLM classifier.
    
    Convenience function that uses OpenAIClassifier for text classification.
    
    Args:
        text: The normalized message text to classify.
        
    Returns:
        "offer" if message indicates availability of fertility medication,
        "not_offer" otherwise.
    """
    classifier = OpenAIClassifier()
    return await classifier.classify(text)
