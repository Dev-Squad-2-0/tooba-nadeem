"""
vector_store.py
---------------

Creates and manages the Chroma vector database.
"""
import shutil

from pathlib import Path
import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app import config
from app.rag.embeddings import get_embedding_model


logger = logging.getLogger(__name__)

class VectorStore:
    """
    Handles creation, loading, and persistence of the Chroma vector database.
    """

    def __init__(
        self,
        persist_directory: Path = config.VECTOR_DB_DIR,
    ):

        self.persist_directory = str(persist_directory)

        self.embedding_model = get_embedding_model()

        self.db = None

    def exists(self) -> bool:
        """
        Check whether a persisted Chroma database already exists.
        """
        db_path = Path(self.persist_directory)

        return db_path.exists() and any(db_path.iterdir())

    def create(
    self,
    documents: list[Document],
    ) -> Chroma:
        """
        Create a fresh vector database from documents.
        """

        logger.info("Creating Chroma vector database...")

        db_path = Path(self.persist_directory)

        if db_path.exists():
            logger.info("Removing old vector database...")
            shutil.rmtree(db_path)

        self.db = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            persist_directory=self.persist_directory,
        )

        logger.info("Vector database created successfully.")

        return self.db

    def load(self) -> Chroma:
        """
        Load an existing vector database.
        """

        logger.info("Loading vector database...")

        self.db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model,
        )

        logger.info("Vector database loaded.")

        return self.db

    def count(self) -> int:
        """
        Return the number of stored chunks.
        """

        if self.db is None:
            self.load()

        return self.db._collection.count()