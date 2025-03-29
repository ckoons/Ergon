"""
Embedding service for Ergon memory system.

This module provides functions to generate embeddings for text using
the configured embedding model.
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
import threading

from ergon.utils.config.settings import settings

# Configure logger
logger = logging.getLogger(__name__)

# Try to import sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not installed. Using fallback embedding.")

# Try to import OpenAI
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Optional model name to override settings
        """
        self.model_name = model_name or settings.embedding_model
        self.model = None
        self.openai_client = None
        self._lock = threading.RLock()
        
        # Determine embedding approach
        if self.model_name.startswith("openai/"):
            if not HAS_OPENAI:
                raise ImportError("OpenAI package not installed but OpenAI embedding requested")
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured but OpenAI embedding requested")
            
            self.embedding_type = "openai"
            self.openai_model = self.model_name.split("/")[1]
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            self.embedding_dimension = 1536  # Default for OpenAI embeddings
            logger.info(f"Using OpenAI embeddings with model: {self.openai_model}")
        else:
            if not HAS_SENTENCE_TRANSFORMERS:
                raise ImportError("sentence-transformers not installed")
            
            self.embedding_type = "sentence_transformers"
            try:
                self.model = SentenceTransformer(self.model_name)
                self.embedding_dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Using sentence-transformers with model: {self.model_name} (dim={self.embedding_dimension})")
            except Exception as e:
                logger.error(f"Error initializing embedding model: {e}")
                raise
    
    async def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text.
        
        Args:
            text: Single text string or list of texts
            
        Returns:
            Embedding vector(s)
        """
        with self._lock:
            try:
                if isinstance(text, str):
                    texts = [text]
                    single_input = True
                else:
                    texts = text
                    single_input = False
                
                # Use the appropriate embedding method
                if self.embedding_type == "openai":
                    response = self.openai_client.embeddings.create(
                        model=self.openai_model,
                        input=texts
                    )
                    embeddings = [item.embedding for item in response.data]
                else:  # sentence_transformers
                    embeddings = self.model.encode(texts).tolist()
                
                # Return single embedding or list based on input
                if single_input:
                    return embeddings[0]
                return embeddings
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                if single_input:
                    # Return zeros as fallback
                    return [0.0] * self.embedding_dimension
                return [[0.0] * self.embedding_dimension for _ in range(len(texts))]

# Create singleton instance
embedding_service = EmbeddingService()