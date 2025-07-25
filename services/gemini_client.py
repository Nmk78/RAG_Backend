from google import genai
import asyncio
import logging
from typing import List, Optional

from config import Config

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.chat_model = Config.GEMINI_MODEL  # e.g. "gemini-2.5-flash"
        self.embedding_model = Config.GEMINI_EMBEDDING_MODEL  # e.g. "gemini-embedding-001"
        self.chat_history = []

    async def generate_response(self, query: str, context: str = "", file_context: bool = False, is_image: bool = False) -> str:
        try:
            if is_image:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.chat_model,
                    contents=query
                )
                response_text = getattr(response, "text", None) or "I couldn't generate a response."
                self.chat_history.append({"role": "user", "Image content": query})
                self.chat_history.append({"role": "assistant", "content": response_text})
                if len(self.chat_history) > 20:
                    self.chat_history = self.chat_history[-20:]
                logger.info(f"Generated response for query: {query[:50]}...")
                return response_text
            elif context:
                prompt = self._build_file_prompt(query, context) if file_context else self._build_rag_prompt(query, context)
            elif not context and not is_image:
                prompt = self._build_normal_prompt(query)
            else:
                raise ValueError("Invalid context or image")
            
            response = await asyncio.to_thread(
                self.client.models.generate_content,    
                model=self.chat_model,
                contents=prompt
            )
            response_text = getattr(response, "text", None) or "I couldn't generate a response."
            self.chat_history.append({"role": "user", "content": query})
            self.chat_history.append({"role": "assistant", "content": response_text})
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            logger.info(f"Generated response for query: {query[:50]}...")
            return response_text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = []
            for text in texts:
                result = await asyncio.to_thread(
                    self.client.models.embed_content,
                    model=self.embedding_model,
                    contents=text
                )
                # result.embeddings[0]["values"] is the embedding vector
                # emb = result.embeddings[0]["values"]
                emb = result.embeddings[0].values
                embeddings.append(emb)
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise
    
    def _build_rag_prompt(self, query: str, context: str) -> str:
        """
        Build a RAG prompt with context
        """
        prompt = f"""You are a helpful AI assistant. Use the following context to answer the user's question in Burmese. 
        If the context doesn't contain relevant information, you can use your general knowledge, but prioritize the provided context.

        Context:
        {context}

        User Question: {query}

        Please provide a clear, accurate, and helpful response based on the context provided."""
        
        return prompt
    
    def _build_normal_prompt(self, query: str) -> str:
        """
        Build a RAG prompt with context
        """
        prompt = f"""You are a helpful AI assistant answer the user's question in Burmese unless user ask for English or other language. 

        User Question: {query}

        Please provide a clear, accurate, and helpful response based on the context provided."""
        
        return prompt
    
    def _build_file_prompt(self, query: str, context: str) -> str:
        """
        Build a prompt specifically for file-based questions
        """
        prompt = f"""You are a helpful AI assistant. The user is asking about a specific document. 
        Please answer their question based ONLY on the content of that document provided below.

        Document Content:
        {context}

        User Question: {query}

        Please provide a clear answer based on the document content. If the document doesn't contain information relevant to the question, please say so."""
        
        return prompt
    
    def clear_chat_history(self) -> None:
        """
        Clear the chat history
        """
        self.chat_history = []
        logger.info("Cleared chat history")
    
    def get_chat_history(self) -> List[dict]:
        """
        Get the current chat history
        """
        return self.chat_history.copy() 