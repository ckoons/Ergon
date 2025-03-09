"""
LLM Client Module for Agenteer.

This module provides a unified interface for interacting with different
LLM providers (OpenAI, Anthropic, Ollama).
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable, AsyncGenerator
from enum import Enum
import httpx

from agenteer.utils.config.settings import settings


class LLMProvider(str, Enum):
    """Enum for supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    UNKNOWN = "unknown"


class Message:
    """Message for LLM conversation."""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary."""
        return {"role": self.role, "content": self.content}
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Message":
        """Create message from dictionary."""
        return cls(data["role"], data["content"])


class LLMClient:
    """
    Unified client for interacting with LLM providers.
    
    This class provides a simple, consistent interface for sending
    prompts to various LLM providers.
    """
    
    def __init__(
        self, 
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize the LLM client.
        
        Args:
            model_name: Name of the model to use
            temperature: Temperature for generation (0-1)
            max_tokens: Maximum tokens to generate
        """
        self.model_name = model_name or settings.default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Determine provider from model name
        if "gpt" in self.model_name.lower() or self.model_name.startswith("openai/"):
            self.provider = LLMProvider.OPENAI
        elif "claude" in self.model_name.lower() or self.model_name.startswith("anthropic/"):
            self.provider = LLMProvider.ANTHROPIC
        elif "ollama" in self.model_name.lower() or "/" in self.model_name:
            self.provider = LLMProvider.OLLAMA
            if self.model_name.startswith("ollama/"):
                self.model_name = self.model_name.replace("ollama/", "")
        else:
            self.provider = LLMProvider.UNKNOWN
        
        # Create appropriate client
        if self.provider == LLMProvider.OPENAI:
            self._create_openai_client()
        elif self.provider == LLMProvider.ANTHROPIC:
            self._create_anthropic_client()
        elif self.provider == LLMProvider.OLLAMA:
            self._create_ollama_client()
        else:
            raise ValueError(f"Unknown model provider for model: {self.model_name}")
    
    def _create_openai_client(self):
        """Create OpenAI client."""
        try:
            from openai import OpenAI, AsyncOpenAI
            
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured.")
            
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.async_client = AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with 'pip install openai'.")
    
    def _create_anthropic_client(self):
        """Create Anthropic client."""
        try:
            from anthropic import Anthropic, AsyncAnthropic
            
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured.")
            
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self.async_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with 'pip install anthropic'.")
    
    def _create_ollama_client(self):
        """Create Ollama client."""
        # For Ollama, we'll use httpx directly since there's no official Python client
        self.client = httpx.Client(base_url=settings.ollama_base_url)
        self.async_client = httpx.AsyncClient(base_url=settings.ollama_base_url)
    
    def _format_messages_for_provider(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for the specific provider."""
        if self.provider == LLMProvider.OPENAI:
            # OpenAI uses role: system, user, assistant
            return messages
        
        elif self.provider == LLMProvider.ANTHROPIC:
            # Anthropic uses role: user, assistant (system goes in system param)
            formatted_messages = []
            system_message = None
            
            for message in messages:
                if message["role"] == "system":
                    system_message = message["content"]
                else:
                    formatted_messages.append(message)
            
            return formatted_messages, system_message
        
        elif self.provider == LLMProvider.OLLAMA:
            # Ollama doesn't distinguish between roles in its simplest API
            # We'll use the approach of prefixing messages with User: or Assistant:
            combined_prompt = ""
            for message in messages:
                role_prefix = ""
                if message["role"] == "user":
                    role_prefix = "User: "
                elif message["role"] == "assistant":
                    role_prefix = "Assistant: "
                elif message["role"] == "system":
                    role_prefix = "System: "
                
                combined_prompt += f"{role_prefix}{message['content']}\n\n"
            
            return combined_prompt
    
    def complete(self, messages: List[Dict[str, str]]) -> str:
        """
        Complete a conversation with the LLM.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Generated text response
        """
        if self.provider == LLMProvider.OPENAI:
            formatted_messages = self._format_messages_for_provider(messages)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            return response.choices[0].message.content
        
        elif self.provider == LLMProvider.ANTHROPIC:
            formatted_messages, system = self._format_messages_for_provider(messages)
            
            response = self.client.messages.create(
                model=self.model_name,
                messages=formatted_messages,
                system=system,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            return response.content[0].text
        
        elif self.provider == LLMProvider.OLLAMA:
            prompt = self._format_messages_for_provider(messages)
            
            response = self.client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": False,
                },
            )
            
            response.raise_for_status()
            return response.json()["response"]
    
    async def acomplete(self, messages: List[Dict[str, str]]) -> str:
        """
        Complete a conversation with the LLM (async).
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Generated text response
        """
        if self.provider == LLMProvider.OPENAI:
            formatted_messages = self._format_messages_for_provider(messages)
            
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            return response.choices[0].message.content
        
        elif self.provider == LLMProvider.ANTHROPIC:
            formatted_messages, system = self._format_messages_for_provider(messages)
            
            response = await self.async_client.messages.create(
                model=self.model_name,
                messages=formatted_messages,
                system=system,
                temperature=self.temperature,
                max_tokens=self.max_tokens or 4096,
            )
            
            return response.content[0].text
        
        elif self.provider == LLMProvider.OLLAMA:
            prompt = self._format_messages_for_provider(messages)
            
            response = await self.async_client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": False,
                },
            )
            
            response.raise_for_status()
            return response.json()["response"]
    
    async def acomplete_stream(
        self, 
        messages: List[Dict[str, str]], 
        callback: Optional[Callable[[str], None]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion from the LLM (async).
        
        Args:
            messages: List of message dictionaries
            callback: Optional callback function to receive chunks
        
        Yields:
            Generated text chunks
        """
        if self.provider == LLMProvider.OPENAI:
            formatted_messages = self._format_messages_for_provider(messages)
            
            stream = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    if callback:
                        callback(content)
                    yield content
        
        elif self.provider == LLMProvider.ANTHROPIC:
            formatted_messages, system = self._format_messages_for_provider(messages)
            
            stream = await self.async_client.messages.create(
                model=self.model_name,
                messages=formatted_messages,
                system=system,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.type == "content_block_delta" and chunk.delta.text:
                    content = chunk.delta.text
                    if callback:
                        callback(content)
                    yield content
        
        elif self.provider == LLMProvider.OLLAMA:
            prompt = self._format_messages_for_provider(messages)
            
            response = await self.async_client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": True,
                },
                headers={"Accept": "application/x-ndjson"},
            )
            
            response.raise_for_status()
            
            # Ollama streams line-delimited JSON
            buffer = ""
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                
                try:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        content = chunk["response"]
                        buffer += content
                        if callback:
                            callback(content)
                        yield content
                except json.JSONDecodeError:
                    continue
