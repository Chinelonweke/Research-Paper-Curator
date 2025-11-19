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
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_routes.router)
app.include_router(routes.router)

@app.get("/")
async def root():
    return {
        "message": "Research Paper Curator API v2.0",
        "features": ["authentication", "tracking", "analytics", "monitoring"],
        "docs": "/docs"
    }
