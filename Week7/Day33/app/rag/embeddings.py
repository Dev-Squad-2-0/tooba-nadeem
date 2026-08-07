"""
embeddings.py
-------------

Creates and returns the embedding model used throughout the application.

Using LangChain's HuggingFaceEmbeddings allows seamless integration
with ChromaDB while still running completely locally.

Embedding Model:
    all-MiniLM-L6-v2
"""

import logging

from langchain_huggingface import HuggingFaceEmbeddings

from app import config


logger = logging.getLogger(__name__)


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Load the embedding model.

    Returns
    -------
    HuggingFaceEmbeddings
    """

    logger.info(
        "Loading embedding model: %s",
        config.EMBEDDING_MODEL,
    )

    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu",
        },
        encode_kwargs={
            "normalize_embeddings": True,
        },
    )