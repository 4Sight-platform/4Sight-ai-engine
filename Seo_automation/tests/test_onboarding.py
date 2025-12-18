from cli.onboarding.orchestrator import run_onboarding

def test_onboarding():
    user_id = run_onboarding()
    assert user_id is not None
    print(f"✓ Onboarding test passed: {user_id}")
