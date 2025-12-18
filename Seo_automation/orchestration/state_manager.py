"""
Workflow State Manager
Tracks state and data flow between phases
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json


class WorkflowState:
    """
    Manages state throughout the SEO automation workflow
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.state = {
            "user_id": user_id,
            "workflow_started_at": datetime.now().isoformat(),
            "current_phase": None,
            "completed_phases": [],
            "phase_outputs": {}
        }
    
    def set_phase(self, phase_name: str):
        """Set current phase"""
        self.state["current_phase"] = phase_name
        self.state[f"{phase_name}_started_at"] = datetime.now().isoformat()
    
    def complete_phase(self, phase_name: str, output: Dict[str, Any]):
        """Mark phase as complete and store output"""
        self.state["completed_phases"].append(phase_name)
        self.state["phase_outputs"][phase_name] = output
        self.state[f"{phase_name}_completed_at"] = datetime.now().isoformat()
        self.state["current_phase"] = None
    
    def get_phase_output(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """Get output from a completed phase"""
        return self.state["phase_outputs"].get(phase_name)
    
    def is_phase_completed(self, phase_name: str) -> bool:
        """Check if phase is completed"""
        return phase_name in self.state["completed_phases"]
    
    def get_state(self) -> Dict[str, Any]:
        """Get complete state"""
        return self.state
    
    def update_state(self, updates: Dict[str, Any]):
        """Update state with new data"""
        self.state.update(updates)
    
    def save_state(self, filepath: Optional[Path] = None):
        """Save state to file"""
        if filepath is None:
            filepath = Path(f"storage/sessions/workflow_{self.user_id}.json")
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    @classmethod
    def load_state(cls, user_id: str, filepath: Optional[Path] = None) -> 'WorkflowState':
        """Load state from file"""
        if filepath is None:
            filepath = Path(f"storage/sessions/workflow_{user_id}.json")
        
        instance = cls(user_id)
        
        if filepath.exists():
            with open(filepath, 'r') as f:
                instance.state = json.load(f)
        
        return instance


class PhaseInput:
    """
    Structured input for a phase
    """
    
    def __init__(self, user_id: str, keywords: List[str], profile: Dict[str, Any]):
        self.user_id = user_id
        self.keywords = keywords
        self.profile = profile
        self.previous_outputs = {}
    
    def add_previous_output(self, phase_name: str, output: Dict[str, Any]):
        """Add output from previous phase"""
        self.previous_outputs[phase_name] = output
    
    def get_previous_output(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """Get output from previous phase"""
        return self.previous_outputs.get(phase_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "keywords": self.keywords,
            "profile": self.profile,
            "previous_outputs": self.previous_outputs
        }


class PhaseOutput:
    """
    Structured output from a phase
    """
    
    def __init__(self, phase_name: str, success: bool, data: Dict[str, Any], 
                 error: Optional[str] = None):
        self.phase_name = phase_name
        self.success = success
        self.data = data
        self.error = error
        self.completed_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "phase_name": self.phase_name,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "completed_at": self.completed_at
        }


class WorkflowStateManager:
    """
    High-level workflow state manager
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.state = WorkflowState(user_id)
        self.phases = [
            "phase1_tuning",
            "phase2_market",
            "phase3_gsc",
            "phase4_gap_analysis",
            "phase5_competitors"
        ]
    
    def start_workflow(self, keywords: List[str], profile: Dict[str, Any]):
        """Initialize workflow"""
        self.state.update_state({
            "initial_keywords": keywords,
            "profile": profile,
            "workflow_status": "running"
        })
        self.state.save_state()
    
    def create_phase_input(self, phase_name: str) -> PhaseInput:
        """Create input for a phase"""
        profile = self.state.get_state().get("profile", {})
        
        # Get keywords from previous phase or initial
        if phase_name == "phase1_tuning":
            keywords = self.state.get_state().get("initial_keywords", [])
        else:
            # Get keywords from Phase 1 output if available
            phase1_output = self.state.get_phase_output("phase1_tuning")
            if phase1_output and "final_keywords" in phase1_output:
                keywords = phase1_output["final_keywords"]
            else:
                keywords = self.state.get_state().get("initial_keywords", [])
        
        phase_input = PhaseInput(self.user_id, keywords, profile)
        
        # Add all previous phase outputs
        for prev_phase in self.phases:
            if prev_phase == phase_name:
                break
            
            if self.state.is_phase_completed(prev_phase):
                output = self.state.get_phase_output(prev_phase)
                if output:
                    phase_input.add_previous_output(prev_phase, output)
        
        return phase_input
    
    def complete_phase(self, phase_output: PhaseOutput):
        """Mark phase as complete"""
        self.state.complete_phase(phase_output.phase_name, phase_output.to_dict())
        self.state.save_state()
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of workflow execution"""
        state = self.state.get_state()
        
        return {
            "user_id": self.user_id,
            "started_at": state.get("workflow_started_at"),
            "status": state.get("workflow_status", "unknown"),
            "completed_phases": state.get("completed_phases", []),
            "current_phase": state.get("current_phase"),
            "total_phases": len(self.phases),
            "progress_percentage": (len(state.get("completed_phases", [])) / len(self.phases)) * 100
        }
    
    def mark_workflow_complete(self):
        """Mark entire workflow as complete"""
        self.state.update_state({
            "workflow_status": "completed",
            "workflow_completed_at": datetime.now().isoformat()
        })
        self.state.save_state()
    
    def mark_workflow_failed(self, error: str):
        """Mark workflow as failed"""
        self.state.update_state({
            "workflow_status": "failed",
            "workflow_failed_at": datetime.now().isoformat(),
            "error": error
        })
        self.state.save_state()
    
    def get_final_results(self) -> Dict[str, Any]:
        """Get final workflow results"""
        return {
            "user_id": self.user_id,
            "summary": self.get_workflow_summary(),
            "phase_outputs": self.state.get_state().get("phase_outputs", {})
        }


# Singleton instance per user
_state_managers = {}

def get_state_manager(user_id: str) -> WorkflowStateManager:
    """Get or create state manager for user"""
    if user_id not in _state_managers:
        _state_managers[user_id] = WorkflowStateManager(user_id)
    return _state_managers[user_id]