"""
Custom Chains
Utility chains for combining phase operations
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.nodes import get_phase_node
from orchestration.state_manager import PhaseInput, PhaseOutput


class ChainExecutor:
    """
    Execute multiple phases as a chain
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def execute_chain(self, phase_names: List[str], initial_input: PhaseInput) -> Dict[str, PhaseOutput]:
        """
        Execute a chain of phases
        
        Args:
            phase_names: List of phase names to execute
            initial_input: Initial input for first phase
        
        Returns:
            Dictionary of phase outputs
        """
        outputs = {}
        current_input = initial_input
        
        for phase_name in phase_names:
            # Get phase node
            node = get_phase_node(phase_name)
            
            # Execute phase
            output = node.execute(current_input)
            
            # Store output
            outputs[phase_name] = output
            
            # If phase failed, stop chain
            if not output.success:
                break
            
            # Update input for next phase
            current_input.add_previous_output(phase_name, output.to_dict())
        
        return outputs


class MarketToGSCChain:
    """
    Chain that combines Market Analysis and GSC Reality Check
    Useful for getting complete picture of keyword landscape
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.executor = ChainExecutor(user_id)
    
    def execute(self, keywords: List[str], profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Phase 2 (Market) and Phase 3 (GSC) together
        
        Args:
            keywords: Keywords to analyze
            profile: User profile
        
        Returns:
            Combined results from both phases
        """
        # Create initial input
        phase_input = PhaseInput(self.user_id, keywords, profile)
        
        # Execute chain
        outputs = self.executor.execute_chain(
            ["phase2_market", "phase3_gsc"],
            phase_input
        )
        
        # Combine results
        market_output = outputs.get("phase2_market")
        gsc_output = outputs.get("phase3_gsc")
        
        if not market_output or not market_output.success:
            return {"error": "Market analysis failed"}
        
        if not gsc_output or not gsc_output.success:
            return {"error": "GSC analysis failed"}
        
        return {
            "market_data": market_output.data,
            "gsc_data": gsc_output.data,
            "combined_insights": self._generate_insights(
                market_output.data,
                gsc_output.data
            )
        }
    
    def _generate_insights(self, market_data: Dict, gsc_data: Dict) -> Dict[str, Any]:
        """Generate insights from combined market and GSC data"""
        
        keywords_data = market_data.get("keyword_data", [])
        gsc_keywords = {
            item["keyword"]: item 
            for item in gsc_data.get("gsc_data", [])
        }
        
        insights = {
            "high_volume_no_rank": [],
            "low_volume_high_rank": [],
            "potential_winners": []
        }
        
        for kw_data in keywords_data:
            keyword = kw_data["keyword"]
            volume = kw_data.get("avg_monthly_searches", 0)
            
            if keyword in gsc_keywords:
                position = gsc_keywords[keyword].get("position", 100)
                
                # Low volume but ranking well
                if volume < 500 and position < 10:
                    insights["low_volume_high_rank"].append({
                        "keyword": keyword,
                        "volume": volume,
                        "position": position
                    })
                
                # High volume and good position - potential winner
                elif volume > 1000 and position < 20:
                    insights["potential_winners"].append({
                        "keyword": keyword,
                        "volume": volume,
                        "position": position
                    })
            else:
                # High volume but not ranking
                if volume > 1000:
                    insights["high_volume_no_rank"].append({
                        "keyword": keyword,
                        "volume": volume
                    })
        
        return insights


class AnalysisToActionChain:
    """
    Chain that combines Gap Analysis and Competitor Intelligence
    Provides actionable recommendations
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.executor = ChainExecutor(user_id)
    
    def execute(self, market_data: Dict, gsc_data: Dict) -> Dict[str, Any]:
        """
        Run Phase 4 (Gap Analysis) and Phase 5 (Competitors)
        
        Args:
            market_data: Results from Phase 2
            gsc_data: Results from Phase 3
        
        Returns:
            Action recommendations
        """
        # Create input with previous phase outputs
        phase_input = PhaseInput(self.user_id, [], {})
        phase_input.add_previous_output("phase2_market", {"data": market_data})
        phase_input.add_previous_output("phase3_gsc", {"data": gsc_data})
        
        # Execute chain
        outputs = self.executor.execute_chain(
            ["phase4_gap_analysis", "phase5_competitors"],
            phase_input
        )
        
        # Combine results
        gap_output = outputs.get("phase4_gap_analysis")
        competitor_output = outputs.get("phase5_competitors")
        
        if not gap_output or not gap_output.success:
            return {"error": "Gap analysis failed"}
        
        if not competitor_output or not competitor_output.success:
            return {"error": "Competitor analysis failed"}
        
        return {
            "gap_analysis": gap_output.data,
            "competitor_data": competitor_output.data,
            "action_items": self._generate_action_items(
                gap_output.data,
                competitor_output.data
            )
        }
    
    def _generate_action_items(self, gap_data: Dict, competitor_data: Dict) -> List[Dict]:
        """Generate action items from analysis"""
        
        action_items = []
        
        # Untapped gold opportunities
        untapped_gold = gap_data.get("untapped_gold", [])
        competitor_insights = competitor_data.get("competitor_data", {})
        
        for keyword in untapped_gold[:5]:  # Top 5 opportunities
            if keyword in competitor_insights:
                top_urls = competitor_insights[keyword].get("top_urls", [])
                
                action_items.append({
                    "priority": "HIGH",
                    "keyword": keyword,
                    "action": "Create content targeting this keyword",
                    "reason": "High search volume with no current ranking",
                    "competitor_count": len(top_urls),
                    "example_url": top_urls[0]["url"] if top_urls else None
                })
        
        # Underperformers
        underperformers = gap_data.get("underperformers", [])
        for keyword in underperformers[:3]:  # Top 3
            action_items.append({
                "priority": "MEDIUM",
                "keyword": keyword,
                "action": "Optimize existing content",
                "reason": "Currently ranking but underperforming"
            })
        
        return action_items


class QuickAnalysisChain:
    """
    Quick analysis chain for rapid insights
    Skips Phase 1 (Tuning) and goes straight to analysis
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.executor = ChainExecutor(user_id)
    
    def execute(self, keywords: List[str], profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Quick analysis: Market → GSC → Gap Analysis
        
        Args:
            keywords: Keywords to analyze
            profile: User profile
        
        Returns:
            Quick analysis results
        """
        # Create initial input
        phase_input = PhaseInput(self.user_id, keywords, profile)
        
        # Execute chain (skip Phase 1)
        outputs = self.executor.execute_chain(
            ["phase2_market", "phase3_gsc", "phase4_gap_analysis"],
            phase_input
        )
        
        # Check if all phases succeeded
        for phase_name, output in outputs.items():
            if not output.success:
                return {"error": f"{phase_name} failed"}
        
        # Get gap analysis results
        gap_output = outputs.get("phase4_gap_analysis")
        
        return {
            "quick_insights": {
                "untapped_opportunities": len(gap_output.data.get("untapped_gold", [])),
                "underperformers": len(gap_output.data.get("underperformers", [])),
                "total_keywords": len(keywords)
            },
            "full_results": {
                phase_name: output.data 
                for phase_name, output in outputs.items()
            }
        }


# Chain registry
CHAINS = {
    "market_to_gsc": MarketToGSCChain,
    "analysis_to_action": AnalysisToActionChain,
    "quick_analysis": QuickAnalysisChain
}


def get_chain(chain_name: str, user_id: str):
    """
    Get chain instance
    
    Args:
        chain_name: Name of the chain
        user_id: User ID
    
    Returns:
        Chain instance
    """
    chain_class = CHAINS.get(chain_name)
    if not chain_class:
        raise ValueError(f"Unknown chain: {chain_name}")
    
    return chain_class(user_id)


# For testing
if __name__ == "__main__":
    # Test quick analysis chain
    test_user_id = "test_user"
    test_keywords = ["seo automation", "keyword research", "competitor analysis"]
    test_profile = {"website_url": "https://example.com"}
    
    chain = get_chain("quick_analysis", test_user_id)
    results = chain.execute(test_keywords, test_profile)
    
    print("Quick Analysis Results:")
    print(results)