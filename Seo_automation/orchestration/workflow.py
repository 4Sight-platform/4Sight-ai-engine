"""
SEO Automation Workflow
Main orchestrator for running all 5 phases
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.state_manager import WorkflowStateManager, get_state_manager
from orchestration.nodes import get_phase_node
from shared.profile_manager import get_profile_manager


class WorkflowOrchestrator:
    """
    Orchestrates the complete 5-phase SEO automation workflow
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.state_manager = get_state_manager(user_id)
        self.profile_manager = get_profile_manager()
        
        self.phases = [
            "phase1_tuning",
            "phase2_market",
            "phase3_gsc",
            "phase4_gap_analysis",
            "phase5_competitors"
        ]
    
    def run_complete_workflow(self) -> Dict[str, Any]:
        """
        Run all 5 phases in sequence
        
        Returns:
            Final workflow results
        """
        print("\n" + "="*60)
        print("  SEO Automation - Complete Workflow")
        print("="*60 + "\n")
        
        try:
            # Load user profile and keywords
            profile = self.profile_manager.load_profile(self.user_id)
            keywords = self.profile_manager.load_keywords_selected(self.user_id)
            
            if not profile:
                raise ValueError(f"Profile not found for user: {self.user_id}")
            
            if not keywords:
                raise ValueError(f"No keywords found for user: {self.user_id}")
            
            print(f"→ User: {profile.get('business_name', 'Unknown')}")
            print(f"→ Keywords: {len(keywords)}")
            print(f"→ Starting workflow...\n")
            
            # Initialize workflow
            self.state_manager.start_workflow(keywords, profile)
            
            # Run each phase
            for i, phase_name in enumerate(self.phases, 1):
                print(f"\n{'='*60}")
                print(f"  Phase {i}/5: {self._get_phase_title(phase_name)}")
                print(f"{'='*60}\n")
                
                success = self.run_phase(phase_name)
                
                if not success:
                    print(f"\n✗ Workflow failed at {phase_name}")
                    self.state_manager.mark_workflow_failed(f"Failed at {phase_name}")
                    return self.state_manager.get_final_results()
                
                print(f"\n✓ Phase {i}/5 complete")
            
            # Mark workflow as complete
            self.state_manager.mark_workflow_complete()
            
            print("\n" + "="*60)
            print("  Workflow Complete!")
            print("="*60 + "\n")
            
            # Generate final report
            results = self.state_manager.get_final_results()
            self.generate_report(results)
            
            return results
        
        except Exception as e:
            print(f"\n✗ Workflow error: {str(e)}")
            self.state_manager.mark_workflow_failed(str(e))
            return self.state_manager.get_final_results()
    
    def run_phase(self, phase_name: str) -> bool:
        """
        Run a single phase
        
        Args:
            phase_name: Name of the phase to run
        
        Returns:
            True if successful
        """
        try:
            # Mark phase as started
            self.state_manager.state.set_phase(phase_name)
            
            # Create phase input
            phase_input = self.state_manager.create_phase_input(phase_name)
            
            # Get phase node
            node = get_phase_node(phase_name)
            
            # Execute phase
            output = node.execute(phase_input)
            
            # Save output
            self.state_manager.complete_phase(output)
            
            return output.success
        
        except Exception as e:
            print(f"Error running {phase_name}: {str(e)}")
            return False
    
    def run_phases_from(self, start_phase: str) -> Dict[str, Any]:
        """
        Run workflow starting from a specific phase
        
        Args:
            start_phase: Phase to start from
        
        Returns:
            Workflow results
        """
        if start_phase not in self.phases:
            raise ValueError(f"Unknown phase: {start_phase}")
        
        # Find starting index
        start_index = self.phases.index(start_phase)
        
        print(f"\n→ Starting workflow from {start_phase}")
        
        # Run from start phase to end
        for phase_name in self.phases[start_index:]:
            success = self.run_phase(phase_name)
            if not success:
                self.state_manager.mark_workflow_failed(f"Failed at {phase_name}")
                break
        
        return self.state_manager.get_final_results()
    
    def _get_phase_title(self, phase_name: str) -> str:
        """Get readable phase title"""
        titles = {
            "phase1_tuning": "Keyword Tuning",
            "phase2_market": "Market Analysis",
            "phase3_gsc": "GSC Reality Check",
            "phase4_gap_analysis": "Gap Analysis",
            "phase5_competitors": "Competitor Intelligence"
        }
        return titles.get(phase_name, phase_name)
    
    def generate_report(self, results: Dict[str, Any]):
        """
        Generate final report
        
        Args:
            results: Workflow results
        """
        from pathlib import Path
        import json
        
        # Save report
        report_dir = Path(f"storage/processed_data/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"workflow_report_{self.user_id}_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"→ Report saved: {report_file}")
        
        # Print summary
        self.print_summary(results)
    
    def print_summary(self, results: Dict[str, Any]):
        """Print workflow summary"""
        print("\nWorkflow Summary:")
        print("-" * 60)
        
        summary = results.get("summary", {})
        phase_outputs = results.get("phase_outputs", {})
        
        print(f"Status: {summary.get('status', 'unknown').upper()}")
        print(f"Progress: {summary.get('progress_percentage', 0):.0f}%")
        print(f"Completed Phases: {len(summary.get('completed_phases', []))}/5")
        
        # Phase 1 summary
        if "phase1_tuning" in phase_outputs:
            p1 = phase_outputs["phase1_tuning"]["data"]
            print(f"\n✓ Phase 1: {len(p1.get('final_keywords', []))} final keywords")
        
        # Phase 2 summary
        if "phase2_market" in phase_outputs:
            p2 = phase_outputs["phase2_market"]["data"]
            print(f"✓ Phase 2: Avg volume {p2.get('avg_search_volume', 0):.0f}/month")
        
        # Phase 3 summary
        if "phase3_gsc" in phase_outputs:
            p3 = phase_outputs["phase3_gsc"]["data"]
            print(f"✓ Phase 3: {p3.get('keywords_with_rankings', 0)} keywords ranked")
        
        # Phase 4 summary
        if "phase4_gap_analysis" in phase_outputs:
            p4 = phase_outputs["phase4_gap_analysis"]["data"]
            print(f"✓ Phase 4: {len(p4.get('untapped_gold', []))} untapped gold opportunities")
        
        # Phase 5 summary
        if "phase5_competitors" in phase_outputs:
            p5 = phase_outputs["phase5_competitors"]["data"]
            print(f"✓ Phase 5: {p5.get('keywords_analyzed', 0)} competitor analyses")
        
        print("\n" + "="*60)


def run_workflow(user_id: str) -> Dict[str, Any]:
    """
    Run complete workflow for a user
    
    Args:
        user_id: User ID
    
    Returns:
        Workflow results
    """
    orchestrator = WorkflowOrchestrator(user_id)
    return orchestrator.run_complete_workflow()


def run_single_phase(user_id: str, phase_name: str) -> bool:
    """
    Run a single phase
    
    Args:
        user_id: User ID
        phase_name: Phase to run
    
    Returns:
        Success status
    """
    orchestrator = WorkflowOrchestrator(user_id)
    return orchestrator.run_phase(phase_name)


def resume_workflow(user_id: str) -> Dict[str, Any]:
    """
    Resume workflow from last completed phase
    
    Args:
        user_id: User ID
    
    Returns:
        Workflow results
    """
    orchestrator = WorkflowOrchestrator(user_id)
    
    # Get last completed phase
    summary = orchestrator.state_manager.get_workflow_summary()
    completed_phases = summary.get("completed_phases", [])
    
    if not completed_phases:
        # No phases completed, start from beginning
        return orchestrator.run_complete_workflow()
    
    # Find next phase
    last_phase = completed_phases[-1]
    last_phase_index = orchestrator.phases.index(last_phase)
    
    if last_phase_index + 1 < len(orchestrator.phases):
        next_phase = orchestrator.phases[last_phase_index + 1]
        print(f"→ Resuming from {next_phase}")
        return orchestrator.run_phases_from(next_phase)
    else:
        print("→ Workflow already complete")
        return orchestrator.state_manager.get_final_results()


# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python workflow.py <user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    
    print(f"Running workflow for user: {user_id}")
    results = run_workflow(user_id)
    
    print("\nFinal Results:")
    print(results)  