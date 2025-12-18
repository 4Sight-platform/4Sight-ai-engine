"""
CLI Main Entry Point
Handles terminal-based interaction
"""

from cli.onboarding.orchestrator import OnboardingOrchestrator

def run_cli():
    """Run CLI mode"""
    print("\n" + "="*60)
    print("  SEO Automation Platform - CLI Mode")
    print("="*60 + "\n")
    
    # Check if user has completed onboarding
    # TODO: Load user profile
    
    print("Options:")
    print("  1) Complete onboarding (first time)")
    print("  2) Run complete workflow (all 5 phases)")
    print("  3) Run individual phase")
    print("  4) View saved reports")
    print("  5) Settings")
    print("  6) Exit")
    
    choice = input("\n→ Select option (1-6): ").strip()
    
    if choice == "1":
        orchestrator = OnboardingOrchestrator()
        orchestrator.run()
    elif choice == "2":
        print("\n✓ Running complete workflow...")
        # TODO: Call orchestration.workflow.run()
    else:
        print("\n✓ Exiting...")


if __name__ == "__main__":
    run_cli()
