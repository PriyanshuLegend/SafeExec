#!/bin/bash

# Find the directory where this script is located
SAFEEXEC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

safeexec() {
    if [ "$1" = "on" ]; then
        source "$SAFEEXEC_DIR/hook.sh"
        echo -e "\e[32m[SafeExec]\e[0m Protection ENABLED."
    elif [ "$1" = "off" ]; then
        trap - DEBUG
        unset SAFEEXEC_ACTIVE
        echo -e "\e[33m[SafeExec]\e[0m Protection DISABLED."
    else
        # Pass through to cli.py
        python "$SAFEEXEC_DIR/cli.py" "$@"
    fi
}
