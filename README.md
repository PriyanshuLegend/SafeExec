# SafeExec 🛡️

AI-powered safety layer for your Linux terminal — catches dangerous commands before they run, and suggests smart completions based on your project.

## Quick Start

1. Clone this repo:
```bash
   git clone <your-repo-url>
   cd safeexec
```

2. Run the installer:
```bash
   bash install.sh
```

3. When prompted, paste your free Groq API key — get one in 30 seconds at
   [console.groq.com/keys](https://console.groq.com/keys)
   (Or press Enter to skip — SafeExec still works with basic pattern-matching protection, just without AI-powered explanations.)

4. Open a new terminal. You're protected. Try it:
```bash
   safeexec status
   rm -rf /
```

That's it — no config files to edit, no manual setup.

### Developer / Manual Setup
If you prefer not to use the automated installer, or if you run into environment issues:

1. Ensure you have Python 3.10+ installed.
2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
   *(If this fails, create a virtual environment first: `python3 -m venv venv && source venv/bin/activate`)*
3. Set up your API key by copying the example environment file:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your GROQ_API_KEY.
4. Source the hook manually in your shell:
   ```bash
   source /path/to/safeexec/safeexec_toggle.sh
   safeexec on
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
