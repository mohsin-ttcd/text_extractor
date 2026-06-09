"""
Books management endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import os
import shutil
from pathlib import Path
from typing import List
from ..models import BookInfo, BookProgress
from ..database import DatabaseManager
from ..ocr_processor import BengaliOcrProcessor
from ..config import get_settings

router = APIRouter(prefix="/api/books", tags=["books"])


def get_db() -> DatabaseManager:
    """Dependency: get database manager"""
    settings = get_settings()
    return DatabaseManager(settings.db_path)


def get_processor(
    settings=Depends(get_settings), db=Depends(get_db)
) -> BengaliOcrProcessor:
    """Dependency: get OCR processor"""
    return BengaliOcrProcessor(
        db_manager=db, tesseract_path=settings.tesseract_path, dpi=settings.dpi
    )


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    db: DatabaseManager = Depends(get_db),
    processor: BengaliOcrProcessor = Depends(get_processor),
):
    """
    Upload a PDF file and register it in the database.

    Returns:
    - book_id: ID of the registered book
    - title: Book title (derived from filename)
    - total_pages: Total number of pages in the PDF
    - message: Success message in Bengali
    """
    try:
        # Save uploaded file to a permanent uploads/ folder inside backend/
        # Resolve uploads dir relative to this file (always correct regardless of cwd)
        _backend_dir = Path(__file__).resolve().parent.parent.parent  # backend/
        uploads_dir = _backend_dir / "uploads"
        uploads_dir.mkdir(exist_ok=True)

        # Use original filename (sanitised)
        safe_name = file.filename.replace("/", "_").replace("\\", "_")
        pdf_path = str(uploads_dir / safe_name)

        # Write the uploaded bytes directly — no cross-drive rename needed
        content = await file.read()
        with open(pdf_path, "wb") as f:
            f.write(content)

        # Count pages
        total_pages = processor.get_pdf_page_count(pdf_path)

        # Register in database
        book_id = db.register_book(pdf_path, total_pages)

        return {
            "success": True,
            "book_id": book_id,
            "title": safe_name.replace(".pdf", "").replace(".PDF", ""),
            "total_pages": total_pages,
            "message": f"✅ পিডিএফ সফলভাবে আপলোড করা হয়েছে: {safe_name}",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error uploading PDF: {str(e)}")



@router.get("/")
async def list_books(db: DatabaseManager = Depends(get_db)):
    """
    List all registered books in the database.

    Returns:
    - List of BookInfo objects with metadata
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, total_pages, processed_pages, pdf_path 
                FROM books 
                ORDER BY created_at DESC
            """)
            books = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "total_pages": row["total_pages"],
                    "processed_pages": row["processed_pages"],
                    "pdf_path": row["pdf_path"],
                }
                for row in cursor.fetchall()
            ]
        return {"books": books}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching books: {str(e)}")


@router.get("/{book_id}")
async def get_book(book_id: int, db: DatabaseManager = Depends(get_db)):
    """
    Get detailed information about a specific book.

    Returns:
    - Book metadata and processing progress
    """
    try:
        processed, total = db.get_book_progress(book_id)

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, total_pages, processed_pages, pdf_path 
                FROM books 
                WHERE id = ?
            """,
                (book_id,),
            )
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        return {
            "id": row["id"],
            "title": row["title"],
            "total_pages": row["total_pages"],
            "processed_pages": processed,
            "pdf_path": row["pdf_path"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching book: {str(e)}")


@router.get("/{book_id}/progress")
async def get_book_progress(book_id: int, db: DatabaseManager = Depends(get_db)):
    """
    Get processing progress for a book.

    Returns:
    - Current page count, total pages, status
    """
    try:
        processed, total = db.get_book_progress(book_id)

        return {
            "book_id": book_id,
            "processed_pages": processed,
            "total_pages": total,
            "percentage": (processed / total * 100) if total > 0 else 0,
            "status": "completed" if processed == total else "in_progress",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching progress: {str(e)}"
        )


@router.delete("/{book_id}")
async def delete_book(book_id: int, db: DatabaseManager = Depends(get_db)):
    """
    Delete a book and all its associated pages from the database.

    This operation is irreversible.
    """
    try:
        # First verify the book exists
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pdf_path FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        # Delete from database
        db.delete_book(book_id)

        # Optional: Delete the PDF file
        try:
            if row["pdf_path"] and os.path.exists(row["pdf_path"]):
                os.remove(row["pdf_path"])
        except:
            pass

        return {"success": True, "message": "Book deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting book: {str(e)}")
