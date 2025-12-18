from phases.phase0_keyword_generation import generate_keywords_for_user

def generate_keywords(profile: dict, count: int = 30) -> list:
    return generate_keywords_for_user(profile, count)
