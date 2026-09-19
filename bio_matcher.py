from sentence_transformers import SentenceTransformer, util
from rapidfuzz import fuzz

# Load the model once at module level
_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def bio_similarity(text_a: str, text_b: str) -> float:
    """Returns 0.0–1.0. Higher = more similar meaning.
    
    Args:
        text_a: First text to compare
        text_b: Second text to compare
    
    Returns:
        Similarity score between 0.0 and 1.0, or 0.0 for empty text
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0
    emb = _model.encode([text_a, text_b], convert_to_tensor=True)
    score = util.cos_sim(emb[0], emb[1]).item()
    return max(0.0, min(1.0, score))  # clamp to 0–1


def name_similarity(a: str, b: str) -> float:
    """Returns 0.0–1.0 based on token sort ratio.
    
    Args:
        a: First name to compare
        b: Second name to compare
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    return fuzz.token_sort_ratio(a.lower(), b.lower()) / 100


if __name__ == "__main__":
    # Test bio similarity
    print("=== Bio Similarity Tests ===")
    similar = bio_similarity("ML engineer building NLP tools",
                            "I develop natural language processing software")
    dissimilar = bio_similarity("ML engineer building NLP tools",
                                "Professional chef and food blogger")
    print(f"Similar pair: {similar:.3f}")
    print(f"Dissimilar pair: {dissimilar:.3f}")
    
    # Test name similarity
    print("\n=== Name Similarity Tests ===")
    name_similar = name_similarity("Johnathan Doe", "Doe Johnathan")
    name_dissimilar = name_similarity("Johnathan Doe", "Jane Smith")
    print(f"Similar names: {name_similar:.3f}")
    print(f"Dissimilar names: {name_dissimilar:.3f}")
