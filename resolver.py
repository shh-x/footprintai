from typing import Callable, Dict, List, Optional, Any
from bio_matcher import bio_similarity, name_similarity

WEIGHTS = {"face": 0.40, "bio": 0.35, "graph": 0.25}


def graph_score(candidate: Dict[str, Any], all_candidates: List[Dict[str, Any]]) -> float:
    """1.0 if two-way links, 0.5 if one-way, 0 if none.
    
    Args:
        candidate: The candidate to score
        all_candidates: List of all candidates to check for links
    
    Returns:
        Graph score between 0.0 and 1.0
    """
    score = 0.0
    for other in all_candidates:
        if other is candidate:
            continue
        a_to_b = any(other["profile_url"] in l or other["username"] in l
                     for l in candidate["links"])
        b_to_a = any(candidate["profile_url"] in l or candidate["username"] in l
                     for l in other["links"])
        if a_to_b and b_to_a:
            score = max(score, 1.0)
        elif a_to_b or b_to_a:
            score = max(score, 0.5)
    return score


def combine(s_face: Optional[float], s_bio: Optional[float], s_graph: Optional[float]) -> float:
    """Combine signals into a confidence score.
    
    Args:
        s_face: Face similarity score (0-1) or None if unavailable
        s_bio: Bio similarity score (0-1) or None if unavailable
        s_graph: Graph score (0-1) or None if unavailable
    
    Returns:
        Confidence score between 0.0 and 1.0, capped at 0.74 if evidence is incomplete
    """
    signals = {"face": s_face, "bio": s_bio, "graph": s_graph}
    available = {k: v for k, v in signals.items() if v is not None}
    total_w = sum(WEIGHTS[k] for k in available)
    conf = sum(WEIGHTS[k] * v for k, v in available.items()) / total_w
    # Safeguard: missing evidence -> can never be auto-verified
    if len(available) < 3:
        conf = min(conf, 0.74)
    # Safeguard: needs at least 2 signals above 0.5 to be verified
    strong = sum(1 for v in available.values() if v >= 0.5)
    if strong < 2:
        conf = min(conf, 0.74)
    return round(conf, 3)


def decide(conf: float) -> str:
    """Decide verification status based on confidence.
    
    Args:
        conf: Confidence score between 0.0 and 1.0
    
    Returns:
        "verified", "needs_review", or "rejected"
    """
    if conf >= 0.75:
        return "verified"
    if conf >= 0.50:
        return "needs_review"
    return "rejected"


def resolve(target: Dict[str, Any], candidates: List[Dict[str, Any]], 
            face_fn: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """Resolve candidates against a target.
    
    For each candidate:
    - Compute bio score (70% bio_similarity + 30% name_similarity)
    - Compute graph score
    - Compute face score (via face_fn if provided, else None)
    - Combine signals and decide
    - Return enriched result with scores, confidence, decision, and reason
    
    Args:
        target: Target dict with "name", "context", "image"
        candidates: List of candidate dicts
        face_fn: Optional function to compute face similarity (takes target_image, candidate_photo_url)
    
    Returns:
        List of enriched candidate dicts sorted by confidence descending
    """
    results = []
    
    for candidate in candidates:
        # Compute bio score (blend bio and name similarity)
        bio_sim = bio_similarity(target["context"], candidate["bio"])
        name_sim = name_similarity(target["name"], candidate["display_name"])
        s_bio = 0.7 * bio_sim + 0.3 * name_sim
        
        # Compute graph score
        s_graph = graph_score(candidate, candidates)
        
        # Compute face score (None for now, pluggable via face_fn)
        s_face = None
        if face_fn and candidate.get("photo_url"):
            s_face = face_fn(target["image"], candidate["photo_url"])
        
        # Combine and decide
        confidence = combine(s_face, s_bio, s_graph)
        decision = decide(confidence)
        
        # Build reason string
        signals = []
        if s_face is not None:
            signals.append(f"Face {s_face:.2f}")
        else:
            signals.append("Face n/a")
        signals.append(f"bio {s_bio:.2f}")
        signals.append(f"links {s_graph:.2f}")
        
        available_count = sum(1 for s in [s_face, s_bio, s_graph] if s is not None)
        if available_count < 3:
            signals.append(f"(only {available_count} of 3 signals available)")
        
        reason = f"{', '.join(signals)} -> {decision}"
        
        # Enrich candidate with results
        result = candidate.copy()
        result["scores"] = {"face": s_face, "bio": s_bio, "graph": s_graph}
        result["confidence"] = confidence
        result["decision"] = decision
        result["reason"] = reason
        
        results.append(result)
    
    # Sort by confidence descending
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results


if __name__ == "__main__":
    from osint_fetcher import load_mock
    
    # Test with Aarav mock data
    print("=== Resolver Test with Aarav Mehta ===")
    target, candidates = load_mock("Aarav Mehta")
    
    if target and candidates:
        results = resolve(target, candidates)
        
        print(f"\nTarget: {target['name']}")
        print(f"Context: {target['context']}")
        print(f"\n{'Username':<20} {'Confidence':<12} {'Decision':<15}")
        print("-" * 50)
        for r in results:
            print(f"{r['username']:<20} {r['confidence']:<12.3f} {r['decision']:<15}")
