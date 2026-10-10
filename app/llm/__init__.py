"""
LLM 统一客户端与模型中台
支持任意大模型（OpenAI, DeepSeek, Qwen, Google Gemini, Anthropic Claude, 硅基流动, 本地 Ollama/vLLM）插件化极速接入
"""
from typing import Any, Optional

from .base_client import BaseLLMClient, normalize_content
from .provider_keys import (
    canonical_aliases,
    normalize_provider_key,
    env_key_for_provider,
    default_backend_url,
)
from .model_catalog import MODEL_OPTIONS, get_model_options, get_known_models


def create_llm_client(*args: Any, **kwargs: Any) -> BaseLLMClient:
    from .factory import create_llm_client as _create_llm_client
    return _create_llm_client(*args, **kwargs)


__all__ = [
    "BaseLLMClient",
    "create_llm_client",
    "normalize_content",
    "canonical_aliases",
    "normalize_provider_key",
    "env_key_for_provider",
    "default_backend_url",
    "MODEL_OPTIONS",
    "get_model_options",
    "get_known_models",
]
