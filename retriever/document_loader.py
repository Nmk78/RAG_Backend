import os
import logging
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from config import Config

logger = logging.getLogger(__name__)

class DocumentLoader:
    """
    Document loader for processing and splitting documents
    """
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def load_documents_from_directory(self, directory_path: str, 
                                          file_extensions: Optional[List[str]] = None) -> List[Document]:
        """
        Load documents from a directory
        """
        try:
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            documents = []
            
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                
                if os.path.isfile(file_path):
                    file_ext = os.path.splitext(filename)[1].lower()
                    
                    # Check if file extension is allowed
                    if file_extensions and file_ext not in file_extensions:
                        continue
                    
                    # Load document
                    doc = await self.load_document(file_path)
                    if doc:
                        documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} documents from {directory_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading documents from directory {directory_path}: {str(e)}")
            raise
    
    async def load_document(self, file_path: str) -> Optional[Document]:
        """
        Load a single document
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return None
            
            # Extract text based on file type
            from processors.file_parser import FileParser
            file_parser = FileParser()
            
            text_content = await file_parser.extract_text(file_path)
            
            if not text_content.strip():
                logger.warning(f"No text content extracted from {file_path}")
                return None
            
            # Create document object
            doc = Document(
                page_content=text_content,
                metadata={
                    "source": file_path,
                    "filename": os.path.basename(file_path),
                    "file_type": os.path.splitext(file_path)[1].lower()
                }
            )
            
            logger.info(f"Loaded document: {file_path} ({len(text_content)} characters)")
            return doc
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            return None
    
    async def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks
        """
        try:
            if not documents:
                return []
            
            # Split documents
            split_docs = self.text_splitter.split_documents(documents)
            
            logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
            return split_docs
            
        except Exception as e:
            logger.error(f"Error splitting documents: {str(e)}")
            raise
    
    async def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Split text into document chunks
        """
        try:
            if not text.strip():
                return []
            
            # Create document object
            doc = Document(
                page_content=text,
                metadata=metadata or {}
            )
            
            # Split document
            split_docs = self.text_splitter.split_documents([doc])
            
            logger.info(f"Split text into {len(split_docs)} chunks")
            return split_docs
            
        except Exception as e:
            logger.error(f"Error splitting text: {str(e)}")
            raise
    
    def get_chunk_stats(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Get statistics about document chunks
        """
        try:
            if not documents:
                return {
                    "total_chunks": 0,
                    "avg_chunk_length": 0,
                    "min_chunk_length": 0,
                    "max_chunk_length": 0
                }
            
            chunk_lengths = [len(doc.page_content) for doc in documents]
            
            return {
                "total_chunks": len(documents),
                "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
                "min_chunk_length": min(chunk_lengths),
                "max_chunk_length": max(chunk_lengths),
                "total_characters": sum(chunk_lengths)
            }
            
        except Exception as e:
            logger.error(f"Error getting chunk stats: {str(e)}")
            return {"error": str(e)}
    
    async def process_document_with_metadata(self, file_path: str, 
                                           additional_metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Process a document and add additional metadata
        """
        try:
            # Load document
            doc = await self.load_document(file_path)
            if not doc:
                return []
            
            # Add additional metadata
            if additional_metadata:
                doc.metadata.update(additional_metadata)
            
            # Split document
            split_docs = await self.split_documents([doc])
            
            return split_docs
            
        except Exception as e:
            logger.error(f"Error processing document with metadata {file_path}: {str(e)}")
            raise 