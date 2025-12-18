"""
FastAPI Application
REST API endpoints for SEO automation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import onboarding_routes, keyword_routes, profile_routes

app = FastAPI(
    title="SEO Automation API",
    description="Complete SEO automation platform with onboarding",
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

# Include routers
app.include_router(onboarding_routes.router)
app.include_router(keyword_routes.router)
app.include_router(profile_routes.router)

@app.get("/")
def root():
    return {
        "message": "SEO Automation API",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
