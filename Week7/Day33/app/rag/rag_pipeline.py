"""
rag_pipeline.py
---------------

High-level orchestration for the Retrieval-Augmented Generation (RAG)
pipeline.

Responsibilities
----------------
1. Build the vector database (one-time setup)
2. Load an existing vector database
3. Retrieve relevant knowledge for a user query

NOTE:
This pipeline intentionally does NOT call an LLM.

Answer generation will be handled later by the LangGraph workflow.
"""

import logging

from app import config
from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import DocumentSplitter
from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever
from langchain_core.documents import Document

from app.llm.client import generate_answer

logger = logging.getLogger(__name__)


class RAGPipeline:

    def __init__(self):

        self.loader = DocumentLoader(
            config.KNOWLEDGE_BASE_DIR
        )

        self.splitter = DocumentSplitter()

        self.vector_store = VectorStore()

    # --------------------------------------------------
    # Build Vector Database
    # --------------------------------------------------

    def build(self) -> int:

        logger.info("Building RAG pipeline...")

        if self.vector_store.exists():

            logger.info("Existing vector database found.")

            self.vector_store.load()

            count = self.vector_store.count()

            logger.info("Indexed %d chunks.", count)

            return count

        logger.info("No existing vector database found.")

        documents = self.loader.load()

        chunks = self.splitter.split(documents)

        self.vector_store.create(chunks)

        count = self.vector_store.count()

        logger.info("Indexed %d chunks.", count)

        return count

    # --------------------------------------------------
    # Retrieve Documents
    # --------------------------------------------------

    def retrieve(
        self,
        query: str,
    ) -> list[Document]:
        """
        Retrieve relevant knowledge chunks.
        """

        retriever = Retriever()

        return retriever.retrieve(query)

    # --------------------------------------------------
    # Generate Grounded Answer
    # --------------------------------------------------

    def answer(
        self,
        question: str,
    ) -> str:
        """
        Retrieve context and generate
        a grounded answer.
        """

        docs = self.retrieve(question)

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        return generate_answer(
            question,
            context,
        )

