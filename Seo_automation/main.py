#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from cli.onboarding.orchestrator import run_onboarding
from orchestration.workflow import run_workflow

if __name__ == "__main__":
    print("SEO Automation Platform - Starting...")
    user_id = run_onboarding()
    print(f"\n{'='*60}\nOnboarding complete! Starting workflow...\n{'='*60}\n")
    results = run_workflow(user_id)
    print("\n✓ All done!")