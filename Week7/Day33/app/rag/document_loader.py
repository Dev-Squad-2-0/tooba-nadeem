"""
document_loader.py
------------------

Loads all knowledge base documents used by the RAG pipeline.

Supported formats
-----------------
- Markdown (.md)

Supported folders
-----------------
database/
    knowledge/
        brochures/
        developers/
        guides/
        faqs/
        company/

Author:
Week 7 Capstone Project
"""

from pathlib import Path
from typing import List
import logging

from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader


logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Loads all Markdown documents from the knowledge base.
    """

    def __init__(self, knowledge_base_path: Path):

        self.knowledge_base_path = Path(knowledge_base_path)

        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {self.knowledge_base_path}"
            )

    def load(self) -> List[Document]:
        """
        Load every Markdown document recursively.

        Returns
        -------
        List[Document]
        """

        logger.info("Loading knowledge base...")

        loader = DirectoryLoader(
        path=str(self.knowledge_base_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={
            "encoding": "utf-8"
        },
        show_progress=True,
        use_multithreading=True,
    )

        documents = loader.load()

        logger.info(
            "Loaded %d documents.",
            len(documents),
        )

        return documents

    def summary(self) -> None:
        """
        Print a summary of the knowledge base.
        """

        documents = self.load()

        logger.info("Knowledge Base Summary")
        logger.info("----------------------")
        logger.info("Documents : %d", len(documents))

        for doc in documents[:5]:
            logger.info(doc.metadata.get("source"))