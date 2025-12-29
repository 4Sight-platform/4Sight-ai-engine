"""
Keyword Analyzer
Analyzes, scores, and ranks generated keywords
"""

import re
from typing import List, Dict, Any, Tuple
from collections import Counter


class KeywordAnalyzer:
    """
    Analyze and rank keyword suggestions
    """
    
    def __init__(self):
        # Common stopwords to filter out
        self.stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with'
        }
    
    def analyze_keywords(self, keywords: List[str], profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive keyword analysis
        
        Args:
            keywords: List of keywords
            profile: User profile for context
        
        Returns:
            Analysis results dictionary
        """
        analysis = {
            "total_keywords": len(keywords),
            "unique_keywords": len(set(keywords)),
            "duplicates": self._find_duplicates(keywords),
            "length_distribution": self._analyze_length_distribution(keywords),
            "word_frequency": self._analyze_word_frequency(keywords),
            "intent_distribution": self._estimate_intent_distribution(keywords),
            "location_keywords": self._find_location_keywords(keywords, profile),
            "brand_keywords": self._find_brand_keywords(keywords, profile),
            "question_keywords": self._find_question_keywords(keywords),
            "commercial_keywords": self._find_commercial_keywords(keywords),
            "quality_score": self._calculate_quality_score(keywords, profile)
        }
        
        return analysis
    
    def rank_keywords(self, keywords: List[str], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank keywords by relevance and potential
        
        Args:
            keywords: List of keywords
            profile: User profile
        
        Returns:
            List of keyword dictionaries with scores
        """
        ranked = []
        
        for keyword in keywords:
            score = self._score_keyword(keyword, profile)
            
            ranked.append({
                "keyword": keyword,
                "score": score["total"],
                "relevance_score": score["relevance"],
                "specificity_score": score["specificity"],
                "intent_score": score["intent"],
                "estimated_difficulty": self._estimate_difficulty(keyword),
                "type": self._classify_keyword_type(keyword),
                "word_count": len(keyword.split())
            })
        
        # Sort by score descending
        ranked.sort(key=lambda x: x["score"], reverse=True)
        
        return ranked
    
    def categorize_keywords(self, keywords: List[str], profile: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Categorize keywords into different types
        
        Args:
            keywords: List of keywords
            profile: User profile
        
        Returns:
            Dictionary of categorized keywords
        """
        categories = {
            "head_terms": [],           # 1-2 words, broad
            "mid_tail": [],             # 2-3 words, moderate
            "long_tail": [],            # 4+ words, specific
            "branded": [],              # Contains brand name
            "location": [],             # Contains location
            "questions": [],            # Question format
            "commercial": [],           # Buying intent
            "informational": [],        # Learning intent
            "navigational": []          # Finding specific site/page
        }
        
        business_name = profile.get('business_name', '').lower()
        locations = [loc.lower() for loc in profile.get('selected_locations', [])]
        
        for keyword in keywords:
            kw_lower = keyword.lower()
            word_count = len(keyword.split())
            
            # Length-based categories
            if word_count <= 2:
                categories["head_terms"].append(keyword)
            elif word_count == 3:
                categories["mid_tail"].append(keyword)
            else:
                categories["long_tail"].append(keyword)
            
            # Branded
            if business_name in kw_lower:
                categories["branded"].append(keyword)
            
            # Location
            if any(loc in kw_lower for loc in locations) or 'near me' in kw_lower:
                categories["location"].append(keyword)
            
            # Questions
            if any(kw_lower.startswith(q) for q in ['how', 'what', 'where', 'when', 'why', 'who']):
                categories["questions"].append(keyword)
            
            # Commercial
            if any(word in kw_lower for word in ['buy', 'purchase', 'price', 'cost', 'cheap', 'discount', 'deal']):
                categories["commercial"].append(keyword)
            
            # Informational
            elif any(word in kw_lower for word in ['how to', 'what is', 'guide', 'tips', 'learn', 'tutorial']):
                categories["informational"].append(keyword)
            
            # Navigational
            elif any(word in kw_lower for word in ['website', 'login', 'sign in', 'official']):
                categories["navigational"].append(keyword)
        
        return categories
    
    def suggest_improvements(self, keywords: List[str], profile: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Suggest improvements to keyword list
        
        Args:
            keywords: Current keywords
            profile: User profile
        
        Returns:
            Dictionary with improvement suggestions
        """
        suggestions = {
            "remove": [],
            "add_location": [],
            "add_intent": [],
            "expand": []
        }
        
        # Analyze current set
        categories = self.categorize_keywords(keywords, profile)
        
        # Suggest removals (too generic)
        generic_keywords = ['business', 'company', 'service', 'product', 'online']
        for keyword in keywords:
            if keyword.lower() in generic_keywords:
                suggestions["remove"].append(f"{keyword} (too generic)")
        
        # Suggest adding location if missing
        if len(categories["location"]) < len(keywords) * 0.2:
            suggestions["add_location"].append("Add more location-based keywords")
        
        # Suggest adding commercial intent if missing
        if len(categories["commercial"]) < len(keywords) * 0.3:
            suggestions["add_intent"].append("Add more commercial intent keywords (buy, price, etc.)")
        
        # Suggest expansion opportunities
        if len(categories["long_tail"]) < len(keywords) * 0.3:
            suggestions["expand"].append("Add more long-tail specific keywords")
        
        if len(categories["questions"]) < 3:
            suggestions["expand"].append("Add question-based keywords")
        
        return suggestions
    
    def _score_keyword(self, keyword: str, profile: Dict[str, Any]) -> Dict[str, float]:
        """Calculate relevance score for a keyword"""
        scores = {
            "relevance": 0.0,
            "specificity": 0.0,
            "intent": 0.0,
            "total": 0.0
        }
        
        # Relevance score (0-10)
        business_terms = self._extract_business_terms(profile)
        keyword_words = set(keyword.lower().split())
        
        matches = keyword_words.intersection(business_terms)
        scores["relevance"] = min(len(matches) * 3, 10)
        
        # Specificity score (0-10)
        word_count = len(keyword.split())
        if word_count >= 4:
            scores["specificity"] = 10
        elif word_count == 3:
            scores["specificity"] = 7
        elif word_count == 2:
            scores["specificity"] = 5
        else:
            scores["specificity"] = 3
        
        # Intent score (0-10)
        intent_words = ['buy', 'purchase', 'find', 'hire', 'get', 'order', 'book']
        if any(word in keyword.lower() for word in intent_words):
            scores["intent"] = 10
        elif any(keyword.lower().startswith(q) for q in ['how', 'what', 'where']):
            scores["intent"] = 7
        else:
            scores["intent"] = 5
        
        # Total score
        scores["total"] = (
            scores["relevance"] * 0.4 +
            scores["specificity"] * 0.3 +
            scores["intent"] * 0.3
        )
        
        return scores
    
    def _extract_business_terms(self, profile: Dict[str, Any]) -> set:
        """Extract relevant terms from business profile"""
        terms = set()
        
        # From description
        description = profile.get('business_description', '')
        words = re.findall(r'\b\w+\b', description.lower())
        terms.update(w for w in words if w not in self.stopwords and len(w) > 3)
        
        # From products/services
        for item in profile.get('products', []) + profile.get('services', []):
            text = item
            if isinstance(item, dict):
                text = item.get('name', '') or item.get('product_name', '') or item.get('service_name', '')
            
            if isinstance(text, str):
                words = re.findall(r'\b\w+\b', text.lower())
                terms.update(w for w in words if w not in self.stopwords)
        
        return terms
    
    def _find_duplicates(self, keywords: List[str]) -> List[str]:
        """Find duplicate keywords"""
        counts = Counter(keywords)
        return [kw for kw, count in counts.items() if count > 1]
    
    def _analyze_length_distribution(self, keywords: List[str]) -> Dict[str, int]:
        """Analyze distribution of keyword lengths"""
        distribution = {
            "1_word": 0,
            "2_words": 0,
            "3_words": 0,
            "4+_words": 0
        }
        
        for keyword in keywords:
            word_count = len(keyword.split())
            if word_count == 1:
                distribution["1_word"] += 1
            elif word_count == 2:
                distribution["2_words"] += 1
            elif word_count == 3:
                distribution["3_words"] += 1
            else:
                distribution["4+_words"] += 1
        
        return distribution
    
    def _analyze_word_frequency(self, keywords: List[str]) -> Dict[str, int]:
        """Analyze most common words in keywords"""
        all_words = []
        
        for keyword in keywords:
            words = keyword.lower().split()
            all_words.extend(w for w in words if w not in self.stopwords)
        
        word_counts = Counter(all_words)
        return dict(word_counts.most_common(10))
    
    def _estimate_intent_distribution(self, keywords: List[str]) -> Dict[str, int]:
        """Estimate distribution of search intent"""
        distribution = {
            "informational": 0,
            "commercial": 0,
            "transactional": 0,
            "navigational": 0
        }
        
        for keyword in keywords:
            kw_lower = keyword.lower()
            
            if any(word in kw_lower for word in ['buy', 'purchase', 'order', 'book']):
                distribution["transactional"] += 1
            elif any(word in kw_lower for word in ['price', 'cost', 'compare', 'review', 'best']):
                distribution["commercial"] += 1
            elif any(word in kw_lower for word in ['website', 'login', 'official']):
                distribution["navigational"] += 1
            else:
                distribution["informational"] += 1
        
        return distribution
    
    def _find_location_keywords(self, keywords: List[str], profile: Dict[str, Any]) -> List[str]:
        """Find keywords with location modifiers"""
        locations = [loc.lower() for loc in profile.get('selected_locations', [])]
        location_keywords = []
        
        for keyword in keywords:
            kw_lower = keyword.lower()
            if any(loc in kw_lower for loc in locations) or 'near me' in kw_lower:
                location_keywords.append(keyword)
        
        return location_keywords
    
    def _find_brand_keywords(self, keywords: List[str], profile: Dict[str, Any]) -> List[str]:
        """Find keywords containing brand name"""
        business_name = profile.get('business_name', '').lower()
        return [kw for kw in keywords if business_name in kw.lower()]
    
    def _find_question_keywords(self, keywords: List[str]) -> List[str]:
        """Find question-based keywords"""
        question_words = ['how', 'what', 'where', 'when', 'why', 'who', 'which']
        return [kw for kw in keywords if any(kw.lower().startswith(q) for q in question_words)]
    
    def _find_commercial_keywords(self, keywords: List[str]) -> List[str]:
        """Find keywords with commercial intent"""
        commercial_words = ['buy', 'purchase', 'price', 'cost', 'cheap', 'discount', 'deal', 'order']
        return [kw for kw in keywords if any(word in kw.lower() for word in commercial_words)]
    
    def _calculate_quality_score(self, keywords: List[str], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall quality score for keyword set"""
        categories = self.categorize_keywords(keywords, profile)
        
        # Calculate diversity score
        diversity_score = (
            (len(categories["head_terms"]) > 0) * 2 +
            (len(categories["mid_tail"]) > 0) * 2 +
            (len(categories["long_tail"]) > 0) * 2 +
            (len(categories["location"]) > 0) * 2 +
            (len(categories["questions"]) > 0) * 2
        )
        
        # Calculate intent balance score
        intent_balance = (
            (len(categories["commercial"]) > 0) * 3 +
            (len(categories["informational"]) > 0) * 3 +
            (len(categories["navigational"]) > 0) * 2
        )
        
        total_score = (diversity_score + intent_balance) / 2
        
        return {
            "total_score": round(total_score, 1),
            "max_score": 10.0,
            "diversity_score": round(diversity_score, 1),
            "intent_balance_score": round(intent_balance, 1),
            "grade": self._score_to_grade(total_score)
        }
    
    def _estimate_difficulty(self, keyword: str) -> str:
        """Estimate ranking difficulty"""
        word_count = len(keyword.split())
        
        if word_count >= 4:
            return "EASY"
        elif word_count == 3:
            return "MEDIUM"
        elif word_count == 2:
            return "MEDIUM" if len(keyword) > 15 else "HARD"
        else:
            return "VERY_HARD"
    
    def _classify_keyword_type(self, keyword: str) -> str:
        """Classify keyword type"""
        kw_lower = keyword.lower()
        
        if any(word in kw_lower for word in ['buy', 'purchase', 'order']):
            return "transactional"
        elif any(word in kw_lower for word in ['price', 'cost', 'compare', 'best']):
            return "commercial"
        elif any(kw_lower.startswith(q) for q in ['how', 'what', 'where']):
            return "informational"
        else:
            return "navigational"
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 9:
            return "A"
        elif score >= 8:
            return "B"
        elif score >= 7:
            return "C"
        elif score >= 6:
            return "D"
        else:
            return "F"


# Convenience functions
def analyze_keywords(keywords: List[str], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze keyword list"""
    analyzer = KeywordAnalyzer()
    return analyzer.analyze_keywords(keywords, profile)


def rank_keywords(keywords: List[str], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Rank keywords by quality"""
    analyzer = KeywordAnalyzer()
    return analyzer.rank_keywords(keywords, profile)


def categorize_keywords(keywords: List[str], profile: Dict[str, Any]) -> Dict[str, List[str]]:
    """Categorize keywords"""
    analyzer = KeywordAnalyzer()
    return analyzer.categorize_keywords(keywords, profile)


# For testing
if __name__ == "__main__":
    # Test analyzer
    test_keywords = [
        "artisan bakery seattle",
        "gluten free cakes",
        "buy wedding cake online",
        "how to order custom cakes",
        "best bakery near me",
        "vegan pastries seattle",
        "cake delivery downtown",
        "organic bakery",
        "custom cake design",
        "seattle cake shop"
    ]
    
    test_profile = {
        "business_name": "Artisan Bakery Co.",
        "business_description": "Local artisan bakery specializing in gluten-free cakes",
        "selected_locations": ["Seattle, WA"],
        "products": ["Cakes", "Pastries"],
        "services": ["Delivery", "Custom design"]
    }
    
    print("Testing Keyword Analyzer")
    print("="*60)
    
    analyzer = KeywordAnalyzer()
    
    # Test analysis
    analysis = analyzer.analyze_keywords(test_keywords, test_profile)
    
    print("\nAnalysis Results:")
    print(f"Total keywords: {analysis['total_keywords']}")
    print(f"Quality score: {analysis['quality_score']['total_score']}/10 ({analysis['quality_score']['grade']})")
    print(f"\nLength distribution: {analysis['length_distribution']}")
    print(f"Intent distribution: {analysis['intent_distribution']}")
    print(f"Location keywords: {len(analysis['location_keywords'])}")
    print(f"Commercial keywords: {len(analysis['commercial_keywords'])}")
    
    # Test ranking
    print(f"\n{'='*60}")
    print("Top 5 Keywords by Score:")
    print("="*60)
    
    ranked = analyzer.rank_keywords(test_keywords, test_profile)
    
    for i, kw in enumerate(ranked[:5], 1):
        print(f"{i}. {kw['keyword']}")
        print(f"   Score: {kw['score']:.1f} | Difficulty: {kw['estimated_difficulty']} | Type: {kw['type']}")
    
    # Test categorization
    print(f"\n{'='*60}")
    print("Keyword Categories:")
    print("="*60)
    
    categories = analyzer.categorize_keywords(test_keywords, test_profile)
    
    for category, keywords in categories.items():
        if keywords:
            print(f"\n{category.upper()}: {len(keywords)}")
            for kw in keywords[:3]:
                print(f"  - {kw}")