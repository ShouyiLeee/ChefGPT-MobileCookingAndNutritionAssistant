# RAG Pipeline for Recipe Retrieval

## Overview

This RAG (Retrieval Augmented Generation) pipeline provides semantic search capabilities for recipes using OpenAI embeddings and PostgreSQL with pgvector.

## Architecture

```
┌─────────────────┐
│  User Query     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Embedding       │  ← OpenAI text-embedding-3-large
│ Generation      │     (3072 dimensions)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Search   │  ← PostgreSQL + pgvector
│ (Cosine Sim)    │     HNSW index for fast search
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Results         │
│ + Scores        │
└─────────────────┘
```

## Components

### 1. Embedding Service (`app/rag/embeddings/`)

**`embedding_service.py`**: Generates embeddings using OpenAI
- Single embedding generation
- Batch processing (up to 100 texts)
- Automatic text cleaning and truncation
- Similarity computation

```python
from app.rag.embeddings import embedding_service

# Generate embedding
embedding = await embedding_service.generate_embedding("Vietnamese pho recipe")

# Batch generation
embeddings = await embedding_service.generate_embeddings_batch(texts)
```

**`text_chunker.py`**: Splits long text into searchable chunks
- Overlapping chunks with configurable size
- Sentence-boundary splitting
- Paragraph-based chunking

```python
from app.rag.embeddings import text_chunker

chunks = text_chunker.chunk_text(text, chunk_size=1000, chunk_overlap=200)
```

### 2. Vector Search (`app/rag/vectorstore/`)

**`vector_search.py`**: Semantic similarity search
- Cosine similarity with pgvector
- Filtered search (cuisine, difficulty, time)
- Hybrid search (semantic + keyword)
- Similar recipe recommendations

```python
from app.rag.vectorstore import vector_search

# Semantic search
results = await vector_search.search_by_text(
    query_text="healthy breakfast",
    session=session,
    limit=10,
)

# Search by ingredients
results = await vector_search.search_by_ingredients(
    ingredients=["chicken", "rice", "vegetables"],
    session=session,
)

# Find similar recipes
similar = await vector_search.find_similar_recipes(
    recipe_id=123,
    session=session,
)
```

### 3. Recipe Services (`app/services/recipe/`)

**`recipe_indexer.py`**: Indexes recipes with embeddings
- Single recipe indexing
- Batch indexing (50 recipes at a time)
- Full reindexing
- Embedding removal

```python
from app.services.recipe import recipe_indexer

# Index a recipe
await recipe_indexer.index_recipe(recipe, session)

# Batch indexing
results = await recipe_indexer.index_recipes_batch([1, 2, 3], session)

# Reindex all
results = await recipe_indexer.reindex_all_recipes(session)
```

**`recipe_retriever.py`**: High-level retrieval service
- Query-based search
- Ingredient-based search
- Contextual search (with user preferences)
- Recommendations

```python
from app.services.recipe import recipe_retriever

# Find recipes by query
results = await recipe_retriever.find_recipes_by_query(
    query="quick dinner",
    session=session,
    limit=10,
)

# Find by ingredients
results = await recipe_retriever.find_recipes_by_ingredients(
    ingredients=["tomato", "pasta", "cheese"],
    session=session,
)
```

### 4. LLM Tools (`app/llm/tools/`)

**`recipe_rag_tool.py`**: RAG-powered tools for LLM agents
- Semantic recipe search
- Ingredient matching
- Similar recipe lookup
- Contextual search

These tools can be used by LLM agents (GPT-4, Claude) for function calling.

## API Endpoints

### Semantic Search

```http
GET /recipes/search/semantic?q=healthy+breakfast&limit=10
```

Returns recipes matching the semantic meaning of the query.

**Example Response:**
```json
[
  {
    "id": 1,
    "title": "Oatmeal with Fruits",
    "match_score": 0.92,
    "match_reason": "healthy ingredients, breakfast category"
  }
]
```

### Search by Ingredients

```http
GET /recipes/search/by-ingredients?ingredients=chicken,rice,tomato&min_match=0.5
```

Finds recipes you can make with available ingredients.

**Example Response:**
```json
[
  {
    "id": 5,
    "title": "Chicken Fried Rice",
    "match_percentage": 85,
    "available_ingredients": ["chicken", "rice"],
    "missing_ingredients": ["soy sauce"],
    "can_make": false,
    "substitution_possible": true
  }
]
```

### Similar Recipes

```http
GET /recipes/search/123/similar?limit=5
```

Get recipes similar to recipe #123.

### Personalized Search

```http
GET /recipes/search/personalized?q=dinner
Authorization: Bearer <token>
```

Search with user preferences (dietary restrictions, goals, etc.).

## Database Schema

### Vector Column

```sql
ALTER TABLE recipes ADD COLUMN embedding vector(3072);
```

### Vector Index (HNSW)

```sql
CREATE INDEX recipes_embedding_idx
ON recipes
USING hnsw (embedding vector_cosine_ops);
```

HNSW (Hierarchical Navigable Small World) provides fast approximate nearest neighbor search.

## Usage Examples

### 1. Index New Recipe

```python
# Create recipe
recipe = Recipe(
    title="Phở Bò",
    description="Vietnamese beef noodle soup...",
    cuisine="vietnamese",
    # ... other fields
)
session.add(recipe)
await session.commit()

# Generate embedding
await recipe_indexer.index_recipe(recipe, session)
```

### 2. Search for Recipes

```python
# Semantic search
results = await vector_search.search_by_text(
    query_text="spicy Thai curry",
    session=session,
    limit=5,
    threshold=0.7,
)

for recipe, score in results:
    print(f"{recipe.title}: {score:.2f}")
```

### 3. Ingredient Matching

```python
# User has these ingredients
user_ingredients = ["chicken", "coconut milk", "curry paste"]

# Find matching recipes
results = await recipe_retriever.find_recipes_by_ingredients(
    ingredients=user_ingredients,
    session=session,
    min_match_percentage=0.6,
)

for result in results:
    print(f"{result['recipe'].title}")
    print(f"Match: {result['match_percentage']:.0%}")
    print(f"Missing: {result['missing_ingredients']}")
```

## Scripts

### Seed Sample Recipes

```bash
cd backend
python scripts/seed_recipes.py
```

Seeds 10 sample Vietnamese recipes and generates embeddings.

### Reindex All Recipes

```bash
python scripts/reindex_recipes.py
```

Regenerates embeddings for all recipes in the database.

## Performance

### Embedding Generation

- Single embedding: ~100-200ms
- Batch of 50: ~2-3 seconds
- Rate limits: 3000 RPM (OpenAI)

### Vector Search

- HNSW index: O(log n) search time
- 10,000 recipes: <10ms
- 100,000 recipes: <50ms
- Recall@10: ~95% with HNSW

### Optimization Tips

1. **Batch Operations**: Always use batch embedding generation
2. **Index Strategy**: Use HNSW for >1000 vectors
3. **Caching**: Cache frequent query embeddings
4. **Prefiltering**: Apply SQL filters before vector search

## Configuration

Environment variables in `.env`:

```env
# Embedding Model
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072

# Search Settings
VECTOR_SEARCH_LIMIT=10
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Testing

```python
# Test embedding generation
embedding = await embedding_service.generate_embedding("test")
assert len(embedding) == 3072

# Test vector search
results = await vector_search.search_by_text("pho", session)
assert len(results) > 0
assert all(0 <= score <= 1 for _, score in results)
```

## Monitoring

Key metrics to monitor:

- **Embedding latency**: Time to generate embeddings
- **Search latency**: Time for vector search
- **Index size**: Memory usage of vector index
- **Hit rate**: Percentage of searches with results
- **Relevance**: User feedback on search quality

## Future Improvements

1. **Multi-modal Search**: Add image embeddings
2. **Query Expansion**: Expand queries with synonyms
3. **Re-ranking**: Use cross-encoder for better ranking
4. **Feedback Loop**: Learn from user interactions
5. **Caching**: Redis cache for common queries
6. **A/B Testing**: Compare different embedding models

## Troubleshooting

### Slow Searches

- Check HNSW index exists
- Verify embedding dimension matches
- Consider prefiltering before vector search

### Poor Results

- Check embedding quality (test similarity)
- Verify recipe descriptions are detailed
- Tune similarity threshold

### Missing Embeddings

- Run reindex script
- Check OpenAI API key
- Verify database connection

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [HNSW Algorithm Paper](https://arxiv.org/abs/1603.09320)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)
