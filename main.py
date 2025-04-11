#!/usr/bin/env python3
"""
Main application entry point for Local SFTP Client
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.routes import auth, files, system
from app.utils.logger import setup_logger

# Initialize application
app = FastAPI(
    title="Local SFTP Client",
    description="A web-based SFTP client for managing remote files",
    version="1.0.0"
)

# Get application settings
settings = get_settings()

# Setup logging
logger = setup_logger()

# Initialize required directories
for directory in [settings.tmp_path, settings.upload_tmp_path, settings.share_path]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(system.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/share", StaticFiles(directory=settings.share_path), name="share")

# Root endpoint redirects to static HTML
@app.get("/")
async def root():
    """
    Redirect root path to static index.html
    """
    return RedirectResponse("/static/index.html")

# Run the application
if __name__ == "__main__":
    logger.info(f"Starting Local SFTP Client on port {settings.port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        access_log=False
    )