"""
FastAPI Application
REST API endpoints for SEO automation
"""

import os

os.environ["PYTHONIOENCODING"] = "utf-8"

from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from platform_services import api_router
from config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="4Sight AI Engine",
    version="2.0.0",
    openapi_tags=[
        {"name": "4Sight AI Engine", "description": "Endpoints for frontend integration"}
    ],
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS - Add middleware BEFORE including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include incremental onboarding router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def index() -> Any:
    """Basic HTML response."""
    body = (
        "<html>"
        "<body style='padding: 10px;'>"
        "<h1>4Sight Platform APIs</h1>"
        "<div>"
        "Check the API spec: <a href='/docs'>here</a>"
        "</div>"
        "</body>"
        "</html>"
    )
    return HTMLResponse(content=body)


@app.get("/health", include_in_schema=False)
def health_check() -> dict:
    return {"status": "ok"}


# Uvicorn startup
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=300,
        log_level="info",
    )
