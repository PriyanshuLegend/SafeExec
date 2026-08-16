#!/bin/bash

# SafeExec Installer

echo -e "\e[36m"
echo "  ___       __      ___               "
echo " / __| __ _|fe|___ | __|_ _____ __    "
echo " \__ \/ _\`|  _/ -_)| _|\ \ / -_) _|   "
echo " |___/\__,_|_| \___||___/_\_\___|\__| "
echo -e "\e[0m"
echo "Welcome to the SafeExec installer."

# 1. Check for python3 and pip3
if ! command -v python3 &> /dev/null; then
    echo -e "\e[31mError:\e[0m python3 could not be found."
    echo "SafeExec requires Python 3.10 or higher. Please install it and try again."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "\e[31mError:\e[0m pip3 could not be found."
    echo "Please install pip3 (e.g., sudo apt install python3-pip) and try again."
    exit 1
fi

SAFEEXEC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SAFEEXEC_DIR"

# 2. Install dependencies
echo "Installing dependencies..."
if ! pip3 install -r requirements.txt --break-system-packages > /dev/null 2>&1; then
    echo -e "\e[33mWarning:\e[0m System-wide pip install failed."
    echo "Please create a virtual environment manually by running:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "Then re-run this install script."
    exit 1
fi
echo -e "\e[32mDependencies installed successfully.\e[0m"

# 3. Handle API key
KEY_STATUS="Not set (Edit .env manually to add later)"
if [ -f ".env" ] && grep -q "GROQ_API_KEY=" ".env" && ! grep -q "GROQ_API_KEY=$" ".env"; then
    echo ".env file with API key already exists. Skipping API key setup."
    KEY_STATUS="Configured"
else
    echo ""
    echo "SafeExec needs a free Groq API key for its AI features."
    echo "Get one here: https://console.groq.com/keys"
    read -s -p "Paste it below (or press Enter to skip and use mock data): " api_key
    echo
    if [ -n "$api_key" ]; then
        echo "GROQ_API_KEY=$api_key" > .env
        echo -e "\e[32mAPI key saved to .env.\e[0m"
        KEY_STATUS="Configured"
    else
        echo -e "\e[33mNo key provided.\e[0m AI features will use mock/fallback data."
        echo "You can add it later by editing the .env file in the SafeExec directory."
        touch .env
    fi
fi

# 4. Shell Integration
BASHRC_FILE="$HOME/.bashrc"
echo ""
echo "This script will add SafeExec to your $BASHRC_FILE."
read -p "Do you want to proceed with shell integration? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Shell integration skipped."
    BASHRC_STATUS="Skipped"
    AUTO_ENABLE_STATUS="Skipped"
else
    MARKER="# >>> SafeExec initialization >>>"
    if [ -f "$BASHRC_FILE" ] && grep -q "$MARKER" "$BASHRC_FILE"; then
        echo -e "\e[33mNotice:\e[0m SafeExec appears to already be installed in $BASHRC_FILE."
        BASHRC_STATUS="Already installed"
        
        # Determine current auto-enable status for summary
        if grep -q "safeexec on" "$BASHRC_FILE"; then
            AUTO_ENABLE_STATUS="Yes"
        else
            AUTO_ENABLE_STATUS="No"
        fi
    else
        echo -e "\nAdding SafeExec shell integration to $BASHRC_FILE..."
        cat << 'EOF' >> "$BASHRC_FILE"

# >>> SafeExec initialization >>>
# Added by SafeExec installer
EOF
        echo "source \"$SAFEEXEC_DIR/safeexec_toggle.sh\"" >> "$BASHRC_FILE"
        BASHRC_STATUS="Added to $BASHRC_FILE"
        
        echo ""
        echo "SafeExec can automatically protect your shell every time you open a new terminal."
        echo "If you choose NO, you can still manually enable it anytime by typing 'safeexec on'."
        read -p "Enable SafeExec by default on new terminals? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "safeexec on" >> "$BASHRC_FILE"
            echo -e "Auto-enable \e[32mconfigured\e[0m."
            AUTO_ENABLE_STATUS="Yes"
        else
            echo -e "Auto-enable \e[33mskipped\e[0m. (Manual start required)."
            AUTO_ENABLE_STATUS="No"
        fi
        
        cat << 'EOF' >> "$BASHRC_FILE"
# <<< SafeExec initialization <<<
EOF
    fi

    # 5. Handle .bash_profile / .profile bridge
    PROFILE_FILE=""
    if [ -f "$HOME/.bash_profile" ]; then
        PROFILE_FILE="$HOME/.bash_profile"
    else
        PROFILE_FILE="$HOME/.profile"
    fi
    
    BRIDGE_MARKER="# >>> SafeExec bashrc bridge >>>"
    if [ -f "$PROFILE_FILE" ] && grep -q "$BRIDGE_MARKER" "$PROFILE_FILE"; then
        echo "Bridge already exists in $PROFILE_FILE."
    else
        echo "Creating bridge to source ~/.bashrc in $PROFILE_FILE..."
        cat << 'EOF' >> "$PROFILE_FILE"

# >>> SafeExec bashrc bridge >>>
# Added by SafeExec installer to ensure .bashrc is loaded in login shells
if [ -n "$BASH_VERSION" ]; then
    if [ -f "$HOME/.bashrc" ]; then
        . "$HOME/.bashrc"
    fi
fi
# <<< SafeExec bashrc bridge <<<
EOF
    fi
fi

# 6. Success summary
echo ""
echo "✅ SafeExec installed successfully!"
echo " - Dependencies installed"
echo " - API key: $KEY_STATUS"
echo " - Shell integration: $BASHRC_STATUS"
echo " - Auto-enable on new terminals: $AUTO_ENABLE_STATUS"
echo ""
echo "Open a new terminal to get started, then run: safeexec status"
echo ""
