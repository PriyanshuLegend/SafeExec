#!/bin/bash

# Find the directory where this script is located
SAFEEXEC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

safeexec_hook() {
    local cmd="$BASH_COMMAND"
    
    # Ignore internal bash commands and safeexec CLI calls to avoid infinite loops
    if [[ "$cmd" == *"cli.py"* || "$cmd" == *"PROMPT_COMMAND"* || "$cmd" == *"safeexec"* ]]; then
        return 0
    fi

    # Execute Python checker. Ensure it reads from /dev/tty so input works in hooks.
    python "$SAFEEXEC_DIR/cli.py" check "$cmd" </dev/tty
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        # Proceed with original command
        return 0
    elif [ $exit_code -eq 1 ]; then
        # Abort original command
        return 1
    elif [ $exit_code -eq 2 ]; then
        # Execute safer alternative
        local run_file=~/.safeexec_run
        if [ -f "$run_file" ]; then
            local new_cmd="$(cat "$run_file")"
            rm -f "$run_file"
            echo -e "\e[32m[SafeExec]\e[0m Executing alternative: $new_cmd"
            eval "$new_cmd" </dev/tty
        fi
        # Abort original command so it doesn't run too
        return 1
    fi
}

# extdebug allows returning non-zero from trap DEBUG to cancel the command execution
shopt -s extdebug
trap safeexec_hook DEBUG

# Alias for manual interaction
alias safeexec="python '$SAFEEXEC_DIR/cli.py'"
