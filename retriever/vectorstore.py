import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
import chromadb
import numpy as np

from config import Config
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector store for document storage and retrieval using Chroma or FAISS
    """
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.vector_store_type = Config.VECTOR_STORE_TYPE
        
        if self.vector_store_type == "chroma":
            self._init_chroma()
        elif self.vector_store_type == "faiss":
            self._init_faiss()
        else:
            raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")
    
    def _init_chroma(self):
        """
        Initialize Chroma vector store
        """
        try:
            # Create persistent client
            self.chroma_client = chromadb.PersistentClient(
                path=Config.CHROMA_PERSIST_DIRECTORY
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="rag_documents",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("Chroma vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Chroma: {str(e)}")
            raise
    
    def _init_faiss(self):
        """
        Initialize FAISS vector store (placeholder for future implementation)
        """
        try:
            # TODO: Implement FAISS vector store
            logger.warning("FAISS vector store not yet implemented, using Chroma as fallback")
            self._init_chroma()
            
        except Exception as e:
            logger.error(f"Error initializing FAISS: {str(e)}")
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
            
            if self.vector_store_type == "chroma":
                await self._add_to_chroma(ids, documents, embeddings, metadatas)
            elif self.vector_store_type == "faiss":
                await self._add_to_faiss(ids, documents, embeddings, metadatas)
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    async def _add_to_chroma(self, ids: List[str], documents: List[str], 
                           embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        """
        Add documents to Chroma vector store
        """
        try:
            # Convert embeddings to numpy arrays
            # embeddings_np = [np.array(emb) for emb in embeddings]
            embeddings_np = [np.array(emb).tolist() for emb in embeddings]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings_np,
                metadatas=metadatas
            )
            
        except Exception as e:
            logger.error(f"Error adding to Chroma: {str(e)}")
            raise
    
    async def _add_to_faiss(self, ids: List[str], documents: List[str], 
                          embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        """
        Add documents to FAISS vector store (placeholder)
        """
        # TODO: Implement FAISS storage
        raise NotImplementedError("FAISS storage not yet implemented")
    
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        """
        try:
            # Get query embedding
            query_embedding = await self.gemini_client.get_embeddings([query])
            query_vector = query_embedding[0]
            
            if self.vector_store_type == "chroma":
                return await self._search_chroma(query_vector, k)
            elif self.vector_store_type == "faiss":
                return await self._search_faiss(query_vector, k)
            
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
            
            if self.vector_store_type == "chroma":
                return await self._search_chroma_with_filter(query_vector, filter_dict, k)
            elif self.vector_store_type == "faiss":
                return await self._search_faiss_with_filter(query_vector, filter_dict, k)
            
        except Exception as e:
            logger.error(f"Error in filtered similarity search: {str(e)}")
            raise
    
    async def _search_chroma(self, query_vector: List[float], k: int) -> List[Dict[str, Any]]:
        """
        Search Chroma vector store
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=k
            )
            
            # Format results
            documents = []
            for i in range(len(results['documents'][0])):
                doc = {
                    "page_content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'][0] else {},
                    "distance": results['distances'][0][i] if results['distances'][0] else 0.0
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching Chroma: {str(e)}")
            raise
    
    async def _search_chroma_with_filter(self, query_vector: List[float], filter_dict: Dict[str, Any], k: int) -> List[Dict[str, Any]]:
        """
        Search Chroma vector store with filter
        """
        try:
            # Build where clause for Chroma
            where_clause = {}
            for key, value in filter_dict.items():
                where_clause[key] = {"$eq": value}
            
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=k,
                where=where_clause
            )
            
            # Format results
            documents = []
            for i in range(len(results['documents'][0])):
                doc = {
                    "page_content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'][0] else {},
                    "distance": results['distances'][0][i] if results['distances'][0] else 0.0
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching Chroma with filter: {str(e)}")
            raise
    
    async def _search_faiss(self, query_vector: List[float], k: int) -> List[Dict[str, Any]]:
        """
        Search FAISS vector store (placeholder)
        """
        # TODO: Implement FAISS search
        raise NotImplementedError("FAISS search not yet implemented")
    
    async def _search_faiss_with_filter(self, query_vector: List[float], filter_dict: Dict[str, Any], k: int) -> List[Dict[str, Any]]:
        """
        Search FAISS vector store with filter (placeholder)
        """
        # TODO: Implement FAISS search with filter
        raise NotImplementedError("FAISS search with filter not yet implemented")
    
    async def delete_by_metadata(self, filter_dict: Dict[str, Any]) -> None:
        """
        Delete documents by metadata filter
        """
        try:
            if self.vector_store_type == "chroma":
                # Build where clause for Chroma
                where_clause = {}
                for key, value in filter_dict.items():
                    where_clause[key] = {"$eq": value}
                
                # Get documents to delete
                results = self.collection.get(where=where_clause)
                
                if results['ids']:
                    # Delete documents
                    self.collection.delete(ids=results['ids'])
                    logger.info(f"Deleted {len(results['ids'])} documents from vector store")
                else:
                    logger.info("No documents found matching filter criteria")
                    
            elif self.vector_store_type == "faiss":
                # TODO: Implement FAISS deletion
                raise NotImplementedError("FAISS deletion not yet implemented")
                
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        """
        try:
            if self.vector_store_type == "chroma":
                count = self.collection.count()
                return {
                    "vector_store_type": "chroma",
                    "document_count": count,
                    "collection_name": "rag_documents"
                }
            elif self.vector_store_type == "faiss":
                # TODO: Implement FAISS stats
                return {
                    "vector_store_type": "faiss",
                    "document_count": "unknown",
                    "status": "not implemented"
                }
                
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)} 