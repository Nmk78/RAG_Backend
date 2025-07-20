from typing import List, Dict, Any
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from config import Config
from retriever.vectorstore import VectorStore

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    RAG pipeline for text processing, embedding, and retrieval
    """
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding
        """
        try:
            # Create a document object for the text splitter
            doc = Document(page_content=text)
            chunks = self.text_splitter.split_documents([doc])
            
            # Extract text content from chunks
            chunk_texts = [chunk.page_content for chunk in chunks]
            
            logger.info(f"Split text into {len(chunk_texts)} chunks")
            return chunk_texts
            
        except Exception as e:
            logger.error(f"Error splitting text: {str(e)}")
            raise
    
    async def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context from vector store
        """
        try:
            # Get similar documents from vector store
            similar_docs = await self.vector_store.similarity_search(
                query=query,
                k=Config.TOP_K_RETRIEVAL
            )
            
            # Combine context from retrieved documents
            context = self._combine_context(similar_docs)
            
            logger.info(f"Retrieved {len(similar_docs)} relevant documents")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            raise
    
    async def retrieve_file_context(self, query: str, file_id: str) -> str:
        """
        Retrieve context only from a specific file
        """
        try:
            # Get similar documents from specific file
            similar_docs = await self.vector_store.similarity_search_with_filter(
                query=query,
                filter_dict={"file_id": file_id},
                k=Config.TOP_K_RETRIEVAL
            )
            
            # Combine context from retrieved documents
            context = self._combine_context(similar_docs)
            
            logger.info(f"Retrieved {len(similar_docs)} relevant documents from file {file_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving file context: {str(e)}")
            raise
    
    def _combine_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Combine multiple documents into a single context string
        """
        if not documents:
            return ""
        
        # Extract text content and combine
        context_parts = []
        total_length = 0
        
        for doc in documents:
            content = doc.get("page_content", "")
            if total_length + len(content) > Config.MAX_CONTEXT_LENGTH:
                break
            
            context_parts.append(content)
            total_length += len(content)
        
        # Join with double newlines for better separation
        combined_context = "\n\n".join(context_parts)
        
        return combined_context
    
    async def add_documents(self, documents: List[str], metadata: Dict[str, Any] = None) -> None:
        """
        Add documents to the vector store
        """
        try:
            await self.vector_store.add_documents(documents, metadata)
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    async def delete_documents(self, filter_dict: Dict[str, Any]) -> None:
        """
        Delete documents from vector store based on filter
        """
        try:
            await self.vector_store.delete_by_metadata(filter_dict)
            logger.info(f"Deleted documents with filter: {filter_dict}")
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise 