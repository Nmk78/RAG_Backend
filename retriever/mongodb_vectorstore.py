import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
import motor.motor_asyncio
from pymongo import MongoClient
import numpy as np
from datetime import datetime
import uuid

from config import Config
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class MongoDBVectorStore:
    """
    Vector store for document storage and retrieval using MongoDB Atlas
    """
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.mongo_uri = Config.MONGODB_URI
        self.database_name = Config.MONGODB_DATABASE
        self.collection_name = Config.MONGODB_COLLECTION
        
        # Initialize MongoDB connection
        self._init_mongodb()
        
    def _init_mongodb(self):
        """
        Initialize MongoDB Atlas connection
        """
        try:
            # Create async motor client
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Create sync client for operations that don't support async
            self.sync_client = MongoClient(self.mongo_uri)
            self.sync_db = self.sync_client[self.database_name]
            self.sync_collection = self.sync_db[self.collection_name]
            
            # Create indexes for efficient querying
            self._create_indexes()
            
            logger.info(f"MongoDB Atlas vector store initialized successfully - Database: {self.database_name}, Collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing MongoDB Atlas: {str(e)}")
            raise
    
    def _create_indexes(self):
        """
        Create necessary indexes for vector search and metadata filtering
        """
        try:
            # Create index on file_id for efficient filtering
            self.sync_collection.create_index("file_id")
            
            # Create index on filename for efficient filtering
            self.sync_collection.create_index("filename")
            
            # Create index on created_at for time-based queries
            self.sync_collection.create_index("created_at")
            
            # Create text index for basic text search (optional)
            self.sync_collection.create_index([("content", "text")])
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {str(e)}")
    
    async def add_documents(self, documents: List[str], metadata: Dict[str, Any] = None) -> None:
        """
        Add documents to MongoDB Atlas vector store
        """
        try:
            if not documents:
                return
            
            # Generate embeddings for documents
            embeddings = await self.gemini_client.get_embeddings(documents)
            
            # Prepare documents for storage
            documents_to_insert = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                doc_id = str(uuid.uuid4())
                doc_data = {
                    "_id": doc_id,
                    "content": doc,
                    "embedding": embedding,
                    "created_at": datetime.utcnow(),
                    "metadata": metadata or {}
                }
                
                # Add metadata fields as top-level for easier querying
                if metadata:
                    for key, value in metadata.items():
                        doc_data[key] = value
                
                documents_to_insert.append(doc_data)
            
            # Insert documents
            if documents_to_insert:
                result = await self.collection.insert_many(documents_to_insert)
                logger.info(f"Added {len(result.inserted_ids)} documents to MongoDB Atlas")
            
        except Exception as e:
            logger.error(f"Error adding documents to MongoDB Atlas: {str(e)}")
            raise
    
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        """
        try:
            # Get query embedding
            query_embedding = await self.gemini_client.get_embeddings([query])
            query_vector = query_embedding[0]
            
            # Perform vector similarity search
            pipeline = [
                {
                    "$vectorSearch": {
                        "queryVector": query_vector,
                        "path": "embedding",
                        "numCandidates": k * 10,  # Get more candidates for better results
                        "limit": k,
                        "index": "vector_index"
                    }
                },
                {
                    "$project": {
                        "content": 1,
                        "metadata": 1,
                        "filename": 1,
                        "file_id": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=k)
            
            # Format results
            documents = []
            for result in results:
                doc = {
                    "page_content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "distance": 1 - result.get("score", 0),  # Convert score to distance
                    "filename": result.get("filename", ""),
                    "file_id": result.get("file_id", "")
                }
                documents.append(doc)
            
            if documents:
                logger.info(f"Vector search found {len(documents)} documents for query: {query}")
                return documents
            else:
                logger.warning(f"Vector search returned no results for query: {query}, trying fallback")
                return await self._fallback_text_search(query, k)
            
        except Exception as e:
            logger.error(f"Error in MongoDB similarity search: {str(e)}")
            logger.info(f"Falling back to text search for query: {query}")
            # Fallback to basic text search if vector search fails
            return await self._fallback_text_search(query, k)
    
    async def _fallback_text_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """
        Fallback to basic text search if vector search is not available
        """
        try:
            # First try text search
            try:
                cursor = self.collection.find(
                    {"$text": {"$search": query}},
                    {"score": {"$meta": "textScore"}}
                ).sort([("score", {"$meta": "textScore"})]).limit(k)
                
                results = await cursor.to_list(length=k)
                
                if results:
                    documents = []
                    for result in results:
                        doc = {
                            "page_content": result.get("content", ""),
                            "metadata": result.get("metadata", {}),
                            "distance": 1 - (result.get("score", 0) / 10),  # Normalize score
                            "filename": result.get("filename", ""),
                            "file_id": result.get("file_id", "")
                        }
                        documents.append(doc)
                    
                    logger.info(f"Text search found {len(documents)} documents for query: {query}")
                    return documents
                    
            except Exception as text_search_error:
                logger.warning(f"Text search failed, trying regex search: {text_search_error}")
            
            # Fallback to regex search if text search fails
            cursor = self.collection.find(
                {"content": {"$regex": query, "$options": "i"}}
            ).limit(k)
            
            results = await cursor.to_list(length=k)
            
            documents = []
            for result in results:
                doc = {
                    "page_content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "distance": 0.5,  # Default distance for regex matches
                    "filename": result.get("filename", ""),
                    "file_id": result.get("file_id", "")
                }
                documents.append(doc)
            
            logger.info(f"Regex search found {len(documents)} documents for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Error in fallback text search: {str(e)}")
            return []
    
    async def similarity_search_with_filter(self, query: str, filter_dict: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents with metadata filter
        """
        try:
            # Get query embedding
            query_embedding = await self.gemini_client.get_embeddings([query])
            query_vector = query_embedding[0]
            
            # Build match stage for filtering
            match_stage = {}
            for key, value in filter_dict.items():
                match_stage[key] = value
            
            # Perform filtered vector similarity search
            pipeline = [
                {"$match": match_stage},
                {
                    "$vectorSearch": {
                        "queryVector": query_vector,
                        "path": "embedding",
                        "numCandidates": k * 10,
                        "limit": k,
                        "index": "vector_index"
                    }
                },
                {
                    "$project": {
                        "content": 1,
                        "metadata": 1,
                        "filename": 1,
                        "file_id": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=k)
            
            # Format results
            documents = []
            for result in results:
                doc = {
                    "page_content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "distance": 1 - result.get("score", 0),
                    "filename": result.get("filename", ""),
                    "file_id": result.get("file_id", "")
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error in filtered MongoDB similarity search: {str(e)}")
            return await self._fallback_filtered_search(query, filter_dict, k)
    
    async def _fallback_filtered_search(self, query: str, filter_dict: Dict[str, Any], k: int) -> List[Dict[str, Any]]:
        """
        Fallback to filtered text search
        """
        try:
            # Build filter query
            filter_query = {}
            for key, value in filter_dict.items():
                filter_query[key] = value
            
            # Add text search
            filter_query["$text"] = {"$search": query}
            
            cursor = self.collection.find(
                filter_query,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(k)
            
            results = await cursor.to_list(length=k)
            
            documents = []
            for result in results:
                doc = {
                    "page_content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "distance": 1 - (result.get("score", 0) / 10),
                    "filename": result.get("filename", ""),
                    "file_id": result.get("file_id", "")
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error in fallback filtered search: {str(e)}")
            return []
    
    async def delete_by_metadata(self, filter_dict: Dict[str, Any]) -> None:
        """
        Delete documents by metadata filter
        """
        try:
            # Build filter query
            filter_query = {}
            for key, value in filter_dict.items():
                filter_query[key] = value
            
            # Delete documents
            result = await self.collection.delete_many(filter_query)
            
            logger.info(f"Deleted {result.deleted_count} documents from MongoDB Atlas")
            
        except Exception as e:
            logger.error(f"Error deleting documents from MongoDB Atlas: {str(e)}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the MongoDB collection
        """
        try:
            # Get document count
            count = await self.collection.count_documents({})
            
            # Get unique file count
            unique_files = await self.collection.distinct("file_id")
            
            # Get storage stats
            stats = await self.db.command("collstats", self.collection_name)
            
            return {
                "vector_store_type": "mongodb_atlas",
                "database": self.database_name,
                "collection": self.collection_name,
                "document_count": count,
                "unique_files": len(unique_files),
                "storage_size_bytes": stats.get("size", 0),
                "index_size_bytes": stats.get("totalIndexSize", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting MongoDB collection stats: {str(e)}")
            return {"error": str(e)}
    
    async def list_files(self) -> List[Dict[str, Any]]:
        """
        List all unique files in the collection
        """
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$file_id",
                        "filename": {"$first": "$filename"},
                        "document_count": {"$sum": 1},
                        "created_at": {"$first": "$created_at"}
                    }
                },
                {"$sort": {"created_at": -1}}
            ]
            
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            files = []
            for result in results:
                file_info = {
                    "file_id": result["_id"],
                    "filename": result["filename"],
                    "document_count": result["document_count"],
                    "created_at": result["created_at"]
                }
                files.append(file_info)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files from MongoDB Atlas: {str(e)}")
            return []
    
    async def close(self):
        """
        Close MongoDB connections
        """
        try:
            self.client.close()
            self.sync_client.close()
            logger.info("MongoDB connections closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connections: {str(e)}")
