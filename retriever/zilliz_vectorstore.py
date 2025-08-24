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
                created_ats.append(datetime.utcnow().isoformat())
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
    
    async def close(self):
        """
        Close Zilliz connection
        """
        try:
            connections.disconnect("default")
            logger.info("Zilliz connection closed")
        except Exception as e:
            logger.error(f"Error closing Zilliz connection: {str(e)}")
