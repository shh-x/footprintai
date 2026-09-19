import pytest
from resolver import resolve, combine, decide


def test_correct_account_not_rejected():
    """Test that a correct account with matching bio and links is not rejected."""
    target = {
        "name": "Aarav Mehta",
        "context": "ML engineer in Hyderabad, works on NLP",
        "image": "test_images/aarav.jpg"
    }
    
    # Include multiple candidates with cross-links to enable graph scoring
    candidates = [
        {
            "platform": "github",
            "username": "aarav-ml",
            "display_name": "Aarav Mehta",
            "profile_url": "https://github.com/aarav-ml",
            "bio": "NLP engineer. Open-source contributor. Building ML tools for Indian languages.",
            "photo_url": "test_images/aarav_gh.jpg",
            "links": ["https://aaravmehta.dev", "https://linkedin.com/in/aarav-mehta"],
            "location": "Hyderabad",
            "extra": {},
            "retrieved_at": "2026-01-15T10:32:00Z"
        },
        {
            "platform": "linkedin",
            "username": "aarav-mehta",
            "display_name": "Aarav Mehta",
            "profile_url": "https://linkedin.com/in/aarav-mehta",
            "bio": "Machine Learning Engineer at TechCorp Hyderabad | NLP Researcher | Open Source",
            "photo_url": "test_images/aarav_li.jpg",
            "links": ["https://github.com/aarav-ml", "https://aaravmehta.dev"],
            "location": "Hyderabad, India",
            "extra": {},
            "retrieved_at": "2026-01-15T10:32:00Z"
        }
    ]
    
    results = resolve(target, candidates)
    assert len(results) == 2
    # The correct accounts should not be rejected (they have matching bio and cross-links)
    correct_accounts = [r for r in results if r["decision"] != "rejected"]
    assert len(correct_accounts) >= 1
    # At least one correct account should have confidence >= 0.5
    assert any(r["confidence"] >= 0.5 for r in correct_accounts)


def test_same_name_chef_rejected():
    """Test that a same-name different profession (chef vs engineer) is rejected."""
    target = {
        "name": "Aarav Mehta",
        "context": "ML engineer in Hyderabad, works on NLP",
        "image": "test_images/aarav.jpg"
    }
    
    candidates = [
        {
            "platform": "github",
            "username": "aarav123",
            "display_name": "Aarav Mehta",
            "profile_url": "https://github.com/aarav123",
            "bio": "Chef and food photographer. Love cooking Indian cuisine.",
            "photo_url": "test_images/other1.jpg",
            "links": ["https://foodblog.com"],
            "location": "Delhi",
            "extra": {},
            "retrieved_at": "2026-01-15T10:32:00Z"
        }
    ]
    
    results = resolve(target, candidates)
    assert len(results) == 1
    assert results[0]["decision"] == "rejected"
    assert results[0]["confidence"] < 0.5


def test_0_74_cap_when_signal_missing():
    """Test that confidence is capped at 0.74 when a signal is missing."""
    # Test with only bio and graph (no face)
    conf = combine(None, 0.8, 0.9)
    assert conf <= 0.74
    
    # Test with only face and bio (no graph)
    conf = combine(0.9, 0.8, None)
    assert conf <= 0.74
    
    # Test with only face and graph (no bio)
    conf = combine(0.9, None, 0.8)
    assert conf <= 0.74
    
    # Test with all three signals - should be able to exceed 0.74
    conf = combine(0.9, 0.8, 0.9)
    assert conf > 0.74


def test_decide_thresholds():
    """Test that decide() returns correct statuses based on confidence."""
    assert decide(0.80) == "verified"
    assert decide(0.75) == "verified"
    assert decide(0.74) == "needs_review"
    assert decide(0.60) == "needs_review"
    assert decide(0.50) == "needs_review"
    assert decide(0.49) == "rejected"
    assert decide(0.30) == "rejected"


def test_graph_score_two_way_links():
    """Test that two-way links give score 1.0."""
    from resolver import graph_score
    
    candidate = {
        "profile_url": "https://github.com/aarav-ml",
        "username": "aarav-ml",
        "links": ["https://linkedin.com/in/aarav-mehta"]
    }
    
    other = {
        "profile_url": "https://linkedin.com/in/aarav-mehta",
        "username": "aarav-mehta",
        "links": ["https://github.com/aarav-ml"]
    }
    
    score = graph_score(candidate, [candidate, other])
    assert score == 1.0


def test_graph_score_one_way_links():
    """Test that one-way links give score 0.5."""
    from resolver import graph_score
    
    candidate = {
        "profile_url": "https://github.com/aarav-ml",
        "username": "aarav-ml",
        "links": ["https://linkedin.com/in/aarav-mehta"]
    }
    
    other = {
        "profile_url": "https://linkedin.com/in/aarav-mehta",
        "username": "aarav-mehta",
        "links": []
    }
    
    score = graph_score(candidate, [candidate, other])
    assert score == 0.5


def test_graph_score_no_links():
    """Test that no links give score 0.0."""
    from resolver import graph_score
    
    candidate = {
        "profile_url": "https://github.com/aarav-ml",
        "username": "aarav-ml",
        "links": []
    }
    
    other = {
        "profile_url": "https://linkedin.com/in/aarav-mehta",
        "username": "aarav-mehta",
        "links": []
    }
    
    score = graph_score(candidate, [candidate, other])
    assert score == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
