"""Embedding providers - get embeddings from Ollama or OpenAI."""

import os
from typing import Optional

import numpy as np

from slimclaw.config import DEFAULT_EMBEDDING_MODELS
from slimclaw.memory.embeddings.types import EmbeddingProvider


def get_embedding(
    text: str,
    provider: EmbeddingProvider = EmbeddingProvider.OLLAMA,
    model: Optional[str] = None,
) -> np.ndarray:
    """Get embedding vector for text."""
    model = model or DEFAULT_EMBEDDING_MODELS[provider.value]

    if provider == EmbeddingProvider.OLLAMA:
        return _get_ollama_embedding(text, model)
    elif provider == EmbeddingProvider.OPENAI:
        return _get_openai_embedding(text, model)
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


def _get_ollama_embedding(text: str, model: str) -> np.ndarray:
    """Get embedding from Ollama."""
    try:
        import ollama

        response = ollama.embeddings(model=model, prompt=text)
        return np.array(response["embedding"], dtype=np.float32)
    except ImportError:
        raise ValueError("ollama package not installed. Run: pip install ollama")
    except Exception as e:
        raise ValueError(f"Ollama embedding failed: {e}")


def _get_openai_embedding(text: str, model: str) -> np.ndarray:
    """Get embedding from OpenAI."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(input=text, model=model)
        return np.array(response.data[0].embedding, dtype=np.float32)
    except ImportError:
        raise ValueError("openai package not installed. Run: pip install openai")
    except Exception as e:
        raise ValueError(f"OpenAI embedding failed: {e}")
