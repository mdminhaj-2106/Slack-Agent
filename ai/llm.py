from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

def get_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """
    Initializes and returns a ChatGoogleGenerativeAI model instance.
    Centralizes LLM connection credentials for imports across the app.
    """
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        google_api_key=settings.GEMINI_API_KEY
    )
