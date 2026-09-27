"""Environment-backed configuration for the model-powered agent."""

import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1").strip().rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3.5:4b").strip()
MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", "5"))


def create_client() -> OpenAI:
    """Create an OpenAI-compatible client connected to the local Ollama server."""
    return OpenAI(base_url=OLLAMA_HOST, api_key="ollama")


def validate_config() -> None:
    """Fail early with a useful setup message when model configuration is missing."""
    if not OLLAMA_HOST.startswith(("http://", "https://")):
        raise RuntimeError("OLLAMA_HOST must be an HTTP URL.")
    if not MODEL_NAME:
        raise RuntimeError("MODEL_NAME must not be empty.")
    if MAX_TOOL_CALLS <= 0:
        raise RuntimeError("MAX_TOOL_CALLS must be a positive integer.")