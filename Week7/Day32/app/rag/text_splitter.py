"""
text_splitter.py
----------------

Splits documents into overlapping chunks for Retrieval-Augmented Generation (RAG).

Why chunking?
-------------
LLMs cannot efficiently search very large documents. Chunking breaks long
documents into smaller overlapping pieces so the retriever can find the
most relevant information.

The chunk size and overlap are configurable from app/config.py.
"""

from typing import List
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app import config


logger = logging.getLogger(__name__)


class DocumentSplitter:
    """
    Splits LangChain Documents into smaller overlapping chunks.
    """

    def __init__(
        self,
        chunk_size: int = config.CHUNK_SIZE,
        chunk_overlap: int = config.CHUNK_OVERLAP,
    ):

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,

            # Split in a natural order
            separators=[
                "\n\n",   # paragraphs
                "\n",     # lines
                ". ",     # sentences
                " ",      # words
                ""        # characters (last resort)
            ]
        )

    def split(
        self,
        documents: List[Document],
    ) -> List[Document]:
        """
        Split documents into chunks.

        Parameters
        ----------
        documents : List[Document]

        Returns
        -------
        List[Document]
        """

        logger.info("Splitting documents...")

        chunks = self.splitter.split_documents(documents)

        logger.info(
            "Created %d chunks.",
            len(chunks),
        )

        return chunks

    @staticmethod
    def statistics(chunks: List[Document]) -> None:
        """
        Display chunk statistics.

        Useful for evaluating different chunk sizes.
        """

        lengths = [len(chunk.page_content) for chunk in chunks]

        if not lengths:
            logger.warning("No chunks available.")
            return

        logger.info("Chunk Statistics")
        logger.info("----------------")
        logger.info("Total chunks : %d", len(chunks))
        logger.info("Smallest     : %d", min(lengths))
        logger.info("Largest      : %d", max(lengths))
        logger.info(
            "Average      : %.2f",
            sum(lengths) / len(lengths),
        )