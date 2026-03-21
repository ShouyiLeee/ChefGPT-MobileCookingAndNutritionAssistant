"""Main FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.logging_config import setup_logging
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers import auth, recipes, chat, vision, meal_plan, social, shopping, recipes_search, personas, memory, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(log_level=settings.log_level, log_file=settings.log_file)
    logger.info("Starting ChefGPT API | provider={} mcp_enabled={}", settings.llm_provider, settings.mcp_enabled)
    create_db_and_tables()
    logger.info("Database tables ready")
    # Initialize RAG index (loads community recipes + embeddings)
    from app.services.rag import rag_service
    await rag_service.initialize()
    logger.info("RAG index ready | recipes={} ready={}", rag_service.recipe_count, rag_service.ready)
    # Load persona templates from JSON files
    from app.services.persona_service import persona_service
    persona_service.load_all()
    logger.info("Persona templates loaded | count={}", len(persona_service.list_all()))

    # ── MCP Agentic Layer (only if MCP_ENABLED=true) ────────────────────────────
    if settings.mcp_enabled:
        from app.services.llm import llm_provider
        from app.services.cache import cache_service
        from app.services.memory_service import memory_service
        from app.services.shopping_agent import shopping_agent_service
        from app.services.tool_registry import tool_registry
        from app.mcp_servers.recipe_server import RecipeMCPServer
        from app.mcp_servers.nutrition_server import NutritionMCPServer
        from app.mcp_servers.shopping_server import ShoppingMCPServer
        from app.mcp_servers.memory_server import MemoryMCPServer
        from app.mcp_servers.vision_server import VisionMCPServer
        from app.agents.coordinator_agent import CoordinatorAgent
        from app.agents.agent_registry import AgentRegistry
        from app.services.agent_loop import AgenticLoop

        # Initialize and register all MCP servers
        recipe_server = RecipeMCPServer(rag_service, llm_provider, cache_service)
        nutrition_server = NutritionMCPServer(llm_provider)
        shopping_server = ShoppingMCPServer(shopping_agent_service, llm_provider)
        memory_server = MemoryMCPServer(memory_service, cache_service)
        vision_server = VisionMCPServer(llm_provider)

        for srv in [recipe_server, nutrition_server, shopping_server, memory_server, vision_server]:
            srv.register_tools(tool_registry)

        logger.info("MCP tools registered | tools={}", tool_registry.list_tools())

        # Initialize coordinator + agent registry + agentic loop
        coordinator = CoordinatorAgent(llm_provider)
        agent_registry = AgentRegistry(tool_registry, llm_provider)
        agent_loop = AgenticLoop(coordinator, agent_registry)

        # Store singletons on app.state for router access
        app.state.tool_registry = tool_registry
        app.state.agent_loop = agent_loop
        logger.info(
            "Agentic loop ready | agents={} tools={}",
            agent_registry.list_agents(), tool_registry.list_tools(),
        )

    yield
    logger.info("Shutting down ChefGPT API")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered cooking and nutrition assistant",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# LoggingMiddleware must be added before CORSMiddleware so it wraps everything
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # Allow any localhost port for local dev (Flutter web picks random ports)
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI routes
app.include_router(recipes.router)       # POST /recipes/suggest
app.include_router(vision.router)        # POST /ingredients/recognize
app.include_router(meal_plan.router)     # POST /mealplan/generate
app.include_router(chat.router)          # POST /chat/query
app.include_router(personas.router)      # GET/PUT /personas
app.include_router(memory.router)        # GET/POST/DELETE /memory
app.include_router(orders.router)        # POST/GET /orders, /payment-mandate
app.include_router(auth.router)

# Community recipes + RAG search
app.include_router(recipes_search.router)  # GET /community-recipes

# Mock routes (demo data)
app.include_router(social.router)          # CRUD /posts
app.include_router(shopping.router)        # GET /shopping-list/mock


@app.get("/")
async def root():
    return {"message": "Welcome to ChefGPT API", "version": settings.app_version}


@app.get("/health")
async def health_check():
    from app.services.cache import cache_service
    redis_ok = await cache_service.ping()
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "llm_provider": settings.llm_provider,
        "redis": "connected" if redis_ok else "unavailable",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.reload)
