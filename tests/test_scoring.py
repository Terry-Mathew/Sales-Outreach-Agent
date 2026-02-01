"""
Tests for the rule-based scoring module.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scoring.rule_scorer import RuleBasedScorer


class TestRuleBasedScorer:
    """Test suite for RuleBasedScorer."""
    
    @pytest.fixture
    def scorer(self):
        """Create a scorer instance."""
        return RuleBasedScorer()
    
    def test_good_email_scores_high(self, scorer, sample_good_email):
        """Good emails should score above 60."""
        result = scorer.score(
            sample_good_email["subject"],
            sample_good_email["body"]
        )
        
        assert result["score"] >= 60
        assert "breakdown" in result
        assert "flags" in result
    
    def test_poor_email_scores_low(self, scorer, sample_poor_email):
        """Poor emails should score below 50."""
        result = scorer.score(
            sample_poor_email["subject"],
            sample_poor_email["body"]
        )
        
        assert result["score"] <= 50
        assert len(result["flags"]) > 0  # Should have flagged issues
    
    def test_bad_opener_detected(self, scorer):
        """Cliché openers should be flagged."""
        subject = "Quick question"
        body = "I hope this email finds you well! I wanted to reach out about our services."
        
        result = scorer.score(subject, body)
        
        # Should have poor opening score
        assert result["breakdown"]["opening_quality"] < 10
    
    def test_good_opener_rewarded(self, scorer):
        """Personal openers should score well."""
        subject = "Congrats on the award"
        body = """Hi Marcus,

Noticed your company just launched a new product line—impressive growth! We help companies like yours automate operations.

Worth a quick call?

Best,
Sarah"""
        
        result = scorer.score(subject, body)
        
        assert result["breakdown"]["opening_quality"] >= 10
    
    def test_length_scoring(self, scorer):
        """Length should be scored appropriately."""
        # Too short
        short_result = scorer.score("Hi", "Short message here.")
        assert short_result["breakdown"]["length"] < 10
        
        # Good length (around 100 words)
        good_body = " ".join(["word"] * 100)
        good_result = scorer.score("Subject", good_body)
        assert good_result["breakdown"]["length"] >= 10
    
    def test_spam_triggers_penalized(self, scorer):
        """Spam trigger words should result in penalties."""
        subject = "ACT NOW - Limited time offer!"
        body = "This is an urgent message. Act now to get our free guide! Limited time offer!"
        
        result = scorer.score(subject, body)
        
        assert result["breakdown"]["spam_penalty"] < 0
        assert any("spam" in flag.lower() for flag in result["flags"])
    
    def test_cta_detection(self, scorer):
        """CTAs should be detected and rewarded."""
        body_with_cta = """Hi there,

We help agencies automate their work.

Would you be free for a 15-minute call next week?

Best,
John"""
        
        body_without_cta = """Hi there,

We help agencies automate their work. Our platform is great.

Best,
John"""
        
        with_cta = scorer.score("Subject", body_with_cta)
        without_cta = scorer.score("Subject", body_without_cta)
        
        assert with_cta["breakdown"]["cta_quality"] > without_cta["breakdown"]["cta_quality"]
    
    def test_value_keywords_rewarded(self, scorer):
        """Value-oriented keywords should be rewarded."""
        body_with_value = """We help companies reduce costs, improve efficiency, and automate manual work."""
        body_generic = """We are a company that does things for other companies."""
        
        with_value = scorer.score("Subject", body_with_value)
        generic = scorer.score("Subject", body_generic)
        
        assert with_value["breakdown"]["value_proposition"] > generic["breakdown"]["value_proposition"]
    
    def test_score_capped_at_100(self, scorer):
        """Score should never exceed 100."""
        # Create an artificially good email
        subject = "Quick thought"
        body = """Hi Marcus,

Congratulations on your recent award! Your team has done amazing work.

We help agencies like yours reduce manual work by 40%, improve efficiency, and automate reporting. Companies like Directive and WebMechanix save 15 hours per week.

Worth a 15-minute call to discuss?

Best,
Sarah"""
        
        result = scorer.score(subject, body)
        
        assert result["score"] <= 100
    
    def test_score_never_negative(self, scorer):
        """Score should never go below 0."""
        # Create a terrible email with lots of spam triggers
        subject = "FREE!!! ACT NOW!!! URGENT!!!"
        body = "FREE FREE FREE! ACT NOW! LIMITED TIME! URGENT! Click here! Buy now!"
        
        result = scorer.score(subject, body)
        
        assert result["score"] >= 0


class TestScorerFlags:
    """Test that flags are correctly generated."""
    
    @pytest.fixture
    def scorer(self):
        return RuleBasedScorer()
    
    def test_too_long_flagged(self, scorer):
        """Emails that are too long should be flagged."""
        body = " ".join(["word"] * 250)  # 250 words
        
        result = scorer.score("Subject", body)
        
        assert any("too long" in flag.lower() for flag in result["flags"])
    
    def test_too_short_flagged(self, scorer):
        """Emails that are too short should be flagged."""
        result = scorer.score("Subject", "Very short.")
        
        assert any("too short" in flag.lower() for flag in result["flags"])
