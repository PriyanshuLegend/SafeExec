import os
import json
import logging
from typing import Dict, Any

try:
    import openai
except ImportError:
    openai = None

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Linux command safety analyzer. Given a shell command and its execution context (current directory, whether user is root, recent command history), assess its risk. Be precise, not paranoid — flag genuine danger, not routine sysadmin work. Consider: is this destructive, irreversible, privilege-escalating, or does it expose the system to network risk? If a safer alternative achieves the same practical goal, suggest it. Respond ONLY with the JSON schema provided, no prose outside it.

JSON Schema:
{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "category": "string",
  "plain_english_explanation": "why this is risky, in one or two sentences",
  "potential_impact": "what could go wrong if this runs",
  "safer_alternative": "a rewritten command, or null if no safer version exists",
  "context_flags": ["e.g. running as root", "targeting system directory /etc"]
}"""

class IntentEngine:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
        is_groq = "GROQ_API_KEY" in os.environ
        
        self.model = "llama-3.3-70b-versatile" if is_groq else "gpt-3.5-turbo"
        
        self.is_mock = False
        if not self.api_key or not openai:
            logger.warning("No API key found or openai not installed. Using mock responses for testing.")
            self.is_mock = True
            self.client = None
            return
            
        is_groq = "GROQ_API_KEY" in os.environ
        base_url = "https://api.groq.com/openai/v1" if is_groq else None
        self.model = "llama-3.3-70b-versatile" if is_groq else "gpt-3.5-turbo"
        
        self.client = openai.OpenAI(api_key=self.api_key, base_url=base_url)

    def analyze(self, command: str, context: dict, retries: int = 1) -> dict:
        if self.is_mock:
            return self._mock_analyze(command)

        user_message = f"""
Command: {command}
Context:
- CWD: {context.get('cwd', 'unknown')}
- User: {context.get('username', 'unknown')} (Root: {context.get('is_root', False)})
- Target is protected: {context.get('target_is_protected', False)}
- Recent History: {context.get('recent_history', [])}
"""

        for attempt in range(retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                # Verify JSON parsing
                parsed = json.loads(content)
                
                # Basic validation
                if "risk_level" not in parsed or "plain_english_explanation" not in parsed:
                    raise ValueError("JSON missing required fields")
                    
                return parsed
                
            except json.JSONDecodeError as e:
                logger.error(f"Attempt {attempt + 1}: Failed to parse JSON from LLM: {e}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: LLM call failed: {e}")
                
            if attempt == retries:
                logger.error("Max retries reached. Failing safe (BLOCK).")
                return self._fail_safe()

    def _mock_analyze(self, command: str) -> dict:
        if "rm" in command:
            return {
                "risk_level": "HIGH",
                "category": "DESTRUCTIVE",
                "plain_english_explanation": f"This command removes files aggressively.",
                "potential_impact": "Loss of important logs or data.",
                "safer_alternative": "rm -i",
                "context_flags": ["destructive", "root_user"]
            }
        elif "chmod" in command:
            return {
                "risk_level": "HIGH",
                "category": "PRIVILEGE_ESCALATION",
                "plain_english_explanation": "Granting 777 permissions exposes the files to anyone.",
                "potential_impact": "Any user can modify or execute these files.",
                "safer_alternative": "chmod 755",
                "context_flags": ["dangerous_perms", "protected_target"]
            }
        else:
            return {
                "risk_level": "MEDIUM",
                "category": "IRREVERSIBLE_GIT",
                "plain_english_explanation": "Force pushing overwrites remote history.",
                "potential_impact": "Coworkers could lose their pushed commits.",
                "safer_alternative": "git push --force-with-lease",
                "context_flags": ["git_repo"]
            }

    def _fail_safe(self) -> dict:
        return {
            "risk_level": "CRITICAL",
            "category": "ANALYSIS_FAILED",
            "plain_english_explanation": "The AI analysis failed to process the command or returned malformed data.",
            "potential_impact": "Unknown risk. Blocked by fail-safe mechanism.",
            "safer_alternative": None,
            "context_flags": ["api_error", "fail_safe"]
        }

if __name__ == "__main__":
    engine = IntentEngine()
    
    test_cases = [
        ("rm -rf /var/log/app", {"cwd": "/var/log", "username": "admin", "is_root": True, "recent_history": ["cd /var/log", "ls"], "target_is_protected": True}),
        ("chmod -R 777 /var/www/html", {"cwd": "/home/user", "username": "user", "is_root": False, "recent_history": [], "target_is_protected": True}),
        ("git push --force origin main", {"cwd": "/project", "username": "dev", "is_root": False, "recent_history": ["git commit --amend"], "target_is_protected": False})
    ]
    
    print("\n--- Testing IntentEngine (3 Hardcoded Commands) ---")
    for cmd, ctx in test_cases:
        print(f"\nAnalyzing Command: {cmd}")
        result = engine.analyze(cmd, ctx)
        print(json.dumps(result, indent=2))
        
    print("\n--- Testing Malformed JSON Recovery (Fail Safe) ---")
    engine.is_mock = False
    
    # Mocking client to return bad JSON to trigger the fail-safe
    class FakeMessage:
        content = "This is not JSON at all."
    class FakeChoice:
        message = FakeMessage()
    class FakeResponse:
        choices = [FakeChoice()]
    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse()
    class FakeChat:
        completions = FakeCompletions()
    class FakeClient:
        chat = FakeChat()
        
    engine.client = FakeClient()
    result = engine.analyze("dummy command", {})
    print(json.dumps(result, indent=2))
