"""
Pages management and OCR processing endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse, Response
import os
import base64
import json
import threading
import time
import asyncio
from io import BytesIO
from PIL import Image
import fitz
from typing import Optional
from ..models import (
    TextEditRequest,
    PageResetRequest,
    OCRRequest,
    BatchOCRRequest,
    SelectionOCRRequest,
)
from ..database import DatabaseManager
from ..ocr_processor import BengaliOcrProcessor
from ..config import get_settings

router = APIRouter(prefix="/api/pages", tags=["pages"])

# Store active processing tasks
processing_tasks = {}


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


@router.get("/{book_id}/{page_num}/image")
async def get_page_image(
    book_id: int,
    page_num: int,
):
    """Get raw page image as PNG bytes."""
    try:
        settings = get_settings()
        db = DatabaseManager(settings.db_path)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pdf_path FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        doc = fitz.open(row["pdf_path"])
        page = doc[page_num - 1]
        zoom = 150 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        buffer = BytesIO()
        pil_img.save(buffer, format="PNG")
        doc.close()
        return Response(content=buffer.getvalue(), media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching image: {str(e)}")


@router.get("/{book_id}/{page_num}")
async def get_page(
    book_id: int,
    page_num: int,
    db: DatabaseManager = Depends(get_db),
    processor: BengaliOcrProcessor = Depends(get_processor),
):
    """
    Get page data including:
    - page_image: Base64 encoded PNG of the page
    - raw_text: Original OCR output
    - edited_text: User-edited text
    - status: Current processing status
    """
    try:
        # Get page text data
        page_data = db.get_page(book_id, page_num)
        if not page_data:
            raise HTTPException(status_code=404, detail="Page not found")

        # Get PDF path
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pdf_path FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        pdf_path = row["pdf_path"]

        # Render page to image and convert to base64
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]

        # Render at 150 DPI for faster response
        zoom = 150 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)

        # Convert to PIL Image and then to base64
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        buffer = BytesIO()
        pil_img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        doc.close()

        return {
            "page_num": page_num,
            "book_id": book_id,
            "page_image": f"data:image/png;base64,{img_base64}",
            "raw_text": page_data["raw_text"],
            "edited_text": page_data["edited_text"],
            "status": page_data["status"],
            "error_message": page_data["error_message"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching page: {str(e)}")


@router.post("/{page_id}/ocr")
async def ocr_single_page(
    page_id: int,
    request: OCRRequest,
    db: DatabaseManager = Depends(get_db),
    processor: BengaliOcrProcessor = Depends(get_processor),
):
    """
    Process a single page with OCR.

    Returns:
    - raw_text: Extracted Bengali text
    - status: 'ocr_done' or 'error'
    - message: Status message in Bengali
    """
    try:
        # Get PDF path
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pdf_path FROM books WHERE id = ?", (request.book_id,)
            )
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        pdf_path = row["pdf_path"]

        # Process the page (this will save to database)
        raw_text, engine_used, error_msg = processor.process_page(
            pdf_path, request.page_num, request.book_id
        )

        return {
            "success": True,
            "page_num": request.page_num,
            "raw_text": raw_text,
            "engine_used": engine_used,
            "status": "ocr_done",
            "message": f"✅ পৃষ্ঠা {request.page_num} সফলভাবে প্রক্রিয়া করা হয়েছে",
        }
    except Exception as e:
        error_str = str(e)
        db.save_page_ocr(
            request.book_id,
            request.page_num,
            "",
            status="error",
            error_message=error_str,
        )
        raise HTTPException(status_code=500, detail=f"OCR error: {error_str}")


@router.post("/batch-ocr")
async def batch_ocr(
    request: BatchOCRRequest,
    background_tasks: BackgroundTasks,
    db: DatabaseManager = Depends(get_db),
    processor: BengaliOcrProcessor = Depends(get_processor),
):
    """
    Start batch OCR processing for multiple pages in the background.

    Returns:
    - task_id: ID to track progress
    - message: Confirmation message
    """
    try:
        # Get PDF path
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pdf_path, total_pages FROM books WHERE id = ?",
                (request.book_id,),
            )
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        pdf_path = row["pdf_path"]
        total_pages = row["total_pages"]

        # Determine page range
        page_start = max(1, request.page_start or 1)
        page_end = min(request.page_end or total_pages, total_pages)
        if page_start > page_end:
            raise HTTPException(status_code=400, detail="Invalid page range")

        # Start background processing
        task_id = f"batch_{request.book_id}_{int(time.time())}"
        stop_event = threading.Event()
        processing_tasks[task_id] = {
            "stop_event": stop_event,
            "status": "running",
            "events": [],
        }

        def batch_process_worker():
            """Background worker for batch processing"""
            try:

                def progress_callback(page, status, preview, msg):
                    event = {
                        "page_num": page,
                        "status": status,
                        "preview": preview,
                        "processed": page - page_start + 1,
                        "total": page_end - page_start + 1,
                    }
                    processing_tasks[task_id].setdefault("events", []).append(event)

                processor.process_book_background(
                    pdf_path,
                    request.book_id,
                    page_start,
                    page_end,
                    progress_callback=progress_callback,
                    stop_event=stop_event,
                )
                processing_tasks[task_id]["status"] = (
                    "stopped" if stop_event.is_set() else "completed"
                )
            except Exception as e:
                processing_tasks[task_id]["error"] = str(e)
                processing_tasks[task_id]["status"] = "failed"

        background_tasks.add_task(batch_process_worker)

        return {
            "success": True,
            "task_id": task_id,
            "book_id": request.book_id,
            "page_start": page_start,
            "page_end": page_end,
            "message": f"✅ ব্যাচ প্রক্রিয়াকরণ শুরু হয়েছে: পৃষ্ঠা {page_start}-{page_end}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting batch OCR: {str(e)}"
        )


@router.get("/task/{task_id}/status")
async def get_task_status(task_id: str):
    """
    Get the status of a batch processing task.

    Returns:
    - status: 'running', 'completed', or 'failed'
    - error: Error message if failed
    """
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = processing_tasks[task_id]
    latest_event = task.get("events", [])[-1] if task.get("events") else {}
    return {
        "task_id": task_id,
        "status": task["status"],
        "error": task.get("error", None),
        "processed": latest_event.get("processed", 0),
        "total": latest_event.get("total", 0),
        "current_page": latest_event.get("page_num"),
    }


@router.get("/task/{task_id}/stream")
async def stream_task_progress(task_id: str):
    """SSE endpoint that streams batch OCR progress events."""

    async def event_generator():
        last_count = 0
        while True:
            if task_id not in processing_tasks:
                yield f"event: error\ndata: {json.dumps({'error': 'Task not found'})}\n\n"
                break

            task = processing_tasks[task_id]
            events = task.get("events", [])

            while last_count < len(events):
                event = events[last_count]
                yield f"data: {json.dumps(event)}\n\n"
                last_count += 1

            if task["status"] == "completed":
                yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"
                break
            elif task["status"] == "stopped":
                yield f"event: done\ndata: {json.dumps({'status': 'stopped'})}\n\n"
                break
            elif task["status"] == "failed":
                yield f"event: error\ndata: {json.dumps({'error': task.get('error', 'Unknown error')})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/batch-ocr/stop")
async def stop_batch_ocr(task_id: str = Query(...)):
    """Stop a running batch OCR task."""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = processing_tasks[task_id]
    if task["status"] != "running":
        raise HTTPException(status_code=400, detail="Task is not running")

    task["stop_event"].set()
    task["status"] = "stopped"
    return {"success": True, "message": "Batch OCR stopped"}


@router.post("/{page_id}/ocr-selection")
async def ocr_selection(
    page_id: int,
    request: SelectionOCRRequest,
    db: DatabaseManager = Depends(get_db),
    processor: BengaliOcrProcessor = Depends(get_processor),
):
    """
    OCR a selected region of a page.

    Accepts crop coordinates (x1,y1,x2,y2) relative to the page image,
    renders the page, crops the region, runs Tesseract, returns text.
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pdf_path FROM books WHERE id = ?", (request.book_id,)
            )
            row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        doc = fitz.open(row["pdf_path"])
        page = doc[request.page_num - 1]
        zoom = 150 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        # Crop the selected region
        x1, y1 = int(min(request.x1, request.x2)), int(min(request.y1, request.y2))
        x2, y2 = int(max(request.x1, request.x2)), int(max(request.y1, request.y2))
        cropped = pil_img.crop((x1, y1, x2, y2))

        # Run Tesseract on the cropped region
        processed = processor.preprocess_image(cropped)
        text = processor.extract_text_tesseract(processed)

        return {"success": True, "text": text, "page_num": request.page_num}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Selection OCR error: {str(e)}")


@router.post("/{page_id}/update-text")
async def update_page_text(
    page_id: int, request: TextEditRequest, db: DatabaseManager = Depends(get_db)
):
    """
    Update the edited text for a page.

    This is called when the user manually edits text in the editor.
    """
    try:
        db.save_page_edit(request.book_id, request.page_num, request.edited_text)

        return {
            "success": True,
            "page_num": request.page_num,
            "message": "✅ পাঠ্য সংরক্ষিত হয়েছে",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating text: {str(e)}")


@router.put("/{page_id}/reset")
async def reset_page_text(
    page_id: int, request: PageResetRequest, db: DatabaseManager = Depends(get_db)
):
    """
    Reset edited text back to raw OCR output.

    This allows users to discard manual edits and start over.
    """
    try:
        page_num = request.page_num or page_id
        page_data = db.get_page(request.book_id, page_num)
        if not page_data:
            raise HTTPException(status_code=404, detail="Page not found")

        # Revert edited_text to raw_text
        db.save_page_edit(request.book_id, page_num, page_data["raw_text"])

        return {
            "success": True,
            "page_num": page_num,
            "text": page_data["raw_text"],
            "message": "✅ মূল লেখায় ফিরে গেছেন",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting text: {str(e)}")
