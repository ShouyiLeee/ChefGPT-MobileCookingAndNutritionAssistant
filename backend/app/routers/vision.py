"""Vision router — ingredient recognition via Gemini Vision."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from app.core.config import settings
from app.core.security import get_current_user_id
from app.services.gemini import gemini_service

router = APIRouter(prefix="/ingredients", tags=["Vision"])

_ALLOWED = {f"image/{ext}" for ext in ["jpeg", "jpg", "png", "webp"]}


def _validate_image(image: UploadFile) -> None:
    if not image.content_type or image.content_type not in _ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (jpeg/png/webp)",
        )


@router.post("/recognize")
async def recognize_ingredients(
    image: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """Recognize food ingredients from an uploaded photo using Gemini Vision."""
    _validate_image(image)
    image_bytes = await image.read()
    if len(image_bytes) > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image too large (max 10MB)",
        )
    try:
        return await gemini_service.recognize_ingredients(image_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )


