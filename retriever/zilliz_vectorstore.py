import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import numpy as np
from datetime import datetime
import uuid

from config import Config
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class ZillizVectorStore:
    """
    Vector store for document storage and retrieval using Zilliz Cloud (Milvus)
    """
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.collection_name = "rag_documents"
        self.dimension = 3072  # Gemini embedding-001 model dimensions
        
        # Initialize Zilliz connection
        self._init_zilliz()
        
    def _init_zilliz(self):
        """
        Initialize Zilliz Cloud connection
        """
        try:
            # Get Zilliz credentials from environment
            zilliz_uri = Config.ZILLIZ_URI
            zilliz_token = Config.ZILLIZ_TOKEN
            
            if not zilliz_uri or not zilliz_token:
                raise ValueError("ZILLIZ_URI and ZILLIZ_TOKEN must be set in environment variables")
            
            # Connect to Zilliz Cloud
            connections.connect(
                alias="default",
                uri=zilliz_uri,
                token=zilliz_token
            )
            
            logger.info("✅ Connected to Zilliz Cloud successfully")
            
            # Create collection if it doesn't exist
            self._create_collection()
            
        except Exception as e:
            logger.error(f"Error initializing Zilliz Cloud: {str(e)}")
            raise
    
    def _create_collection(self):
        """
        Create the collection for document storage
        """
        try:
            if utility.has_collection(self.collection_name):
                logger.info(f"Collection '{self.collection_name}' already exists")
                # Check if dimensions match
                existing_collection = Collection(self.collection_name)
                schema = existing_collection.schema
                
                # Find embedding field
                embedding_field = None
                for field in schema.fields:
                    if field.name == "embedding":
                        embedding_field = field
                        break
                
                if embedding_field and embedding_field.params.get("dim") == self.dimension:
                    logger.info(f"Collection '{self.collection_name}' exists with correct dimensions")
                    self.collection = existing_collection
                    return
                else:
                    logger.warning(f"Collection exists but dimensions don't match. Dropping and recreating...")
                    utility.drop_collection(self.collection_name)
            
            # Define collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
                FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=30),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=4096)
            ]
            
            schema = CollectionSchema(fields=fields, description="RAG documents collection")
            
            # Create collection
            self.collection = Collection(
                name=self.collection_name,
                schema=schema,
                using="default"
            )
            
            # Create index for vector search
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            logger.info(f"✅ Created collection '{self.collection_name}' with vector index")
            
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise
    
    async def add_documents(self, documents: List[str], metadata: Dict[str, Any] = None) -> None:
        """
        Add documents to Zilliz Cloud vector store
        """
        try:
            if not documents:
                return
            
            # Generate embeddings for documents
            embeddings = await self.gemini_client.get_embeddings(documents)
            
            # Prepare data for insertion
            ids = []
            contents = []
            embedding_vectors = []
            file_ids = []
            filenames = []
            created_ats = []
            metadata_list = []
            
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                doc_id = str(uuid.uuid4())
                
                ids.append(doc_id)
                contents.append(doc)
                embedding_vectors.append(embedding)
                file_ids.append(metadata.get("file_id", "") if metadata else "")
                filenames.append(metadata.get("filename", "") if metadata else "")
                created_ats.append(datetime.now(ZoneInfo("Asia/Yangon")).isoformat())
                metadata_list.append(str(metadata) if metadata else "{}")
            
            # Insert data into collection
            data = [
                ids,
                contents,
                embedding_vectors,
                file_ids,
                filenames,
                created_ats,
                metadata_list
            ]
            
            self.collection.insert(data)
            self.collection.flush()
            
            logger.info(f"✅ Added {len(documents)} documents to Zilliz Cloud")
            
        except Exception as e:
            logger.error(f"Error adding documents to Zilliz Cloud: {str(e)}")
            raise
    
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        """
        try:
            # Get query embedding
            query_embedding = await self.gemini_client.get_embeddings([query])
            query_vector = query_embedding[0]
            
            # Load collection
            self.collection.load()
            
            # Perform vector search
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=k,
                output_fields=["content", "file_id", "filename", "metadata"]
            )
            
            # Format results
            documents = []
            for hits in results:
                for hit in hits:
                    doc = {
                        "page_content": hit.entity.get("content", ""),
                        "metadata": eval(hit.entity.get("metadata", "{}")),
                        "distance": 1 - hit.score,  # Convert score to distance
                        "filename": hit.entity.get("filename", ""),
                        "file_id": hit.entity.get("file_id", "")
                    }
                    documents.append(doc)
            
            logger.info(f"✅ Vector search found {len(documents)} documents for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Error in Zilliz similarity search: {str(e)}")
            return []
    
    async def similarity_search_with_filter(self, query: str, filter_dict: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents with metadata filter
        """
        try:
            # Get query embedding
            query_embedding = await self.gemini_client.get_embeddings([query])
            query_vector = query_embedding[0]
            
            # Load collection
            self.collection.load()
            
            # Build filter expression
            filter_expr = ""
            for key, value in filter_dict.items():
                if filter_expr:
                    filter_expr += " and "
                filter_expr += f'{key} == "{value}"'
            
            # Perform filtered vector search
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=k,
                expr=filter_expr,
                output_fields=["content", "file_id", "filename", "metadata"]
            )
            
            # Format results
            documents = []
            for hits in results:
                for hit in hits:
                    doc = {
                        "page_content": hit.entity.get("content", ""),
                        "metadata": eval(hit.entity.get("metadata", "{}")),
                        "distance": 1 - hit.score,
                        "filename": hit.entity.get("filename", ""),
                        "file_id": hit.entity.get("file_id", "")
                    }
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error in filtered Zilliz search: {str(e)}")
            return []
    
    async def delete_by_metadata(self, filter_dict: Dict[str, Any]) -> None:
        """
        Delete documents by metadata filter
        """
        try:
            # Build filter expression
            filter_expr = ""
            for key, value in filter_dict.items():
                if filter_expr:
                    filter_expr += " and "
                filter_expr += f'{key} == "{value}"'
            
            # Delete documents
            self.collection.delete(filter_expr)
            self.collection.flush()
            
            logger.info(f"✅ Deleted documents with filter: {filter_dict}")
            
        except Exception as e:
            logger.error(f"Error deleting documents from Zilliz: {str(e)}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Zilliz collection
        """
        try:
            # Get collection statistics
            stats = self.collection.get_statistics()
            
            return {
                "vector_store_type": "zilliz_cloud",
                "collection_name": self.collection_name,
                "document_count": stats.get("row_count", 0),
                "dimension": self.dimension
            }
            
        except Exception as e:
            logger.error(f"Error getting Zilliz collection stats: {str(e)}")
            return {"error": str(e)}
    
    async def list_files(self) -> List[Dict[str, Any]]:
        """
        List all unique files in the collection
        """
        try:
            # Query to get unique files
            results = self.collection.query(
                expr="",
                output_fields=["file_id", "filename", "created_at"],
                limit=1000
            )
            
            # Group by file_id
            files = {}
            for result in results:
                file_id = result.get("file_id")
                if file_id and file_id not in files:
                    files[file_id] = {
                        "file_id": file_id,
                        "filename": result.get("filename", ""),
                        "created_at": result.get("created_at", "")
                    }
            
            return list(files.values())
            
        except Exception as e:
            logger.error(f"Error listing files from Zilliz: {str(e)}")
            return []
    
    async def list_files_paginated(self, page: int = 1, page_size: int = 10, 
                                 order_by: str = "created_at", order_direction: str = "desc") -> Dict[str, Any]:
        """
        List unique files in the collection with pagination and ordering
        """
        try:
            # Validate order_by field
            valid_order_fields = ["created_at", "filename", "file_id"]
            if order_by not in valid_order_fields:
                order_by = "created_at"
            
            # Validate order_direction
            if order_direction.lower() not in ["asc", "desc"]:
                order_direction = "desc"
            
            # Query to get all unique files first (we need to do client-side pagination due to Milvus limitations)
            results = self.collection.query(
                expr="",
                output_fields=["file_id", "filename", "created_at"],
                limit=10000  # Get a large number to handle pagination client-side
            )
            
            # Group by file_id to get unique files
            files = {}
            for result in results:
                file_id = result.get("file_id")
                if file_id and file_id not in files:
                    files[file_id] = {
                        "file_id": file_id,
                        "filename": result.get("filename", ""),
                        "created_at": result.get("created_at", "")
                    }
            
            # Convert to list and sort
            files_list = list(files.values())
            
            # Sort based on order_by and order_direction
            reverse_order = order_direction.lower() == "desc"
            if order_by == "created_at":
                files_list.sort(key=lambda x: x.get("created_at", ""), reverse=reverse_order)
            elif order_by == "filename":
                files_list.sort(key=lambda x: x.get("filename", "").lower(), reverse=reverse_order)
            elif order_by == "file_id":
                files_list.sort(key=lambda x: x.get("file_id", ""), reverse=reverse_order)
            
            # Calculate pagination
            total_count = len(files_list)
            total_pages = (total_count + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            # Get the page slice
            paginated_files = files_list[start_idx:end_idx]
            
            return {
                "files": paginated_files,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"Error listing files with pagination from Zilliz: {str(e)}")
            return {
                "files": [],
                "total_count": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "error": str(e)
            }
    
    async def search_files(self, query: str, search_type: str = "filename", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search files by different criteria for admin management
        """
        try:
            # Validate search_type
            valid_search_types = ["filename", "file_id", "content"]
            if search_type not in valid_search_types:
                search_type = "filename"
            
            if search_type == "content":
                # For content search, use vector similarity search
                logger.info(f"Performing content search for query: {query}")
                
                # Generate embedding for query
                query_embedding = await self.gemini_client.get_embeddings([query])
                query_vector = query_embedding[0]
                logger.info(f"Generated embedding vector of dimension: {len(query_vector)}")
                
                # Ensure collection is loaded
                self.collection.load()
                logger.info("Collection loaded for search")
                
                # Check if collection has data
                try:
                    row_count = self.collection.num_entities
                    logger.info(f"Collection has {row_count} entities")
                except Exception as e:
                    logger.warning(f"Could not get entity count: {e}")
                
                # Perform vector search with adjusted parameters
                search_params = {
                    "metric_type": "COSINE",
                    "params": {"nprobe": 16}
                }
                
                results = self.collection.search(
                    data=[query_vector],
                    anns_field="embedding",
                    param=search_params,
                    limit=limit * 2,  # Get more results to account for grouping
                    output_fields=["content", "file_id", "filename", "created_at", "metadata"]
                )
                
                logger.info(f"Vector search returned {len(results)} result sets")
                
                # Format results and group by file
                files = {}
                total_hits = 0
                for hits in results:
                    total_hits += len(hits)
                    logger.info(f"Processing {len(hits)} hits")
                    for hit in hits:
                        file_id = hit.entity.get("file_id", "")
                        content = hit.entity.get("content", "")
                        score = float(hit.score)
                        
                        logger.info(f"Hit: file_id={file_id}, score={score}, content_length={len(content)}")
                        
                        # Only include results with reasonable similarity scores
                        if file_id and score > 0.1:  # Adjust threshold as needed
                            if file_id not in files:
                                files[file_id] = {
                                    "file_id": file_id,
                                    "filename": hit.entity.get("filename", ""),
                                    "created_at": hit.entity.get("created_at", ""),
                                    "relevance_score": score,
                                    "matched_content": content[:200] + "..." if len(content) > 200 else content
                                }
                            elif score > files[file_id]["relevance_score"]:
                                # Update with better match from same file
                                files[file_id]["relevance_score"] = score
                                files[file_id]["matched_content"] = content[:200] + "..." if len(content) > 200 else content
                
                logger.info(f"Total hits processed: {total_hits}, unique files found: {len(files)}")
                
                # Sort by relevance score
                sorted_files = sorted(files.values(), key=lambda x: x["relevance_score"], reverse=True)
                return sorted_files[:limit]
            
            else:
                # For filename and file_id search, use query with filter
                if search_type == "filename":
                    # Use LIKE operation for filename search
                    expr = f'filename like "%{query}%"'
                elif search_type == "file_id":
                    # Exact or partial match for file_id
                    expr = f'file_id like "%{query}%"'
                
                results = self.collection.query(
                    expr=expr,
                    output_fields=["file_id", "filename", "created_at"],
                    limit=limit
                )
                
                # Group by file_id to get unique files
                files = {}
                for result in results:
                    file_id = result.get("file_id")
                    if file_id and file_id not in files:
                        files[file_id] = {
                            "file_id": file_id,
                            "filename": result.get("filename", ""),
                            "created_at": result.get("created_at", "")
                        }
                
                return list(files.values())
            
        except Exception as e:
            logger.error(f"Error searching files in Zilliz: {str(e)}")
            return []
    
    async def close(self):
        """
        Close Zilliz connection
        """
        try:
            connections.disconnect("default")
            logger.info("Zilliz connection closed")
        except Exception as e:
            logger.error(f"Error closing Zilliz connection: {str(e)}")
