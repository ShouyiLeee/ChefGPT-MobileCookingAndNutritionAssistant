"""Main FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.routers import auth, recipes, chat, vision, meal_plan, social, shopping


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting ChefGPT API...")
    create_db_and_tables()
    print("Database tables ready")
    yield
    print("Shutting down ChefGPT API...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered cooking and nutrition assistant — Gemini 2.5 Flash",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI routes (real — Gemini 2.5 Flash)
app.include_router(recipes.router)       # POST /recipes/suggest
app.include_router(vision.router)        # POST /ingredients/recognize
app.include_router(meal_plan.router)     # POST /mealplan/generate
app.include_router(chat.router)          # POST /chat/query
app.include_router(auth.router)

# Mock routes (demo data)
app.include_router(social.router)        # GET /posts/mock
app.include_router(shopping.router)      # GET /shopping-list/mock


@app.get("/")
async def root():
    return {"message": "Welcome to ChefGPT API", "version": settings.app_version}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version, "environment": settings.environment}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.reload)
