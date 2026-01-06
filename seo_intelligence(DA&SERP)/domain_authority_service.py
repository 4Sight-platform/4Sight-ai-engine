"""
Domain Authority Service
Fetches and caches Domain Authority scores using Moz Link Explorer API
"""

import os
import logging
import httpx
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime
from Database.models import Base

logger = logging.getLogger(__name__)


class DomainAuthorityCache(Base):
    """Cache table for Domain Authority scores (monthly refresh)"""
    __tablename__ = "domain_authority_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    domain_authority = Column(Integer, nullable=False)
    provider = Column(String(50), default="moz", nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class DomainAuthorityService:
    """
    Service for fetching Domain Authority scores from Moz API.
    
    Features:
    - Moz Link Explorer API integration
    - Monthly caching to reduce API calls
    - Graceful error handling
    """
    
    API_BASE = "https://lsapi.seomoz.com/v2/url_metrics"
    CACHE_DURATION_DAYS = 30  # Monthly refresh
    
    def __init__(self):
        self.access_id = os.getenv("MOZ_ACCESS_ID")
        self.secret_key = os.getenv("MOZ_SECRET_KEY")
        
        if not self.access_id or not self.secret_key:
            logger.warning("[Domain Authority] Moz credentials not configured")
    
    def _get_auth_header(self) -> str:
        """Generate Basic Auth header for Moz API."""
        credentials = f"{self.access_id}:{self.secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def _is_cache_valid(self, cached_entry: Optional[DomainAuthorityCache]) -> bool:
        """
        Check if cached DA score is still valid.
        
        Args:
            cached_entry: Cached DA record
            
        Returns:
            True if cache is valid (not expired)
        """
        if not cached_entry:
            return False
        
        return datetime.utcnow() < cached_entry.expires_at
    
    async def fetch_from_moz(self, domain: str) -> Optional[int]:
        """
        Fetch Domain Authority score from Moz API.
        
        Args:
            domain: Domain to fetch DA for (e.g., "example.com")
            
        Returns:
            DA score (0-100) or None if error
        """
        if not self.access_id or not self.secret_key:
            logger.error("[Domain Authority] Missing Moz credentials")
            return None
        
        # Normalize domain
        domain_clean = domain.lower().replace("www.", "").replace("http://", "").replace("https://", "").strip("/")
        
        logger.info(f"[Domain Authority] Fetching DA for {domain_clean} from Moz API")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_BASE,
                    json={"targets": [domain_clean]},
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract DA from response
                results = data.get("results", [])
                if results and len(results) > 0:
                    da_score = results[0].get("domain_authority", 0)
                    logger.info(f"[Domain Authority] Moz API returned DA={da_score} for {domain_clean}")
                    return int(da_score)
                else:
                    logger.warning(f"[Domain Authority] No results from Moz for {domain_clean}")
                    return 0
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"[Domain Authority] Moz API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"[Domain Authority] Error fetching from Moz: {str(e)}", exc_info=True)
            return None
    
    async def get_domain_authority(
        self,
        domain: str,
        db: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get Domain Authority score with caching.
        
        Args:
            domain: Domain to get DA for
            db: Database session
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dict with DA score and metadata
        """
        # Normalize domain
        domain_clean = domain.lower().replace("www.", "").replace("http://", "").replace("https://", "").strip("/")
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            try:
                cached = db.query(DomainAuthorityCache).filter(
                    DomainAuthorityCache.domain == domain_clean
                ).first()
                
                if self._is_cache_valid(cached):
                    logger.info(f"[Domain Authority] Using cached DA={cached.domain_authority} for {domain_clean}")
                    return {
                        "domain_authority": cached.domain_authority,
                        "provider": cached.provider,
                        "last_updated": cached.fetched_at.date().isoformat(),
                        "cache_hit": True
                    }
                else:
                    if cached:
                        logger.info(f"[Domain Authority] Cache expired for {domain_clean}, fetching fresh data")
            except Exception as e:
                logger.warning(f"[Domain Authority] Cache lookup error: {e}")
        
        # Fetch from Moz API
        da_score = await self.fetch_from_moz(domain_clean)
        
        if da_score is None:
            # API error - return cached value if available, otherwise 0
            try:
                cached = db.query(DomainAuthorityCache).filter(
                    DomainAuthorityCache.domain == domain_clean
                ).first()
                
                if cached:
                    logger.warning(f"[Domain Authority] API error, using stale cache for {domain_clean}")
                    return {
                        "domain_authority": cached.domain_authority,
                        "provider": cached.provider,
                        "last_updated": cached.fetched_at.date().isoformat(),
                        "cache_hit": True,
                        "warning": "Using stale cache due to API error"
                    }
            except Exception as e:
                logger.error(f"[Domain Authority] Error accessing cache: {e}")
            
            return {
                "domain_authority": 0,
                "provider": "moz",
                "last_updated": datetime.utcnow().date().isoformat(),
                "error": "Failed to fetch from Moz API"
            }
        
        # Update cache
        try:
            cached = db.query(DomainAuthorityCache).filter(
                DomainAuthorityCache.domain == domain_clean
            ).first()
            
            now = datetime.utcnow()
            expires = now + timedelta(days=self.CACHE_DURATION_DAYS)
            
            if cached:
                # Update existing cache
                cached.domain_authority = da_score
                cached.fetched_at = now
                cached.expires_at = expires
                logger.info(f"[Domain Authority] Updated cache for {domain_clean}")
            else:
                # Create new cache entry
                new_cache = DomainAuthorityCache(
                    domain=domain_clean,
                    domain_authority=da_score,
                    provider="moz",
                    fetched_at=now,
                    expires_at=expires
                )
                db.add(new_cache)
                logger.info(f"[Domain Authority] Created cache for {domain_clean}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"[Domain Authority] Error updating cache: {e}", exc_info=True)
            db.rollback()
        
        return {
            "domain_authority": da_score,
            "provider": "moz",
            "last_updated": datetime.utcnow().date().isoformat(),
            "cache_hit": False
        }
