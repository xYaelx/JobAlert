import openai
import asyncio
from config import GPT_API_KEY

# Read API key from the file (assuming GPT_key.txt contains the OpenAI key)
openai.api_key = GPT_API_KEY

async def classify_with_llm(text: str) -> str:
    """
    Uses OpenAI API to classify a message as either an offer or not_offer.
    Args:
    - text: The message text to classify.
    
    Returns:
    - "offer" or "not_offer" based on the classification.
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

# # Example Usage
# async def test_classification():
#     text = אני צריכה גונל למסיר
