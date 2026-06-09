"""
Pydantic models for API request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class PageStatus(str, Enum):
    PENDING = "pending"
    OCR_DONE = "ocr_done"
    ERROR = "error"
    PROCESSING = "processing"


class PageData(BaseModel):
    """Page data response schema"""

    page_num: int
    raw_text: str
    edited_text: str
    status: str
    error_message: str = ""


class BookInfo(BaseModel):
    """Book metadata response schema"""

    id: int
    title: str
    total_pages: int
    processed_pages: int
    pdf_path: str


class BookProgress(BaseModel):
    """Book processing progress"""

    book_id: int
    current_page: int
    total_pages: int
    processed_pages: int
    status: str = "processing"


class OCRRequest(BaseModel):
    """Request to process a page"""

    book_id: int
    page_num: int
    engine: str = "tesseract"


class TextEditRequest(BaseModel):
    """Request to update edited text"""

    book_id: int
    page_num: int
    edited_text: str


class PageResetRequest(BaseModel):
    """Request to reset edited text for a page"""

    book_id: int
    page_num: int


class BatchOCRRequest(BaseModel):
    """Request to batch process pages"""

    book_id: int
    page_start: int = 1
    page_end: Optional[int] = None
    engine: str = "tesseract"


class ConfigUpdate(BaseModel):
    """Configuration update request"""

    tesseract_path: Optional[str] = None
    dpi: Optional[int] = None
    connected_docx_path: Optional[str] = None
    forget_on_close: Optional[bool] = None


class SelectionOCRRequest(BaseModel):
    """Request to OCR a selected region"""

    book_id: int
    page_num: int
    x1: float
    y1: float
    x2: float
    y2: float


class AppendRequest(BaseModel):
    """Request to append text to a connected Word document"""

    book_id: int
    text: str
    page_num: Optional[int] = None


class ExportRequest(BaseModel):
    """Word export request"""

    book_id: int
    output_path: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema"""

    detail: str
    error_code: str
    status_code: int
