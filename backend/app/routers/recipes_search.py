"""Recipe search router — stub for MVP (RAG not implemented yet)."""
from fastapi import APIRouter

router = APIRouter(prefix="/recipes/search", tags=["Recipe Search"])

# RAG-powered search is planned for Phase 2.
# For MVP, recipe discovery goes through POST /recipes/suggest (Gemini AI).
