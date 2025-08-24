# MongoDB Atlas Migration Guide

This guide will help you migrate your RAG Chatbot API from ChromaDB to MongoDB Atlas for better scalability and performance.

## Prerequisites

1. **MongoDB Atlas Account**: Sign up at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. **MongoDB Atlas Cluster**: Create a new cluster (M0 free tier is sufficient for testing)
3. **Vector Search Enabled**: Ensure your cluster supports vector search (available on M10+ clusters)

## Step 1: Set Up MongoDB Atlas

### 1.1 Create a MongoDB Atlas Cluster

1. Log in to MongoDB Atlas
2. Create a new project (if needed)
3. Build a new cluster:
   - Choose **M10** or higher for vector search support
   - Select your preferred cloud provider and region
   - Choose cluster name (e.g., "rag-chatbot-cluster")

### 1.2 Configure Network Access

1. Go to **Network Access** in the left sidebar
2. Click **Add IP Address**
3. Add your current IP address or use `0.0.0.0/0` for development (not recommended for production)

### 1.3 Create Database User

1. Go to **Database Access** in the left sidebar
2. Click **Add New Database User**
3. Create a user with **Read and write to any database** permissions
4. Save the username and password

### 1.4 Get Connection String

1. Go to **Database** in the left sidebar
2. Click **Connect**
3. Choose **Connect your application**
4. Copy the connection string
5. Replace `<password>` with your database user password
6. Replace `<dbname>` with your desired database name (e.g., `rag_chatbot`)

## Step 2: Update Environment Configuration

### 2.1 Update .env File

Add the following MongoDB configuration to your `.env` file:

```env
# Vector Store Configuration
VECTOR_STORE_TYPE=mongodb

# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/rag_chatbot?retryWrites=true&w=majority
MONGODB_DATABASE=rag_chatbot
MONGODB_COLLECTION=documents
```

**Important**: Replace the connection string with your actual MongoDB Atlas connection string.

### 2.2 Install Dependencies

Install the required MongoDB dependencies:

```bash
pip install pymongo motor
```

Or update your requirements:

```bash
pip install -r requirements.in
```

## Step 3: Set Up MongoDB Atlas

### 3.1 Run the Setup Script

Use the provided setup script to configure MongoDB Atlas:

```bash
python setup_mongodb.py
```

This script will:
- Validate your MongoDB Atlas connection
- Create necessary indexes for efficient querying
- Create a vector search index for embeddings
- Test the vector search functionality

### 3.2 Manual Index Creation (Alternative)

If the setup script doesn't work, you can create indexes manually:

1. **Vector Search Index**: In MongoDB Atlas, go to your collection and create a search index:
   ```json
   {
     "mappings": {
       "dynamic": true,
       "fields": {
         "embedding": {
           "dimensions": 768,
           "similarity": "cosine",
           "type": "knnVector"
         }
       }
     }
   }
   ```

2. **Regular Indexes**: Create indexes on:
   - `file_id` (ascending)
   - `filename` (ascending)
   - `created_at` (ascending)
   - `content` (text)

## Step 4: Data Migration (Optional)

If you have existing data in ChromaDB that you want to migrate:

### 4.1 Export ChromaDB Data

```python
import chromadb
import json

# Connect to existing ChromaDB
client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_collection("rag_documents")

# Get all documents
results = collection.get()
documents = []

for i in range(len(results['ids'])):
    doc = {
        'id': results['ids'][i],
        'content': results['documents'][i],
        'metadata': results['metadatas'][i] if results['metadatas'] else {},
        'embedding': results['embeddings'][i] if results['embeddings'] else []
    }
    documents.append(doc)

# Save to JSON file
with open('chromadb_export.json', 'w') as f:
    json.dump(documents, f, indent=2)
```

### 4.2 Import to MongoDB Atlas

```python
import asyncio
import json
from retriever.mongodb_vectorstore import MongoDBVectorStore

async def migrate_data():
    # Load exported data
    with open('chromadb_export.json', 'r') as f:
        documents = json.load(f)
    
    # Initialize MongoDB vector store
    vector_store = MongoDBVectorStore()
    
    # Migrate documents
    for doc in documents:
        await vector_store.add_documents(
            [doc['content']], 
            doc['metadata']
        )
    
    print(f"Migrated {len(documents)} documents")

# Run migration
asyncio.run(migrate_data())
```

## Step 5: Test the Migration

### 5.1 Test API Endpoints

1. **Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should show `"vector_store": "mongodb_atlas"`

2. **File Upload**:
   ```bash
   curl -X POST "http://localhost:8000/api/v2/file" \
     -F "file=@test_document.pdf"
   ```

3. **Text Query**:
   ```bash
   curl -X POST "http://localhost:8000/api/v2/text" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is machine learning?"}'
   ```

4. **List Files**:
   ```bash
   curl http://localhost:8000/api/v2/files
   ```

### 5.2 Verify Data in MongoDB Atlas

1. Go to your MongoDB Atlas cluster
2. Navigate to **Browse Collections**
3. Check that documents are being stored with embeddings
4. Verify that vector search queries work

## Step 6: Performance Optimization

### 6.1 Monitor Performance

- Use MongoDB Atlas **Performance Advisor** to identify slow queries
- Monitor **Metrics** to track database performance
- Set up **Alerts** for important metrics

### 6.2 Optimize Indexes

- Ensure vector search index is created and active
- Monitor index usage and remove unused indexes
- Consider compound indexes for complex queries

### 6.3 Connection Pooling

The MongoDB driver automatically handles connection pooling. For production:

```python
# In your MongoDB configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/rag_chatbot?retryWrites=true&w=majority&maxPoolSize=10&minPoolSize=5
```

## Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Check your MongoDB Atlas connection string
   - Verify network access settings
   - Ensure database user has correct permissions

2. **Vector Search Not Working**:
   - Verify you're using M10+ cluster
   - Check that vector search index is created
   - Ensure embeddings have correct dimensions (768 for Gemini)

3. **Index Creation Failed**:
   - Check cluster tier supports vector search
   - Verify collection exists
   - Check user permissions

4. **Performance Issues**:
   - Monitor MongoDB Atlas metrics
   - Check index usage
   - Consider upgrading cluster tier

### Error Messages

- **"Vector search index not found"**: Run the setup script or create index manually
- **"Connection timeout"**: Check network access and connection string
- **"Authentication failed"**: Verify username and password in connection string

## Benefits of MongoDB Atlas

1. **Scalability**: Automatic scaling based on usage
2. **Reliability**: 99.95% uptime SLA
3. **Security**: Built-in security features
4. **Monitoring**: Comprehensive monitoring and alerting
5. **Backup**: Automated backups and point-in-time recovery
6. **Global Distribution**: Multi-region deployment options

## Cost Considerations

- **M0 (Free)**: 512MB storage, shared RAM (no vector search)
- **M10**: $57/month, 10GB storage, 2GB RAM, vector search support
- **M20**: $114/month, 20GB storage, 4GB RAM, vector search support

For production use, M10 or higher is recommended for vector search functionality.

## Next Steps

1. **Production Deployment**: Configure proper security settings
2. **Monitoring**: Set up alerts and monitoring
3. **Backup Strategy**: Configure automated backups
4. **Performance Tuning**: Optimize based on usage patterns
5. **Security**: Implement proper authentication and authorization

## Support

- **MongoDB Atlas Documentation**: [docs.mongodb.com/atlas](https://docs.mongodb.com/atlas)
- **Vector Search Guide**: [docs.mongodb.com/atlas/atlas-vector-search](https://docs.mongodb.com/atlas/atlas-vector-search)
- **Community Support**: [community.mongodb.com](https://community.mongodb.com)
