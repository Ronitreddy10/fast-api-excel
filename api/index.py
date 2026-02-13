"""
FastAPI Application Entry Point
Student Response Report Generator

This application generates Excel reports from a SQL Server database.
IMPORTANT: All database operations are READ-ONLY.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os

from routes.reports import router as reports_router
from database import test_connection


# Create FastAPI application
app = FastAPI(
    title="Student Response Report Generator",
    description="""
    API for generating Excel reports of student test responses.
    
    ## Features
    - Generates Excel reports with student test response data
    - Supports filtering by contest, grade, school, and date range
    - Pivots data so each student is one row with question columns
    
    ## Safety
    - All database operations are READ-ONLY
    - Queries are parameterized to prevent SQL injection
    - Result limits prevent excessive data retrieval
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET"],  # Only allow GET since we're read-only
    allow_headers=["*"],
)

# Include routers
app.include_router(reports_router)

# Get the directory where the project root is
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")


@app.get("/", tags=["Root"])
async def root():
    """Serve the frontend HTML page."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Tests database connectivity.
    """
    db_connected = False
    try:
        db_connected = test_connection()
    except Exception:
        pass
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "database_connected": db_connected,
        "timestamp": datetime.now().isoformat()
    }


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
