import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Try to load .env from the safeexec dir first, then parent dir
base_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(base_dir, '.env')):
    load_dotenv(os.path.join(base_dir, '.env'))
else:
    load_dotenv(os.path.join(os.path.dirname(base_dir), '.env'))
try:
    import openai
except ImportError:
    openai = None

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Linux command completion assistant. Given a partially typed command, the user's recent command history, current directory, and detected project type, suggest 1-3 likely full commands the user is trying to type. 

CRITICAL INSTRUCTIONS:
- Prioritize commands consistent with the project type and recent history. 
- EVERY suggestion MUST be a fully runnable command that can be executed as-is.
- If 'Available Scripts' are provided, you MUST append one of those specific scripts to your suggestions (e.g., 'npm run dev').
- NEVER suggest 'npm run' or 'yarn run' by itself without appending a specific script name.
- Respond ONLY with a JSON object containing a 'suggestions' array.

Expected JSON format:
{
  "suggestions": [
    {
      "completed_command": "npm run dev",
      "confidence": "high",
      "reasoning": "matches available script"
    }
  ]
}"""

class SuggestEngine:
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
            
        base_url = "https://api.groq.com/openai/v1" if is_groq else None
        
        self.client = openai.OpenAI(api_key=self.api_key, base_url=base_url)

    def get_suggestions(self, partial_command: str, context: dict, retries: int = 1) -> List[Dict[str, Any]]:
        if self.is_mock:
            return self._mock_get_suggestions(partial_command, context)

        user_message = f"""
Partial Command: {partial_command}
Context:
- CWD: {context.get('cwd', 'unknown')}
- User: {context.get('username', 'unknown')} (Root: {context.get('is_root', False)})
- Recent History: {context.get('recent_history', [])}
- Project Type: {context.get('project_type', 'unknown')}
- Package Manager: {context.get('package_manager', 'None')}
- Markers Found: {context.get('markers_found', [])}
- Available Scripts (if Node): {context.get('scripts', [])}
"""

        for attempt in range(retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"} # We might need to handle raw string array depending on model, but we'll try json parsing. Wait, response_format json_object requires the output to be an object, not an array. We should ask for an object containing an array.
                )
                
                content = response.choices[0].message.content
                
                # Parse JSON
                parsed = json.loads(content)
                
                # If the LLM returned a JSON object containing an array (due to json_object enforcement)
                if isinstance(parsed, dict):
                    # Find the first array value
                    for val in parsed.values():
                        if isinstance(val, list):
                            parsed = val
                            break
                    if isinstance(parsed, dict):
                        # Still a dict, try to wrap it
                        parsed = [parsed]
                        
                if not isinstance(parsed, list):
                    raise ValueError("JSON response is not a list/array")
                    
                # Validate schema
                valid_suggestions = []
                for item in parsed:
                    if isinstance(item, dict) and "completed_command" in item:
                        valid_suggestions.append({
                            "completed_command": item.get("completed_command"),
                            "confidence": item.get("confidence", "low"),
                            "reasoning": item.get("reasoning", "")
                        })
                        
                return valid_suggestions
                
            except json.JSONDecodeError as e:
                logger.error(f"Attempt {attempt + 1}: Failed to parse JSON from LLM: {e}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: LLM call failed: {e}")
                
            if attempt == retries:
                logger.error("Max retries reached. Returning empty list.")
                return []

    def _mock_get_suggestions(self, partial_command: str, context: dict) -> List[Dict[str, Any]]:
        if "npm r" in partial_command and context.get("project_type") == "node":
            return [
                {
                    "completed_command": "npm run dev",
                    "confidence": "high",
                    "reasoning": "Common node script based on package.json"
                },
                {
                    "completed_command": "npm run build",
                    "confidence": "medium",
                    "reasoning": "Standard build command"
                }
            ]
        elif "git c" in partial_command and "git add ." in context.get("recent_history", []):
            return [
                {
                    "completed_command": "git commit -m \"\"",
                    "confidence": "high",
                    "reasoning": "Usually follows git add"
                },
                {
                    "completed_command": "git checkout -b",
                    "confidence": "medium",
                    "reasoning": "Common git branch operation"
                }
            ]
        else:
            return []

if __name__ == "__main__":
    pass
