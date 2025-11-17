"""Vision API router for ingredient recognition."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.core.security import get_current_user_id
from app.schemas.vision import IngredientRecognitionResponse

router = APIRouter(prefix="/ingredients", tags=["Vision"])


@router.post("/recognize", response_model=IngredientRecognitionResponse)
async def recognize_ingredients(
    image: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
) -> IngredientRecognitionResponse:
    """Recognize ingredients from an uploaded image."""
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # TODO: Implement vision model integration
    # For now, return placeholder
    return IngredientRecognitionResponse(
        ingredients=["tomato", "onion", "garlic", "chicken"],
        confidence=0.85,
        metadata={"model": "gpt-4-vision", "processing_time": 1.2},
    )
