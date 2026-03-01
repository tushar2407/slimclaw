"""LLM factory - creates provider-specific chat models."""

import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

from slimclaw.llm.types import Model, Provider

# Load environment variables from .env file
load_dotenv()


class LLMConfigurationError(Exception):
    """Raised when LLM configuration is invalid or missing."""

    pass


def create_llm(model: Model) -> BaseChatModel:
    """
    Factory function to create the appropriate LangChain chat model.

    Args:
        model: Model with provider and model settings

    Returns:
        A LangChain BaseChatModel instance

    Raises:
        LLMConfigurationError: If required API keys are missing or config is invalid
    """
    if model.provider == Provider.OLLAMA:
        return _create_ollama(model)
    elif model.provider == Provider.OPENAI:
        return _create_openai(model)
    elif model.provider == Provider.ANTHROPIC:
        return _create_anthropic(model)
    else:
        raise LLMConfigurationError(f"Unknown provider: {model.provider}")


def _create_ollama(model: Model) -> BaseChatModel:
    """Create ChatOllama instance."""
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model.id,
        base_url=model.base_url or "http://localhost:11434",
    )


def _create_openai(model: Model) -> BaseChatModel:
    """Create ChatOpenAI instance."""
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMConfigurationError(
            "OPENAI_API_KEY not found in environment. Please add it to your .env file."
        )

    return ChatOpenAI(
        model=model.id,
        api_key=api_key,
    )


def _create_anthropic(model: Model) -> BaseChatModel:
    """Create ChatAnthropic instance."""
    from langchain_anthropic import ChatAnthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMConfigurationError(
            "ANTHROPIC_API_KEY not found in environment. "
            "Please add it to your .env file."
        )

    return ChatAnthropic(
        model=model.id,
        api_key=api_key,
    )
