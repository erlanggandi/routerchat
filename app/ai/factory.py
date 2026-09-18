import logging
from langchain_openai import ChatOpenAI
from config.settings import settings

logger = logging.getLogger(__name__)


def get_llm(
    model: str = None,
    base_url: str = None,
    api_key: str = None,
    temperature: float = None,
) -> ChatOpenAI:
    """
    Instantiates an OpenAI-compatible Chat model.
    Supports OpenAI, DeepSeek, Groq, Ollama, OpenRouter, Gemini, and local LLM endpoints.
    """
    model_name = model or settings.AI_MODEL
    url = base_url or settings.AI_BASE_URL
    key = api_key or settings.AI_API_KEY
    temp = temperature if temperature is not None else settings.AI_TEMPERATURE

    if not key:
        logger.warning("AI_API_KEY is not set. LLM calls will fail if not using a keyless local endpoint.")

    llm = ChatOpenAI(
        model=model_name,
        base_url=url,
        api_key=key if key else "no-key-required",
        temperature=temp,
        timeout=30,
        max_retries=2,
    )
    return llm
