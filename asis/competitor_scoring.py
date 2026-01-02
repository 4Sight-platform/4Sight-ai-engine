"""
Competitor Scoring Service
Computes SEO visibility scores for competitors
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import date

logger = logging.getLogger(__name__)


class CompetitorScoringService:
    """
    Service for computing competitor SEO visibility scores.
    
    Visibility Score (0-100) based on:
    - Keyword visibility (top 10 rankings)
    - Click/impression share
    - SERP feature presence
    """
    
    def __init__(self):
        pass
    
    def compute_visibility_score(
        self,
        domain: str,
        keyword_rankings: List[Dict],
        serp_features: List[Dict] = None,
        total_keywords: int = 20
    ) -> Dict[str, Any]:
        """
        Compute SEO visibility score for a domain.
        
        Args:
            domain: Domain to score
            keyword_rankings: List of {keyword, position} for this domain
            serp_features: List of SERP features where domain appears
            total_keywords: Total tracked keywords for normalization
            
        Returns:
            Dict with visibility_score and breakdown
        """
        score = 0
        factors = {}
        
        # Factor 1: Keyword Visibility (up to 60 points)
        # Points based on ranking positions
        ranking_points = 0
        top3_count = 0
        top10_count = 0
        
        for ranking in keyword_rankings:
            position = ranking.get("position", 100)
            if position <= 3:
                ranking_points += 10
                top3_count += 1
            elif position <= 5:
                ranking_points += 7
            elif position <= 10:
                ranking_points += 4
                top10_count += 1
            elif position <= 20:
                ranking_points += 1
        
        # Normalize to 60 points max
        max_ranking_points = total_keywords * 10  # If all #1
        keyword_score = min((ranking_points / max_ranking_points) * 60, 60) if max_ranking_points > 0 else 0
        
        factors["keyword_visibility"] = {
            "score": round(keyword_score, 1),
            "top3_count": top3_count,
            "top10_count": top10_count + top3_count,
            "ranking_keywords": len(keyword_rankings)
        }
        score += keyword_score
        
        # Factor 2: SERP Feature Presence (up to 25 points)
        feature_points = 0
        features_owned = []
        
        if serp_features:
            for feature in serp_features:
                if feature.get("domain_present", False):
                    feature_points += 5
                    features_owned.append(feature.get("feature_type", "unknown"))
        
        feature_score = min(feature_points, 25)
        factors["serp_features"] = {
            "score": feature_score,
            "features_owned": features_owned
        }
        score += feature_score
        
        # Factor 3: Domain Strength Bonus (up to 15 points)
        # Based on consistency of rankings
        if len(keyword_rankings) >= total_keywords * 0.8:
            domain_bonus = 15
        elif len(keyword_rankings) >= total_keywords * 0.5:
            domain_bonus = 10
        elif len(keyword_rankings) >= total_keywords * 0.2:
            domain_bonus = 5
        else:
            domain_bonus = 0
        
        factors["domain_strength"] = {
            "score": domain_bonus,
            "coverage_ratio": len(keyword_rankings) / total_keywords if total_keywords > 0 else 0
        }
        score += domain_bonus
        
        return {
            "domain": domain,
            "visibility_score": round(min(score, 100), 1),
            "factors": factors
        }
    
    def rank_competitors(
        self,
        user_domain: str,
        user_score: float,
        competitor_scores: List[Dict]
    ) -> Dict[str, Any]:
        """
        Rank all domains (user + competitors) by visibility score.
        
        Args:
            user_domain: User's domain
            user_score: User's visibility score
            competitor_scores: List of competitor score dicts
            
        Returns:
            Dict with rankings and user's position
        """
        # Combine user and competitors
        all_scores = [
            {"domain": user_domain, "visibility_score": user_score, "is_user": True}
        ]
        
        for comp in competitor_scores:
            all_scores.append({
                "domain": comp["domain"],
                "visibility_score": comp["visibility_score"],
                "is_user": False
            })
        
        # Sort by visibility score (descending)
        ranked = sorted(all_scores, key=lambda x: x["visibility_score"], reverse=True)
        
        # Add rank
        for i, entry in enumerate(ranked):
            entry["rank"] = i + 1
        
        # Find user's rank
        user_rank = next((e["rank"] for e in ranked if e["is_user"]), None)
        
        return {
            "rankings": ranked,
            "user_rank": user_rank,
            "total_competitors": len(competitor_scores),
            "user_visibility_score": user_score
        }
    
    def compute_competitive_gap(
        self,
        user_score: float,
        competitors: List[Dict]
    ) -> Dict[str, Any]:
        """
        Compute the gap between user and competitors.
        
        Returns:
            Dict with gap analysis
        """
        if not competitors:
            return {
                "gap_to_leader": 0,
                "gap_to_average": 0,
                "position_summary": "No competitors to compare"
            }
        
        scores = [c["visibility_score"] for c in competitors]
        leader_score = max(scores)
        avg_score = sum(scores) / len(scores)
        
        gap_to_leader = leader_score - user_score
        gap_to_average = avg_score - user_score
        
        if user_score >= leader_score:
            summary = "Leading the competition"
        elif user_score >= avg_score:
            summary = "Above average, room to improve"
        else:
            summary = "Below average, significant improvements needed"
        
        return {
            "gap_to_leader": round(gap_to_leader, 1),
            "gap_to_average": round(gap_to_average, 1),
            "leader_score": round(leader_score, 1),
            "average_score": round(avg_score, 1),
            "position_summary": summary
        }
