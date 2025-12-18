"""
Workflow Nodes
Defines nodes for each phase in the SEO automation workflow
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.state_manager import PhaseInput, PhaseOutput


class BasePhaseNode:
    """
    Base class for phase nodes
    """
    
    def __init__(self, phase_name: str):
        self.phase_name = phase_name
        self.started_at = None
        self.completed_at = None
    
    def execute(self, phase_input: PhaseInput) -> PhaseOutput:
        """
        Execute the phase
        
        Args:
            phase_input: Input data for the phase
        
        Returns:
            PhaseOutput with results
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def log(self, message: str):
        """Log a message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{self.phase_name}] {message}")


class Phase1TuningNode(BasePhaseNode):
    """
    Phase 1: Keyword Tuning
    Refines keywords selected during onboarding
    """
    
    def __init__(self):
        super().__init__("phase1_tuning")
    
    def execute(self, phase_input: PhaseInput) -> PhaseOutput:
        """
        Execute Phase 1: Tuning
        
        Input:
            - keywords: List of keywords from onboarding
        
        Output:
            - final_keywords: Refined keyword list
            - removed_keywords: Keywords that were removed
            - added_keywords: Keywords that were added
        """
        self.log("Starting Phase 1: Keyword Tuning")
        self.started_at = datetime.now()
        
        try:
            keywords = phase_input.keywords
            profile = phase_input.profile
            
            self.log(f"Received {len(keywords)} keywords from onboarding")
            
            # Import Phase 1 module
            try:
                from phases.phase1_tuning.keyword_refiner import refine_keywords
                
                # Run keyword refinement
                self.log("Refining keywords...")
                refined_data = refine_keywords(keywords, profile)
                
                final_keywords = refined_data.get("final_keywords", keywords)
                removed = refined_data.get("removed_keywords", [])
                added = refined_data.get("added_keywords", [])
                
                self.log(f"Refinement complete: {len(final_keywords)} final keywords")
                self.log(f"  - Removed: {len(removed)}")
                self.log(f"  - Added: {len(added)}")
                
                output_data = {
                    "final_keywords": final_keywords,
                    "removed_keywords": removed,
                    "added_keywords": added,
                    "refinement_notes": refined_data.get("notes", "")
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
            
            except ImportError:
                # Phase 1 not implemented yet - pass through keywords
                self.log("Phase 1 module not implemented, passing through keywords")
                
                output_data = {
                    "final_keywords": keywords,
                    "removed_keywords": [],
                    "added_keywords": [],
                    "refinement_notes": "Phase 1 not yet implemented"
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
        
        except Exception as e:
            self.log(f"Error in Phase 1: {str(e)}")
            return PhaseOutput(self.phase_name, False, {}, error=str(e))


class Phase2MarketNode(BasePhaseNode):
    """
    Phase 2: Market Analysis
    Gets search volume, CPC, competition data from Google Keyword Planner
    """
    
    def __init__(self):
        super().__init__("phase2_market")
    
    def execute(self, phase_input: PhaseInput) -> PhaseOutput:
        """
        Execute Phase 2: Market Analysis
        
        Input:
            - keywords: Final keywords from Phase 1
        
        Output:
            - keyword_data: List of dicts with volume, CPC, competition
        """
        self.log("Starting Phase 2: Market Analysis")
        self.started_at = datetime.now()
        
        try:
            # Get final keywords from Phase 1
            phase1_output = phase_input.get_previous_output("phase1_tuning")
            if phase1_output:
                keywords = phase1_output["data"]["final_keywords"]
            else:
                keywords = phase_input.keywords
            
            self.log(f"Analyzing {len(keywords)} keywords")
            
            # Import Phase 2 module
            try:
                from phases.phase2_market.keyword_planner_client import get_keyword_data
                
                # Get market data
                self.log("Fetching data from Google Keyword Planner...")
                keyword_data = get_keyword_data(keywords)
                
                self.log(f"Market data retrieved for {len(keyword_data)} keywords")
                
                output_data = {
                    "keyword_data": keyword_data,
                    "total_keywords": len(keyword_data),
                    "avg_search_volume": sum(k.get("avg_monthly_searches", 0) for k in keyword_data) / len(keyword_data) if keyword_data else 0
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
            
            except ImportError:
                # Phase 2 not implemented yet - return mock data
                self.log("Phase 2 module not implemented, returning mock data")
                
                keyword_data = [
                    {
                        "keyword": kw,
                        "avg_monthly_searches": 1000,
                        "competition": "MEDIUM",
                        "low_top_of_page_bid_micros": 1000000,
                        "high_top_of_page_bid_micros": 3000000
                    }
                    for kw in keywords
                ]
                
                output_data = {
                    "keyword_data": keyword_data,
                    "total_keywords": len(keyword_data),
                    "avg_search_volume": 1000,
                    "note": "Phase 2 not yet implemented - mock data"
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
        
        except Exception as e:
            self.log(f"Error in Phase 2: {str(e)}")
            return PhaseOutput(self.phase_name, False, {}, error=str(e))


class Phase3GSCNode(BasePhaseNode):
    """
    Phase 3: GSC Reality Check
    Gets current rankings from Google Search Console
    """
    
    def __init__(self):
        super().__init__("phase3_gsc")
    
    def execute(self, phase_input: PhaseInput) -> PhaseOutput:
        """
        Execute Phase 3: GSC Reality Check
        
        Input:
            - keywords: Keywords to check
            - site_url: Website URL from profile
        
        Output:
            - gsc_data: Current rankings (impressions, clicks, position, CTR)
        """
        self.log("Starting Phase 3: GSC Reality Check")
        self.started_at = datetime.now()
        
        try:
            # Get keywords from Phase 1
            phase1_output = phase_input.get_previous_output("phase1_tuning")
            if phase1_output:
                keywords = phase1_output["data"]["final_keywords"]
            else:
                keywords = phase_input.keywords
            
            site_url = phase_input.profile.get("website_url", "")
            
            self.log(f"Checking GSC data for {len(keywords)} keywords")
            self.log(f"Site: {site_url}")
            
            # Import Phase 3 module
            try:
                from phases.phase3_gsc.client import GSCClient
                
                # Get GSC data
                self.log("Fetching data from Google Search Console...")
                gsc_client = GSCClient()
                gsc_data = gsc_client.get_keyword_performance(site_url, keywords)
                
                self.log(f"GSC data retrieved for {len(gsc_data)} keywords")
                
                # Calculate stats
                ranked_keywords = [k for k in gsc_data if k.get("position", 0) > 0]
                avg_position = sum(k.get("position", 0) for k in ranked_keywords) / len(ranked_keywords) if ranked_keywords else 0
                
                output_data = {
                    "gsc_data": gsc_data,
                    "total_keywords_checked": len(keywords),
                    "keywords_with_rankings": len(ranked_keywords),
                    "avg_position": avg_position,
                    "total_impressions": sum(k.get("impressions", 0) for k in gsc_data),
                    "total_clicks": sum(k.get("clicks", 0) for k in gsc_data)
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
            
            except ImportError:
                # Phase 3 not implemented yet - return mock data
                self.log("Phase 3 module not fully integrated, returning mock data")
                
                gsc_data = [
                    {
                        "keyword": kw,
                        "impressions": 100,
                        "clicks": 5,
                        "position": 15.5,
                        "ctr": 0.05
                    }
                    for kw in keywords[:len(keywords)//2]  # Only half have rankings
                ]
                
                output_data = {
                    "gsc_data": gsc_data,
                    "total_keywords_checked": len(keywords),
                    "keywords_with_rankings": len(gsc_data),
                    "avg_position": 15.5,
                    "total_impressions": len(gsc_data) * 100,
                    "total_clicks": len(gsc_data) * 5,
                    "note": "Phase 3 not fully integrated - mock data"
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
        
        except Exception as e:
            self.log(f"Error in Phase 3: {str(e)}")
            return PhaseOutput(self.phase_name, False, {}, error=str(e))


class Phase4GapAnalysisNode(BasePhaseNode):
    """
    Phase 4: Gap Analysis
    Classifies keywords into strategy buckets
    """
    
    def __init__(self):
        super().__init__("phase4_gap_analysis")
    
    def execute(self, phase_input: PhaseInput) -> PhaseOutput:
        """
        Execute Phase 4: Gap Analysis
        
        Input:
            - market_data: From Phase 2
            - gsc_data: From Phase 3
        
        Output:
            - classified_keywords: Categorized by strategy
            - untapped_gold: High volume + no rank
            - underperformers: Ranked but low CTR
            - low_priority: Low volume or high competition
        """
        self.log("Starting Phase 4: Gap Analysis")
        self.started_at = datetime.now()
        
        try:
            # Get data from previous phases
            phase2_output = phase_input.get_previous_output("phase2_market")
            phase3_output = phase_input.get_previous_output("phase3_gsc")
            
            if not phase2_output or not phase3_output:
                return PhaseOutput(self.phase_name, False, {}, 
                                 error="Missing data from Phase 2 or 3")
            
            market_data = phase2_output["data"]["keyword_data"]
            gsc_data = phase3_output["data"]["gsc_data"]
            
            self.log(f"Analyzing {len(market_data)} keywords")
            
            # Import Phase 4 module
            try:
                from phases.phase4_gap_analysis.classifier import classify_keywords
                
                # Classify keywords
                self.log("Classifying keywords into strategy buckets...")
                classification = classify_keywords(market_data, gsc_data)
                
                untapped_gold = classification.get("untapped_gold", [])
                underperformers = classification.get("underperformers", [])
                low_priority = classification.get("low_priority", [])
                
                self.log(f"Classification complete:")
                self.log(f"  - Untapped Gold: {len(untapped_gold)}")
                self.log(f"  - Under-Performers: {len(underperformers)}")
                self.log(f"  - Low Priority: {len(low_priority)}")
                
                output_data = {
                    "classified_keywords": classification,
                    "untapped_gold": untapped_gold,
                    "underperformers": underperformers,
                    "low_priority": low_priority,
                    "total_classified": len(untapped_gold) + len(underperformers) + len(low_priority)
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
            
            except ImportError:
                # Phase 4 not implemented yet - simple classification
                self.log("Phase 4 module not implemented, using simple classification")
                
                # Simple classification logic
                untapped_gold = []
                underperformers = []
                low_priority = []
                
                gsc_keywords = {item["keyword"]: item for item in gsc_data}
                
                for item in market_data:
                    keyword = item["keyword"]
                    volume = item.get("avg_monthly_searches", 0)
                    
                    # Check if ranked in GSC
                    if keyword in gsc_keywords:
                        # Has ranking - check if underperforming
                        position = gsc_keywords[keyword].get("position", 100)
                        if position > 10 and volume > 500:
                            underperformers.append(keyword)
                        else:
                            low_priority.append(keyword)
                    else:
                        # No ranking
                        if volume > 1000:
                            untapped_gold.append(keyword)
                        else:
                            low_priority.append(keyword)
                
                classification = {
                    "untapped_gold": untapped_gold,
                    "underperformers": underperformers,
                    "low_priority": low_priority
                }
                
                output_data = {
                    "classified_keywords": classification,
                    "untapped_gold": untapped_gold,
                    "underperformers": underperformers,
                    "low_priority": low_priority,
                    "total_classified": len(untapped_gold) + len(underperformers) + len(low_priority),
                    "note": "Phase 4 not yet implemented - simple classification"
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
        
        except Exception as e:
            self.log(f"Error in Phase 4: {str(e)}")
            return PhaseOutput(self.phase_name, False, {}, error=str(e))


class Phase5CompetitorsNode(BasePhaseNode):
    """
    Phase 5: Competitor Intelligence
    Scrapes top 10 URLs for untapped gold keywords
    """
    
    def __init__(self):
        super().__init__("phase5_competitors")
    
    def execute(self, phase_input: PhaseInput) -> PhaseOutput:
        """
        Execute Phase 5: Competitor Intelligence
        
        Input:
            - untapped_gold: Keywords from Phase 4
        
        Output:
            - competitor_data: Titles, descriptions, insights for top 10 URLs
        """
        self.log("Starting Phase 5: Competitor Intelligence")
        self.started_at = datetime.now()
        
        try:
            # Get untapped gold keywords from Phase 4
            phase4_output = phase_input.get_previous_output("phase4_gap_analysis")
            
            if not phase4_output:
                return PhaseOutput(self.phase_name, False, {}, 
                                 error="Missing data from Phase 4")
            
            untapped_gold = phase4_output["data"]["untapped_gold"]
            
            self.log(f"Analyzing competitors for {len(untapped_gold)} untapped gold keywords")
            
            # Import Phase 5 module
            try:
                from phases.phase5_competitors.scraper import scrape_competitors
                
                # Scrape competitor data
                self.log("Scraping competitor URLs...")
                competitor_data = scrape_competitors(untapped_gold)
                
                self.log(f"Competitor data retrieved for {len(competitor_data)} keywords")
                
                output_data = {
                    "competitor_data": competitor_data,
                    "keywords_analyzed": len(competitor_data),
                    "total_urls_scraped": sum(len(data.get("top_urls", [])) for data in competitor_data.values())
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
            
            except ImportError:
                # Phase 5 not implemented yet - return mock data
                self.log("Phase 5 module not implemented, returning mock data")
                
                competitor_data = {
                    kw: {
                        "keyword": kw,
                        "top_urls": [
                            {
                                "url": f"https://example.com/page-{i}",
                                "title": f"Example Title {i}",
                                "description": f"Example description for {kw}"
                            }
                            for i in range(1, 4)  # Top 3 URLs per keyword
                        ]
                    }
                    for kw in untapped_gold[:5]  # Limit to first 5 keywords
                }
                
                output_data = {
                    "competitor_data": competitor_data,
                    "keywords_analyzed": len(competitor_data),
                    "total_urls_scraped": len(competitor_data) * 3,
                    "note": "Phase 5 not yet implemented - mock data"
                }
                
                self.completed_at = datetime.now()
                return PhaseOutput(self.phase_name, True, output_data)
        
        except Exception as e:
            self.log(f"Error in Phase 5: {str(e)}")
            return PhaseOutput(self.phase_name, False, {}, error=str(e))


# Node registry
PHASE_NODES = {
    "phase1_tuning": Phase1TuningNode,
    "phase2_market": Phase2MarketNode,
    "phase3_gsc": Phase3GSCNode,
    "phase4_gap_analysis": Phase4GapAnalysisNode,
    "phase5_competitors": Phase5CompetitorsNode
}


def get_phase_node(phase_name: str) -> BasePhaseNode:
    """
    Get node instance for a phase
    
    Args:
        phase_name: Name of the phase
    
    Returns:
        Phase node instance
    """
    node_class = PHASE_NODES.get(phase_name)
    if not node_class:
        raise ValueError(f"Unknown phase: {phase_name}")
    
    return node_class()