import json
from pathlib import Path


def load_mock(name: str):
    """
    Load mock data for a target name (case-insensitive).
    
    Args:
        name: Target name to search for
    
    Returns:
        Tuple of (target_dict, candidates_list) or (None, None) if not found
    """
    mock_path = Path(__file__).parent / "mock_data.json"
    
    if not mock_path.exists():
        print(f"Mock data file not found: {mock_path}")
        print(f"Current directory: {Path(__file__).parent}")
        print(f"Files in directory: {list(Path(__file__).parent.iterdir())}")
        return None, None
    
    with open(mock_path, 'r') as f:
        data = json.load(f)
    
    name_lower = name.lower().strip()
    
    for target in data.get("targets", []):
        if target["name"].lower().strip() == name_lower:
            return target, target["candidates"]
    
    print(f"No mock data found for name: {name}")
    print(f"Available names: {[t['name'] for t in data.get('targets', [])]}")
    return None, None


def discover(name: str, context: str, use_mock: bool = True):
    """
    Discover candidate accounts for a target name.
    
    Args:
        name: Target name to search for
        context: Context about the target (city, field, etc.)
        use_mock: If True, use mock data; if False, use live discovery (not yet implemented)
    
    Returns:
        Tuple of (target_dict, candidates_list) or (None, None) if not found
    """
    if use_mock:
        return load_mock(name)
    else:
        # TODO: Implement live discovery
        print("Live discovery not yet implemented, falling back to mock")
        return load_mock(name)


if __name__ == "__main__":
    # Test loading mock data
    test_names = ["Aarav Mehta", "priya sharma", "Unknown Person"]
    
    for test_name in test_names:
        print(f"\n--- Loading mock data for: {test_name} ---")
        target, candidates = load_mock(test_name)
        
        if target:
            print(f"Target: {target['name']}")
            print(f"Context: {target['context']}")
            print(f"Image: {target['image']}")
            print(f"Candidates found: {len(candidates)}")
            for i, cand in enumerate(candidates, 1):
                print(f"  {i}. {cand['platform']}/{cand['username']}: {cand['bio'][:50]}...")
        else:
            print("No data found")
