import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
import numpy as np

from config import Config
from services.gemini_client import GeminiClient
from retriever.mongodb_vectorstore import MongoDBVectorStore
from retriever.zilliz_vectorstore import ZillizVectorStore

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector store for document storage and retrieval using MongoDB or Zilliz
    """
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.vector_store_type = Config.VECTOR_STORE_TYPE
        
        if self.vector_store_type == "mongodb":
            self._init_mongodb()
        elif self.vector_store_type == "zilliz":
            self._init_zilliz()
        else:
            raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")
    

    
    def _init_mongodb(self):
        """
        Initialize MongoDB Atlas vector store
        """
        try:
            self.mongodb_store = MongoDBVectorStore()
            logger.info("MongoDB Atlas vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing MongoDB Atlas: {str(e)}")
            raise
    
    def _init_zilliz(self):
        """
        Initialize Zilliz Cloud vector store
        """
        try:
            self.zilliz_store = ZillizVectorStore()
            logger.info("Zilliz Cloud vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Zilliz Cloud: {str(e)}")
            raise
    
    async def add_documents(self, documents: List[str], metadata: Dict[str, Any] = None) -> None:
        """
        Add documents to vector store
        """
        try:
            if not documents:
                return
            
            # Generate embeddings for documents
            embeddings = await self.gemini_client.get_embeddings(documents)
            
            # Prepare data for storage
            ids = [f"doc_{i}_{hash(doc) % 1000000}" for i, doc in enumerate(documents)]
            metadatas = [metadata or {} for _ in documents]
            
            if self.vector_store_type == "mongodb":
                await self.mongodb_store.add_documents(documents, metadata)
            elif self.vector_store_type == "zilliz":
                await self.zilliz_store.add_documents(documents, metadata)
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    

    
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        """
        try:
            # Get query embedding
            query_embedding = await self.gemini_client.get_embeddings([query])
            query_vector = query_embedding[0]
            
            if self.vector_store_type == "mongodb":
                return await self.mongodb_store.similarity_search(query, k)
            elif self.vector_store_type == "zilliz":
                return await self.zilliz_store.similarity_search(query, k)
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise
    
    async def similarity_search_with_filter(self, query: str, filter_dict: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents with metadata filter
        """
        try:
            # Get query embedding
            query_embedding = await self.gemini_client.get_embeddings([query])
            query_vector = query_embedding[0]
            
            if self.vector_store_type == "mongodb":
                return await self.mongodb_store.similarity_search_with_filter(query, filter_dict, k)
            elif self.vector_store_type == "zilliz":
                return await self.zilliz_store.similarity_search_with_filter(query, filter_dict, k)
            
        except Exception as e:
            logger.error(f"Error in filtered similarity search: {str(e)}")
            raise
    

    
    async def delete_by_metadata(self, filter_dict: Dict[str, Any]) -> None:
        """
        Delete documents by metadata filter
        """
        try:
            if self.vector_store_type == "mongodb":
                await self.mongodb_store.delete_by_metadata(filter_dict)
            elif self.vector_store_type == "zilliz":
                await self.zilliz_store.delete_by_metadata(filter_dict)
                
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        """
        try:
            if self.vector_store_type == "mongodb":
                return await self.mongodb_store.get_collection_stats()
            elif self.vector_store_type == "zilliz":
                return await self.zilliz_store.get_collection_stats()
                
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)} 