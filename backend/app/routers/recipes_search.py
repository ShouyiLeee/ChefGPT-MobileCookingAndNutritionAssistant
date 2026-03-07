"""Community recipes — keyword browse + RAG semantic search."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.security import get_current_user_id
from app.services.rag import rag_service

router = APIRouter(prefix="/community-recipes", tags=["Community Recipes"])


# ── Response schemas ──────────────────────────────────────────────────────────

class NutritionOut(BaseModel):
    calories: int
    protein: int
    carbs: int
    fat: int


class CommunityRecipeCard(BaseModel):
    """Lightweight card for list views."""
    id: int
    title: str
    description: str
    cuisine: str
    category: str
    difficulty: str
    prep_time: int
    cook_time: int
    servings: int
    tags: list[str]
    ingredients: list[str]
    nutrition: NutritionOut


class CommunityRecipeOut(CommunityRecipeCard):
    """Full detail including steps."""
    steps: list[str]


class SearchResult(BaseModel):
    recipe: CommunityRecipeCard
    score: float
    match_type: str  # "semantic" | "keyword"


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResult]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[CommunityRecipeCard])
async def list_community_recipes(
    q: Optional[str] = Query(None, description="Keyword search"),
    cuisine: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None, enum=["easy", "medium", "hard"]),
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    _user_id: str = Depends(get_current_user_id),
):
    """Browse community recipes with keyword search and filters (no embedding)."""
    results = rag_service.keyword_search(
        query=q or "",
        cuisine=cuisine,
        difficulty=difficulty,
        category=category,
        limit=limit,
        offset=offset,
    )
    return [_to_card(r) for r in results]


@router.get("/search", response_model=SearchResponse)
async def semantic_search(
    q: str = Query(..., min_length=2, description="Natural language query"),
    k: int = Query(8, ge=1, le=20),
    _user_id: str = Depends(get_current_user_id),
):
    """
    RAG semantic search using Gemini text-embedding-004 + cosine similarity.
    Falls back to keyword search if RAG index is not ready.
    """
    if rag_service.ready:
        raw = await rag_service.search(q, k=k)
        match_type = "semantic"
    else:
        raw = rag_service.keyword_search(query=q, limit=k)
        match_type = "keyword"

    results = [
        SearchResult(
            recipe=_to_card(r),
            score=r.get("score", 1.0),
            match_type=match_type,
        )
        for r in raw
    ]
    return SearchResponse(query=q, total=len(results), results=results)


@router.get("/stats")
async def rag_stats(_user_id: str = Depends(get_current_user_id)):
    """RAG index status."""
    return {
        "ready": rag_service.ready,
        "recipe_count": rag_service.recipe_count,
        "embed_model": "text-embedding-004",
    }


@router.get("/{recipe_id}", response_model=CommunityRecipeOut)
async def get_community_recipe(
    recipe_id: int,
    _user_id: str = Depends(get_current_user_id),
):
    """Full detail of a single community recipe."""
    for r in rag_service._recipes:
        if r["id"] == recipe_id:
            return CommunityRecipeOut(**r)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_card(r: dict) -> CommunityRecipeCard:
    return CommunityRecipeCard(
        id=r["id"],
        title=r["title"],
        description=r["description"],
        cuisine=r["cuisine"],
        category=r["category"],
        difficulty=r["difficulty"],
        prep_time=r["prep_time"],
        cook_time=r["cook_time"],
        servings=r["servings"],
        tags=r.get("tags", []),
        ingredients=r.get("ingredients", []),
        nutrition=NutritionOut(**r["nutrition"]),
    )
