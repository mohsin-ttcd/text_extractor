"""
Bengali OCR FastAPI Application
Main entry point for the API server
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import books, pages, config, export

# Create FastAPI app
app = FastAPI(
    title="Bengali OCR API",
    description="API for extracting and editing Bengali text from scanned PDFs",
    version="1.0.0",
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "tauri://localhost",
        "http://tauri.localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(books.router)
app.include_router(pages.router)
app.include_router(config.router)
app.include_router(export.router)


@app.get("/")
async def root():
    """Health check and welcome endpoint"""
    return {
        "message": "স্বাগতম Bengali OCR API তে",
        "status": "healthy",
        "api_version": "1.0.0",
        "documentation": "/docs",
    }


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
