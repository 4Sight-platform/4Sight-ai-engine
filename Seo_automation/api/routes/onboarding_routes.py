"""
API Onboarding Routes
POST /onboarding/* endpoints
"""

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

class BusinessInfo(BaseModel):
    business_name: str
    website_url: str
    business_description: str

@router.post("/business-info")
async def save_business_info(data: BusinessInfo):
    """Save Page 1: Business Info"""
    # TODO: Implement
    return {"status": "success"}

@router.post("/gsc-connect")
async def connect_gsc():
    """Initiate GSC OAuth flow"""
    # TODO: Implement
    return {"auth_url": "https://..."}

@router.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    """Upload brand logo"""
    # TODO: Implement
    return {"logo_url": "/uploads/logo.png"}

# TODO: Add remaining onboarding endpoints
