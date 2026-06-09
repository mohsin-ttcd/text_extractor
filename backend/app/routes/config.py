"""
Configuration and settings endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from ..models import ConfigUpdate
from ..config import get_settings, Settings

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
async def get_config(settings: Settings = Depends(get_settings)):
    """
    Get current application configuration.
    """
    return {
        "tesseract_path": settings.tesseract_path,
        "dpi": settings.dpi,
        "connected_docx_path": settings.connected_docx_path,
        "forget_on_close": settings.forget_on_close,
    }


@router.put("")
async def update_config(
    request: ConfigUpdate, settings: Settings = Depends(get_settings)
):
    """
    Update application configuration.

    All fields are optional; only provided fields will be updated.
    """
    try:
        if request.tesseract_path is not None:
            settings.tesseract_path = request.tesseract_path

        if request.dpi is not None:
            settings.dpi = request.dpi

        if request.connected_docx_path is not None:
            settings.connected_docx_path = request.connected_docx_path

        if request.forget_on_close is not None:
            settings.forget_on_close = request.forget_on_close

        # Save to file
        settings.save_config()

        return {
            "success": True,
            "message": "✅ কনফিগারেশন আপডেট করা হয়েছে",
            "config": {
                "tesseract_path": settings.tesseract_path,
                "dpi": settings.dpi,
                "connected_docx_path": settings.connected_docx_path,
                "forget_on_close": settings.forget_on_close,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating config: {str(e)}")
