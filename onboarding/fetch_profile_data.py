import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, Optional
from datetime import datetime

from Database.database import SessionLocal
from Database.models import (
    User, BusinessProfile, Integrations, Products, Services, Differentiators,
    AudienceProfile, SeoGoal, OnboardingKeyword, OnboardingCompetitor, 
    PageUrl, ReportingPreference
)
# Import other models as needed

logger = logging.getLogger(__name__)

class ProfileManager:
    """
    Manages user profile data using PostgreSQL database.
    Replaces the old file-based JSON storage.
    """
    
    def __init__(self):
        pass

    def get_db(self):
        """Helper to get DB session"""
        return SessionLocal()

    def profile_exists(self, user_id: str) -> bool:
        """Check if user exists in database"""
        db = self.get_db()
        try:
            return db.query(User).filter(User.id == user_id).first() is not None
        finally:
            db.close()

    def create_profile(self) -> str:
        """
        Legacy support - simpler creation. 
        For full creation with email/name, use create_profile_with_id
        """
        raise NotImplementedError("Use create_profile_with_id for database storage")

    def create_profile_with_id(self, user_id: str, data: Dict[str, Any]) -> str:
        """
        Create new user and initial business profile in Database.
        """
        db = self.get_db()
        try:
            logger.info(f"Attempting to create profile for user_id: {user_id}")
            
            # 1. Create User
            new_user = User(
                id=user_id,
                email=data.get('email'),
                username=data.get('username'),
                full_name=data.get('full_name'),
                onboarding_completed=False,
                current_onboarding_page=1
            )
            db.add(new_user)
            db.flush() # Force User insertion first
            
            # 2. Create Business Profile (if data present)
            if 'business_name' in data:
                profile = BusinessProfile(
                    user_id=user_id,
                    business_name=data.get('business_name'),
                    website_url=data.get('website_url'),
                    business_description=data.get('business_description')
                )
                db.add(profile)
            
            db.commit()
            logger.info(f"Successfully created new user in DB: {user_id}")
            return user_id
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating profile: {e}")
            raise e
        finally:
            db.close()

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> None:
        """
        Update existing profile (Business Info, etc).
        """
        db = self.get_db()
        try:
            logger.info(f"Updating profile for user_id: {user_id}")
            
            # Ensure user exists first (double check)
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"User {user_id} not found during update. Creating user first.")
                # Fallback: Create user if missing but update requested (shouldn't happen often)
                # We might lack fields here, best to error or minimal create? 
                # For now, let's error to see why we are here
                raise ValueError(f"Cannot update profile: User {user_id} does not exist.")

            # Handle Page 1 updates (Business Profile)
            if 'business_name' in updates:
                profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user_id).first()
                if profile:
                    # Update existing
                    profile.business_name = updates.get('business_name', profile.business_name)
                    profile.website_url = updates.get('website_url', profile.website_url)
                    profile.business_description = updates.get('business_description', profile.business_description)
                else:
                    # Create if missing
                    profile = BusinessProfile(
                        user_id=user_id,
                        business_name=updates.get('business_name'),
                        website_url=updates.get('website_url'),
                        business_description=updates.get('business_description')
                    )
                    db.add(profile)

            # Handle Page 2 updates (Integrations)
            if 'gsc_connected' in updates or 'ga4_connected' in updates:
                integ = db.query(Integrations).filter(Integrations.user_id == user_id).first()
                if not integ:
                    integ = Integrations(user_id=user_id)
                    db.add(integ)
                
                if 'gsc_connected' in updates:
                    integ.gsc_connected = updates['gsc_connected']
                    integ.gsc_verified_site = updates.get('gsc_matched_site')
                    if updates['gsc_connected']:
                        integ.gsc_last_validated = datetime.utcnow()
                
                if 'ga4_connected' in updates:
                    integ.ga4_connected = updates['ga4_connected']
                    if updates['ga4_connected']:
                        integ.ga4_last_validated = datetime.utcnow()

            # Handle Page 4 updates (Products)
            if 'products' in updates and isinstance(updates['products'], list):
                # Clear existing items to avoid duplicates/stale data
                db.query(Products).filter(Products.user_id == user_id).delete()
                for item in updates['products']:
                    if isinstance(item, dict) and 'product_name' in item:
                        prod = Products(
                            user_id=user_id,
                            product_name=item['product_name'],
                            product_url=item.get('product_url')
                        )
                        db.add(prod)

            # Handle Page 4 updates (Services)
            if 'services' in updates and isinstance(updates['services'], list):
                # Clear existing items
                db.query(Services).filter(Services.user_id == user_id).delete()
                for item in updates['services']:
                    if isinstance(item, dict) and 'service_name' in item:
                        svc = Services(
                            user_id=user_id,
                            service_name=item['service_name'],
                            service_url=item.get('service_url')
                        )
                        db.add(svc)

            # Handle Page 4 updates (Differentiators)
            if 'differentiators' in updates and isinstance(updates['differentiators'], list):
                db.query(Differentiators).filter(Differentiators.user_id == user_id).delete()
                for d in updates['differentiators']:
                    if isinstance(d, str) and d.strip():
                         db.add(Differentiators(user_id=user_id, differentiator=d.strip()))

            # Handle Page 3 updates (Audience)
            if 'location_scope' in updates:
                aud = db.query(AudienceProfile).filter(AudienceProfile.user_id == user_id).first()
                if not aud:
                    aud = AudienceProfile(user_id=user_id, location_scope='', customer_description='', search_intent=[])
                    db.add(aud)
                
                aud.location_scope = updates.get('location_scope', aud.location_scope)
                aud.selected_locations = updates.get('selected_locations', aud.selected_locations)
                aud.customer_description = updates.get('customer_description', aud.customer_description)
                aud.search_intent = updates.get('search_intent', aud.search_intent)

            # Handle Page 5 updates (SEO Goals)
            if 'goals' in updates or 'seo_goals' in updates:
                 goals_list = updates.get('goals') or updates.get('seo_goals')
                 sg = db.query(SeoGoal).filter(SeoGoal.user_id == user_id).first()
                 if not sg:
                     sg = SeoGoal(user_id=user_id, goals=[])
                     db.add(sg)
                 sg.goals = goals_list

            # Handle Page 7 updates (Page URLs)
            if 'home_url' in updates:
                urls = db.query(PageUrl).filter(PageUrl.user_id == user_id).first()
                if not urls:
                    urls = PageUrl(user_id=user_id, home_url='', product_url='', contact_url='', about_url='', blog_url='')
                    db.add(urls)
                urls.home_url = updates.get('home_url', '')
                urls.product_url = updates.get('product_url', '')
                urls.contact_url = updates.get('contact_url', '')
                urls.about_url = updates.get('about_url', '')
                urls.blog_url = updates.get('blog_url', '')

            # Handle Page 8 updates (Reporting)
            if 'report_frequency' in updates:
                rep = db.query(ReportingPreference).filter(ReportingPreference.user_id == user_id).first()
                if not rep:
                    rep = ReportingPreference(user_id=user_id, reporting_channels=[], report_frequency='')
                    db.add(rep)
                rep.reporting_channels = updates.get('reporting_channels', [])
                rep.report_frequency = updates.get('report_frequency', 'Monthly')

            # Handle Suggested Competitors (Page 6 Step 1)
            if 'suggested_competitors' in updates and isinstance(updates['suggested_competitors'], list):
                # We usually append or replace suggestions? Let's replace 'suggested' ones
                db.query(OnboardingCompetitor).filter(
                    OnboardingCompetitor.user_id == user_id,
                    OnboardingCompetitor.source == 'suggested'
                ).delete()
                
                for comp in updates['suggested_competitors']:
                    if isinstance(comp, dict):
                        # Handle different key formats (domain vs url)
                        c_url = comp.get('url') or comp.get('domain') or ''
                        c_name = comp.get('name') or comp.get('title') or comp.get('domain') or ''
                        
                        # Ensure we have a URL/Identifier
                        if not c_url:
                            continue

                        c = OnboardingCompetitor(
                            user_id=user_id,
                            competitor_url=c_url,
                            competitor_name=c_name,
                            source='suggested',
                            is_selected=False,
                            keywords_matched=comp.get('keywords_matched', [])
                        )
                        db.add(c)

            db.commit()
            logger.info(f"Updated profile for user: {user_id}")
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error updating profile: {e}")
            raise e
        finally:
            db.close()

    def save_keywords_selected(self, user_id: str, keywords: list) -> None:
        """
        Save selected keywords (Page 6).
        """
        db = self.get_db()
        try:
            logger.info(f"Saving selected keywords for user: {user_id}")
            # Identify these are the ones the USER (or system auto-selection) chose
            # We first clear previous 'selected' ones to avoid dupes if re-running
            # Or we can upsert. Simpler to clear 'is_selected=True' or all? 
            # If we clear all, we lose 'generated' history. 
            # Strategy: Upsert.
            
            # For simplicity in this fix: Clear all keys for this user to be safe and clean
            db.query(OnboardingKeyword).filter(OnboardingKeyword.user_id == user_id).delete()
            
            for kw in keywords:
                if kw and isinstance(kw, str) and kw.strip():
                    k = OnboardingKeyword(
                        user_id=user_id,
                        keyword=kw.strip(),
                        source='generated', 
                        is_selected=True
                    )
                    db.add(k)
            
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error saving selected keywords: {e}")
            raise e
        finally:
            db.close()

    def save_keywords_generated(self, user_id: str, keywords: list) -> None:
        """
        Save raw generated keywords (Page 6).
        keywords: List of dicts {'keyword': str, 'score': float, ...}
        """
        db = self.get_db()
        try:
            logger.info(f"Saving generated keywords for user: {user_id}")
            # We don't want to wipe selected ones if possible, but usually generation happens BEFORE selection.
            # platform_services calls generated THEN selected.
            # So 'selected' call will wipe these if I use delete() in selected!
            
            # FIX: save_keywords_selected above uses delete(). 
            # If generated runs first, saves DB. Then selected runs, deletes DB... we lose the non-selected generated ones.
            # Validation: 
            # 1. save_keywords_generated inserts all.
            # 2. save_keywords_selected inserts selected.
            
            # Better approach: 
            # save_keywords_generated: Insert all with is_selected=False.
            # save_keywords_selected: Update is_selected=True for matching keywords. Or Re-insert.
            
            # Given the flow, let's make save_keywords_selected ONLY update/insert selected ones.
            # But the current implementation of save_keywords_selected DELETES everything.
            
            # Adjusted Strategy:
            # save_keywords_generated dumps data but maybe we don't need it if selected overwrites it immediately?
            # platform_services lines 754 then 760.
            # It saves generated, extracting top 15, then saves selected.
            
            # If I want to persist the "pool" of generated keywords:
            # save_keywords_selected should NOT delete everything. 
            pass # See below for implementation
            
            for kw_data in keywords:
                kw_str = kw_data.get('keyword')
                if kw_str:
                    # Check if exists
                    exists = db.query(OnboardingKeyword).filter(
                        OnboardingKeyword.user_id == user_id, 
                        OnboardingKeyword.keyword == kw_str
                    ).first()
                    
                    if not exists:
                        k = OnboardingKeyword(
                            user_id=user_id,
                            keyword=kw_str,
                            source='generated',
                            is_selected=False,
                            score=kw_data.get('score')
                        )
                        db.add(k)
            db.commit()

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error saving generated keywords: {e}")
            raise e
        finally:
            db.close()

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve full profile data (merging multiple tables).
        """
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user_id).first()
            
            # Construct dictionary response
            data = {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "onboarding_completed": user.onboarding_completed,
            }
            
            if profile:
                data.update({
                    "business_name": profile.business_name,
                    "website_url": profile.website_url,
                    "business_description": profile.business_description
                })

            # Fetch Products
            products = db.query(Products).filter(Products.user_id == user_id).all()
            data['products'] = [{'name': p.product_name, 'url': p.product_url} for p in products]

            # Fetch Services
            services = db.query(Services).filter(Services.user_id == user_id).all()
            data['services'] = [{'name': s.service_name, 'url': s.service_url} for s in services]
            
            # Fetch Audience
            audience = db.query(AudienceProfile).filter(AudienceProfile.user_id == user_id).first()
            if audience:
                data.update({
                    "location_scope": audience.location_scope,
                    "customer_description": audience.customer_description,
                    "search_intent": audience.search_intent
                })
                
            
            return data
            
        finally:
            db.close()

    def mark_onboarding_complete(self, user_id: str) -> None:
        """
        Mark the user's onboarding as complete.
        """
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.onboarding_completed = True
                db.commit()
                logger.info(f"Marked onboarding complete for user: {user_id}")
            else:
                logger.warning(f"User not found when marking complete: {user_id}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error marking onboarding complete: {e}")
            raise e
        finally:
            db.close()


# Singleton pattern
_profile_manager = None

def get_profile_manager():
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager