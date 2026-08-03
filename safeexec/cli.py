import argparse
import sys
import os
from rich.console import Console

from prefilter import Prefilter
from context import gather_context
from intent_engine import IntentEngine
from display import display_risk_and_prompt
from db import init_db, log_command, get_stats

console = Console()
RUN_FILE = os.path.expanduser("~/.safeexec_run")

def setup():
    init_db()

def check_command(command: str):
    setup()
    
    if os.path.exists(RUN_FILE):
        try:
            os.remove(RUN_FILE)
        except Exception:
            pass
            
    # 1. Prefilter
    pf = Prefilter()
    pf_result = pf.analyze(command)
    
    ctx = gather_context(command)
    
    if pf_result.status == 'SAFE':
        # Instantly allow
        sys.exit(0)
        
    if pf_result.status == 'BLOCKED':
        # Hard block
        console.print(f"\n[bold red on black] SafeExec HARD BLOCK [/]")
        console.print(f"[red]Command:[/] {command}")
        console.print(f"[red]Reason:[/] {pf_result.rule.description}\n")
        
        log_command(command, pf_result.rule.severity, pf_result.rule.category, "hard_block", ctx['cwd'])
        sys.exit(1)
        
    # 2. LLM Analysis
    engine = IntentEngine()
    analysis = engine.analyze(command, ctx)
    
    # 3. Display
    action, final_cmd = display_risk_and_prompt(command, analysis)
    
    # 4. Log
    log_command(command, analysis.get('risk_level', 'UNKNOWN'), analysis.get('category', 'UNKNOWN'), action, ctx['cwd'])
    
    # 5. Handle action
    if action == 'proceed':
        sys.exit(0)
    elif action == 'abort':
        sys.exit(1)
    elif action == 'edit':
        # Write to run file for bash hook to execute
        with open(RUN_FILE, 'w') as f:
            f.write(final_cmd + "\n")
        sys.exit(2)

def show_stats():
    setup()
    stats = get_stats()
    console.print("\n[bold cyan]--- SafeExec Stats ---[/bold cyan]")
    console.print(f"Total Intercepted: [white]{stats['total_intercepted']}[/white]")
    console.print(f"Blocked: [red]{stats['blocked']}[/red]")
    console.print(f"Edited: [green]{stats['edited']}[/green]")
    console.print(f"Proceeded: [yellow]{stats['proceeded']}[/yellow]\n")

def main():
    parser = argparse.ArgumentParser(description="SafeExec - AI Command Interceptor")
    subparsers = parser.add_subparsers(dest="command")
    
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("cmd_string", help="The command string to check")
    
    stats_parser = subparsers.add_parser("stats")
    
    args = parser.parse_args()
    
    if args.command == "check":
        check_command(args.cmd_string)
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
