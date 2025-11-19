"""
Main FastAPI Application - PRODUCTION READY
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.connection import engine
from src.database.models import Base
from src.api import routes, auth_routes

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Research Paper Curator API",
    description="RAG-powered research paper discovery with authentication and analytics",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Research Paper Curator API v2.0",
        "status": "running",
        "docs": "/docs",
        "api": "/api"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0"
    }

# Include routers with /api prefix
app.include_router(auth_routes.router)
app.include_router(routes.router, prefix="/api")
