"""
Keyword API Routes
"""

from fastapi import APIRouter

router = APIRouter(prefix="/keywords", tags=["keywords"])

@router.get("/suggestions")
async def get_keyword_suggestions(user_id: str):
    """Get LLM-generated keyword suggestions"""
    # TODO: Implement
    return {"keywords": []}

@router.post("/select")
async def select_keywords(user_id: str, keywords: list[str]):
    """Save user's selected keywords"""
    # TODO: Implement
    return {"status": "success"}
