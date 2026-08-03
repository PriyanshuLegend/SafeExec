# SafeExec

SafeExec is an AI-Based System Intent Engine for Safe Linux Command Execution. It intercepts your terminal commands using a shell hook, evaluates the risk level (using a local prefilter and an LLM), and explains potential dangers before executing them.

## Architecture

1. **Bash Hook (`hook.sh`)**: Uses `trap DEBUG` to intercept commands before they are run.
2. **Local Pre-filter (`prefilter.py`)**: Uses regex rules in `risk_rules.yaml` to instantly pass safe commands or hard-block undeniably catastrophic ones.
3. **Intent Engine (`intent_engine.py`)**: For ambiguous commands, calls the Groq or OpenAI API to analyze intent and suggest safer alternatives.
4. **Display UI (`display.py`)**: Presents a rich terminal warning box.
5. **SQLite Logger (`db.py`)**: Logs intercepted commands and user actions to `~/.safeexec.db` for session stats.

## Installation

1. Clone or download this project.
2. Ensure you have Python 3.11+ installed.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your API key (Groq recommended for speed):
   ```bash
   export GROQ_API_KEY="your_api_key_here"
   ```
   *(If no API key is provided, SafeExec will use a local mock engine for testing).*
5. Source the hook in your shell (e.g., add to `~/.bashrc`):
   ```bash
   source /path/to/safeexec/hook.sh
   ```

## Usage

Simply use your terminal as normal! Safe commands like `ls` will execute instantly. Risky commands will trigger a SafeExec popup.

You can also manually check commands:
```bash
safeexec check "rm -rf /var/log"
```

To view your blocked/intercepted command stats for the session:
```bash
safeexec stats
```

## Demo

See `demo_commands.txt` for a list of commands you can type into your shell to test the different risk tiers.
