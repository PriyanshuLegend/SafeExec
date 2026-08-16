import json
from suggest_engine import SuggestEngine

def main():
    print("--- Testing Suggest Engine ---")
    
    engine = SuggestEngine()
    
    # Force mock mode for testing if API key is not present (it handles it automatically, but we ensure output matches requirements)
    # The prompt explicitly asked: "Use the same mock-fallback pattern already established in intent_engine.py if no API key is present in your test environment, and say so explicitly."
    if engine.is_mock:
        print("Note: No API key found. Using mock responses for testing.\n")
    
    # 1. Node context
    ctx1 = {
        "project_type": "node",
        "recent_history": ["ls", "npm install"],
        "scripts": ["dev", "build", "test", "lint"]
    }
    
    print("\n--- EXACT CONTEXT DICT SENT TO LLM FOR SCENARIO 1 ---")
    print(json.dumps(ctx1, indent=2))
    print("-----------------------------------------------------\n")
    
    print("[Scenario 1: 'npm r' in Node context]")
    res1 = engine.get_suggestions("npm r", ctx1)
    print(json.dumps(res1, indent=2))
    
    # 2. Git context
    ctx2 = {
        "recent_history": ["git status", "git add ."]
    }
    print("\n[Scenario 2: 'git c' with recent git add]")
    res2 = engine.get_suggestions("git c", ctx2)
    print(json.dumps(res2, indent=2))
    
    # 3. Nonsense context
    ctx3 = {}
    print("\n[Scenario 3: 'xyz123nonsense' with empty context]")
    res3 = engine.get_suggestions("xyz123nonsense", ctx3)
    print(json.dumps(res3, indent=2))

if __name__ == "__main__":
    main()
