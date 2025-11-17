# ChefGPT Backend API

FastAPI-based backend for ChefGPT - AI-powered cooking and nutrition assistant.

## Features

- **Authentication**: JWT-based auth with Supabase integration
- **Recipe Management**: CRUD operations with RAG-powered search
- **AI Chatbot**: Intelligent cooking assistant using GPT-4.1/Claude
- **Vision API**: Ingredient recognition from images
- **Meal Planning**: AI-generated personalized meal plans
- **Social Features**: Community posts, comments, likes
- **Vector Search**: PostgreSQL + pgvector for semantic recipe search

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15+ with pgvector extension
- **ORM**: SQLModel (SQLAlchemy 2.0)
- **Authentication**: JWT (python-jose)
- **LLM**: OpenAI GPT-4.1, Anthropic Claude 3.5 Sonnet
- **Vector DB**: pgvector for embeddings
- **Cache**: Redis (optional)
- **Task Queue**: Celery (optional)

## Project Structure

```
backend/
├── app/
│   ├── core/              # Core configuration
│   │   ├── config.py      # Settings management
│   │   ├── database.py    # Database connection
│   │   └── security.py    # Auth & JWT
│   ├── models/            # SQLModel database models
│   │   ├── user.py
│   │   ├── recipe.py
│   │   ├── social.py
│   │   ├── meal_plan.py
│   │   ├── shopping.py
│   │   └── chat.py
│   ├── schemas/           # Pydantic request/response schemas
│   ├── routers/           # API endpoints
│   │   ├── auth.py
│   │   ├── recipes.py
│   │   ├── chat.py
│   │   ├── vision.py
│   │   ├── meal_plan.py
│   │   └── social.py
│   ├── services/          # Business logic
│   ├── llm/               # LLM integration
│   │   ├── client.py      # LLM client
│   │   ├── agents/        # AI agents
│   │   └── tools/         # Agent tools
│   ├── rag/               # RAG pipeline
│   │   ├── vectorstore.py # Vector database
│   │   └── embeddings.py  # Embedding generation
│   └── main.py            # FastAPI app
├── alembic/               # Database migrations
├── scripts/               # Utility scripts
├── tests/                 # Tests
├── requirements.txt       # Dependencies
├── pyproject.toml         # Project config
├── Dockerfile             # Docker config
└── docker-compose.yml     # Docker Compose config
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Redis (optional, for caching)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/chefgpt.git
cd chefgpt/backend
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**:
```bash
# Make sure PostgreSQL is running with pgvector extension
alembic upgrade head
```

6. **Run the application**:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Docker Setup

### Using Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, Redis, Backend)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t chefgpt-backend .

# Run container
docker run -p 8000:8000 --env-file .env chefgpt-backend
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user

### Recipes
- `GET /recipes` - List recipes with filters
- `GET /recipes/{id}` - Get recipe details
- `POST /recipes` - Create recipe
- `PUT /recipes/{id}` - Update recipe
- `DELETE /recipes/{id}` - Delete recipe

### Chat
- `POST /chat/query` - Send message to AI
- `GET /chat/history` - Get chat history

### Vision
- `POST /ingredients/recognize` - Recognize ingredients from image

### Meal Planning
- `POST /mealplan/generate` - Generate meal plan
- `GET /mealplan` - Get user's meal plans

### Social
- `GET /posts` - Get public posts
- `POST /posts` - Create post
- `POST /posts/{id}/like` - Like/unlike post
- `GET /posts/{id}/comments` - Get comments
- `POST /posts/{id}/comments` - Add comment

## Environment Variables

Key environment variables (see `.env.example` for all):

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chefgpt

# JWT
JWT_SECRET_KEY=your-secret-key

# OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4-turbo-preview

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
```

## Development

### Code Formatting

```bash
# Format with black
black app/

# Lint with ruff
ruff check app/

# Type checking with mypy
mypy app/
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## LLM Integration

The backend supports multiple LLM providers:

- **OpenAI GPT-4.1**: Primary model for chat and reasoning
- **Anthropic Claude**: Alternative model
- **OpenAI Embeddings**: For RAG vector search

### Adding Custom Tools

Create tools in `app/llm/tools/`:

```python
async def my_tool(param: str) -> dict:
    """Custom tool for agent."""
    # Implementation
    return {"result": "..."}
```

## RAG Pipeline

The RAG system uses:

1. **Embeddings**: OpenAI text-embedding-3-large (3072 dimensions)
2. **Vector DB**: PostgreSQL + pgvector
3. **Search**: Cosine similarity for recipe matching

### Indexing Recipes

```python
from app.rag.vectorstore import vector_store

# Automatically index when creating/updating recipes
await vector_store.add_recipe(recipe, session)
```

## Production Deployment

### Using Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

1. Set `ENVIRONMENT=production` in `.env`
2. Use production database
3. Set `DEBUG=False`
4. Configure CORS origins
5. Use HTTPS
6. Set up monitoring (e.g., Sentry)

### Recommended Services

- **Hosting**: Fly.io, Railway, AWS ECS
- **Database**: Supabase, AWS RDS
- **Cache**: Redis Cloud, AWS ElastiCache
- **Storage**: Supabase Storage, AWS S3

## Monitoring & Logging

- Logs are output in JSON format for production
- Health check endpoint: `GET /health`
- Metrics: Consider adding Prometheus/Grafana

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

Proprietary - For internal development and research.

## Support

For issues and questions, please contact the development team.
