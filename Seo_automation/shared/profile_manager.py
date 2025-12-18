"""
User Profile Manager
Handles loading, saving, and managing user onboarding profiles
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class ProfileManager:
    """Manage user profiles and onboarding data"""
    
    def __init__(self, storage_dir: str = "storage/user_profiles"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_user_id(self) -> str:
        """Generate unique user ID"""
        return f"user_{uuid.uuid4().hex[:12]}"
    
    def get_profile_path(self, user_id: str) -> Path:
        """Get path to user's profile directory"""
        return self.storage_dir / user_id
    
    def profile_exists(self, user_id: str) -> bool:
        """Check if user profile exists"""
        profile_file = self.get_profile_path(user_id) / "profile.json"
        return profile_file.exists()
    
    def create_profile(self, user_id: Optional[str] = None) -> str:
        """Create new user profile directory"""
        if user_id is None:
            user_id = self.generate_user_id()
        
        profile_dir = self.get_profile_path(user_id)
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty profile
        initial_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "onboarding_completed": False,
            "current_page": 1
        }
        
        self.save_profile(user_id, initial_data)
        return user_id
    
    def save_profile(self, user_id: str, data: Dict[str, Any]) -> None:
        """Save user profile data"""
        profile_dir = self.get_profile_path(user_id)
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        profile_file = profile_dir / "profile.json"
        
        # Add metadata
        data["user_id"] = user_id
        data["updated_at"] = datetime.now().isoformat()
        
        with open(profile_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user profile data"""
        profile_file = self.get_profile_path(user_id) / "profile.json"
        
        if not profile_file.exists():
            return None
        
        with open(profile_file, 'r') as f:
            return json.load(f)
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> None:
        """Update specific fields in user profile"""
        profile = self.load_profile(user_id)
        
        if profile is None:
            raise ValueError(f"Profile not found: {user_id}")
        
        profile.update(updates)
        self.save_profile(user_id, profile)
    
    def save_keywords_generated(self, user_id: str, keywords: list) -> None:
        """Save LLM-generated keyword suggestions"""
        profile_dir = self.get_profile_path(user_id)
        keywords_file = profile_dir / "keywords_generated.json"
        
        data = {
            "keywords": keywords,
            "generated_at": datetime.now().isoformat(),
            "count": len(keywords)
        }
        
        with open(keywords_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_keywords_generated(self, user_id: str) -> Optional[list]:
        """Load LLM-generated keywords"""
        keywords_file = self.get_profile_path(user_id) / "keywords_generated.json"
        
        if not keywords_file.exists():
            return None
        
        with open(keywords_file, 'r') as f:
            data = json.load(f)
            return data.get("keywords", [])
    
    def save_keywords_selected(self, user_id: str, keywords: list) -> None:
        """Save user's selected keywords"""
        profile_dir = self.get_profile_path(user_id)
        keywords_file = profile_dir / "keywords_selected.json"
        
        data = {
            "keywords": keywords,
            "selected_at": datetime.now().isoformat(),
            "count": len(keywords)
        }
        
        with open(keywords_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_keywords_selected(self, user_id: str) -> Optional[list]:
        """Load user's selected keywords"""
        keywords_file = self.get_profile_path(user_id) / "keywords_selected.json"
        
        if not keywords_file.exists():
            return None
        
        with open(keywords_file, 'r') as f:
            data = json.load(f)
            return data.get("keywords", [])
    
    def mark_onboarding_complete(self, user_id: str) -> None:
        """Mark onboarding as completed"""
        self.update_profile(user_id, {
            "onboarding_completed": True,
            "completed_at": datetime.now().isoformat()
        })
    
    def get_all_profiles(self) -> list:
        """Get list of all user profiles"""
        profiles = []
        
        for user_dir in self.storage_dir.iterdir():
            if user_dir.is_dir():
                profile = self.load_profile(user_dir.name)
                if profile:
                    profiles.append(profile)
        
        return profiles
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete user profile"""
        import shutil
        
        profile_dir = self.get_profile_path(user_id)
        
        if profile_dir.exists():
            shutil.rmtree(profile_dir)
            return True
        
        return False


# Singleton instance
_profile_manager = None

def get_profile_manager() -> ProfileManager:
    """Get singleton ProfileManager instance"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager