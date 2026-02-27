"""LLM factory - creates provider-specific chat models."""

import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

from slimclaw.llm.types import LLMConfig, Provider

# Load environment variables from .env file
load_dotenv()


class LLMConfigurationError(Exception):
    """Raised when LLM configuration is invalid or missing."""

    pass


def create_llm(config: LLMConfig) -> BaseChatModel:
    """
    Factory function to create the appropriate LangChain chat model.

    Args:
        config: LLMConfig with provider and model settings

    Returns:
        A LangChain BaseChatModel instance

    Raises:
        LLMConfigurationError: If required API keys are missing or config is invalid
    """
    if config.provider == Provider.OLLAMA:
        return _create_ollama(config)
    elif config.provider == Provider.OPENAI:
        return _create_openai(config)
    elif config.provider == Provider.ANTHROPIC:
        return _create_anthropic(config)
    else:
        raise LLMConfigurationError(f"Unknown provider: {config.provider}")


def _create_ollama(config: LLMConfig) -> BaseChatModel:
    """Create ChatOllama instance."""
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=config.model,
        base_url=config.base_url or "http://localhost:11434",
    )


def _create_openai(config: LLMConfig) -> BaseChatModel:
    """Create ChatOpenAI instance."""
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMConfigurationError(
            "OPENAI_API_KEY not found in environment. Please add it to your .env file."
        )

    return ChatOpenAI(
        model=config.model,
        api_key=api_key,
    )


def _create_anthropic(config: LLMConfig) -> BaseChatModel:
    """Create ChatAnthropic instance."""
    from langchain_anthropic import ChatAnthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMConfigurationError(
            "ANTHROPIC_API_KEY not found in environment. "
            "Please add it to your .env file."
        )

    return ChatAnthropic(
        model=config.model,
        api_key=api_key,
    )
