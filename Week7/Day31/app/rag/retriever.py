"""
retriever.py
------------

Creates a semantic retriever over the Chroma vector database.
"""

import logging

from langchain_core.documents import Document

from app import config
from app.rag.vector_store import VectorStore


logger = logging.getLogger(__name__)


class Retriever:
    """
    Wrapper around Chroma's retriever.
    """

    def __init__(self):

        self.vector_store = VectorStore()

        if not self.vector_store.exists():
            raise RuntimeError(
                "Vector database not found. Run pipeline.build() first."
            )

        self.db = self.vector_store.load()

        self.retriever = self.db.as_retriever(
            search_type=config.SEARCH_TYPE,
            search_kwargs={
                "k": config.TOP_K_RESULTS * 2
            },
        )

    def retrieve(  # <-- Moved to class level (not inside __init__)
        self,
        query: str,
    ) -> list[Document]:
        """
        Retrieve the most relevant chunks along with
        their similarity scores.
        """

        logger.info("Searching knowledge base...")

        results = self.db.similarity_search_with_score(
            query,
            k=config.TOP_K_RESULTS,
        )

        logger.info(
            "Retrieved %d documents.",
            len(results),
        )

        for doc, score in results:
            logger.info(
                "Score: %.4f | %s",
                score,
                doc.metadata.get("source"),
            )

        return [doc for doc, score in results]