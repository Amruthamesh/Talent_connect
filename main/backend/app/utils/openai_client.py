"""
Global OpenAI client configuration with SSL settings
"""
import httpx
from openai import OpenAI, AsyncOpenAI
from app.config import settings


def create_openai_client() -> OpenAI:
    """
    Create OpenAI client with global SSL configuration
    """
    http_client = httpx.Client(
        verify=settings.SSL_VERIFY,
        timeout=settings.HTTP_TIMEOUT
    )
    
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        http_client=http_client
    )


def create_async_openai_client() -> AsyncOpenAI:
    """
    Create AsyncOpenAI client with global SSL configuration
    """
    http_client = httpx.AsyncClient(
        verify=settings.SSL_VERIFY,
        timeout=settings.HTTP_TIMEOUT
    )
    
    return AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        http_client=http_client
    )


# Global instances
openai_client = create_openai_client()
async_openai_client = create_async_openai_client()