import asyncio
from typing import Optional, List
import logging

from config import Config
from services.rag_pipeline import RAGPipeline
from services.gemini_client import GeminiClient
from retriever.vectorstore import VectorStore

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Main orchestrator that coordinates all RAG operations
    """
    
    def __init__(self):
        self.rag_pipeline = RAGPipeline()
        self.gemini_client = GeminiClient()
        self.vector_store = VectorStore()
        
    async def handle_text(self, query: str) -> str:
        """
        Handle text-based queries using RAG pipeline
        """
        try:
            # Clean and normalize query
            cleaned_query = await self._clean_query(query)
            
            # Get relevant context from vector store
            context = await self.rag_pipeline.retrieve_context(cleaned_query)
            
            # logging.critical(f"Context: {context}");  ## Log Context here

            # Generate response using Gemini
            response = await self.gemini_client.generate_response(
                query=cleaned_query,
                context=context
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in handle_text: {str(e)}")
            raise
    
    async def handle_file_question(self, query: str, context: str, is_image: bool) -> str:
        """
        Handle queries specifically about a particular file
        """
        try:
            # Clean query
            cleaned_query = await self._clean_query(query)  

            if is_image:
                # For images, the context is already the extracted text/description from Gemini Vision
                # So we can treat it like a normal text response
                response = await self.gemini_client.generate_response(
                    query=cleaned_query,
                    context=context,
                    file_context=True,
                    is_image=False  # Set to False since context is already processed
                )
            else:
                # For regular files, generate response normally
                response = await self.gemini_client.generate_response(
                    query=cleaned_query,
                    context=context,
                    file_context=True,
                    is_image=False
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in handle_file_question: {str(e)}")
            raise
    
    async def process_file(self, file_id: str, text_content: str, filename: str) -> None:
        """
        Process and index a file for RAG
        """
        try:
            # Split text into chunks
            chunks = await self.rag_pipeline.split_text(text_content)
            
            # Store chunks in vector store with file metadata
            await self.vector_store.add_documents(
                documents=chunks,
                metadata={
                    "file_id": file_id,
                    "filename": filename,
                    "source": "file_upload"
                }
            )
            
            logger.info(f"Successfully processed and indexed file: {filename} (ID: {file_id})")
            
        except Exception as e:
            logger.error(f"Error processing file {file_id}: {str(e)}")
            raise
    
    async def delete_file(self, file_id: str) -> None:
        """
        Delete a file and its indexed content
        """
        try:
            # Remove documents from vector store
            await self.vector_store.delete_by_metadata({"file_id": file_id})
            
            logger.info(f"Successfully deleted file content: {file_id}")
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            raise
    
    async def _clean_query(self, query: str) -> str:
        """
        Clean and normalize user query
        """
        # Basic cleaning - can be extended with more sophisticated text processing
        cleaned = query.strip()
        if len(cleaned) > Config.MAX_CONTEXT_LENGTH:
            cleaned = cleaned[:Config.MAX_CONTEXT_LENGTH]
        return cleaned
    
    async def get_chat_history(self, user_id: Optional[str] = None) -> List[dict]:
        """
        Get chat history (placeholder for future implementation)
        """
        # TODO: Implement chat history storage and retrieval
        return []
    
    async def add_to_chat_history(self, query: str, response: str, user_id: Optional[str] = None) -> None:
        """
        Add interaction to chat history (placeholder for future implementation)
        """
        # TODO: Implement chat history storage
        pass 