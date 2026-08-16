import argparse
import sys
import os
import time
from rich.console import Console

from prefilter import Prefilter
from context import gather_context
from intent_engine import IntentEngine
from display import display_risk_and_prompt
from db import init_db, log_command, get_stats
from project_detector import detect_project_type
from suggest_engine import SuggestEngine
from datetime import datetime

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
    t0 = time.time()
    pf_result = pf.analyze(command)
    t1 = time.time()
    if os.environ.get("SAFEEXEC_DEBUG") == "1":
        console.print(f"[bold yellow][TIMING] Prefilter check:[/] {(t1 - t0) * 1000:.2f} ms")
    
    t0 = time.time()
    ctx = gather_context(command)
    t1 = time.time()
    if os.environ.get("SAFEEXEC_DEBUG") == "1":
        console.print(f"[bold yellow][TIMING] Context gathering:[/] {(t1 - t0) * 1000:.2f} ms")
    
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
    t0 = time.time()
    analysis = engine.analyze(command, ctx)
    t1 = time.time()
    if os.environ.get("SAFEEXEC_DEBUG") == "1":
        console.print(f"[bold yellow][TIMING] Total LLM Analysis (IntentEngine wrapper):[/] {(t1 - t0) * 1000:.2f} ms")
    
    # 3. Display
    t0 = time.time()
    action, final_cmd = display_risk_and_prompt(command, analysis)
    t1 = time.time()
    if os.environ.get("SAFEEXEC_DEBUG") == "1":
        console.print(f"[bold yellow][TIMING] Display rendering and prompt:[/] {(t1 - t0) * 1000:.2f} ms")
    
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

def suggest_command(partial_command: str, raw: bool):
    # 1. Gather context
    ctx = gather_context(partial_command)
    
    # Add project detection context
    proj_ctx = detect_project_type(ctx['cwd'])
    ctx.update(proj_ctx)
    
    # 2. Get suggestions
    engine = SuggestEngine()
    suggestions = engine.get_suggestions(partial_command, ctx)
    
    if raw:
        if suggestions:
            print(suggestions[0].get("completed_command", ""))
        sys.exit(0)
        
    # Normal display
    from rich.panel import Panel
    from rich.text import Text
    
    if not suggestions:
        console.print("[cyan]SafeExec Suggestion:[/] No confident completions found.")
        sys.exit(0)
        
    content = Text()
    for i, s in enumerate(suggestions, 1):
        cmd = s.get("completed_command", "unknown")
        reason = s.get("reasoning", "")
        conf = s.get("confidence", "low").upper()
        
        # Color based on confidence
        conf_color = "green" if conf == "HIGH" else "yellow" if conf == "MEDIUM" else "white"
        
        content.append(f"{i}. ", style="bold")
        content.append(f"{cmd}\n", style="bold cyan")
        content.append(f"   Confidence: ", style="bold")
        content.append(f"{conf} ", style=f"bold {conf_color}")
        content.append(f"- {reason}\n\n", style="italic white")
        
    panel = Panel(
        content,
        title="[bold cyan]SafeExec Suggestions[/bold cyan]",
        border_style="cyan",
        expand=False
    )
    console.print(panel)

def show_status():
    from rich.panel import Panel
    from rich.text import Text
    
    is_active = os.environ.get('SAFEEXEC_ACTIVE') == '1'
    
    if is_active:
        today_str = datetime.now().strftime("%Y-%m-%d")
        stats = get_stats(for_date=today_str)
        
        content = Text()
        content.append("Protection is actively monitoring your shell.\n\n", style="white")
        content.append("Today's Interceptions:\n", style="bold underline white")
        content.append(f"  Total: ", style="white")
        content.append(f"{stats['total_intercepted']}\n", style="bold cyan")
        content.append(f"  Blocked: ", style="white")
        content.append(f"{stats['blocked']}\n", style="bold red")
        content.append(f"  Edited: ", style="white")
        content.append(f"{stats['edited']}\n", style="bold green")
        content.append(f"  Proceeded: ", style="white")
        content.append(f"{stats['proceeded']}\n", style="bold yellow")
        
        panel = Panel(
            content,
            title="[bold green]🛡️ SafeExec: ACTIVE[/bold green]",
            border_style="green",
            expand=False
        )
        console.print(panel)
    else:
        content = Text()
        content.append("Protection is currently disabled in this shell.\n\n", style="white")
        content.append("To enable protection, run:\n", style="white")
        content.append("  safeexec on\n", style="bold cyan")
        
        panel = Panel(
            content,
            title="[bold red]⚠️ SafeExec: NOT ACTIVE[/bold red]",
            border_style="red",
            expand=False
        )
        console.print(panel)

def main():
    parser = argparse.ArgumentParser(description="SafeExec - AI Command Interceptor")
    subparsers = parser.add_subparsers(dest="command")
    
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("cmd_string", help="The command string to check")
    
    suggest_parser = subparsers.add_parser("suggest")
    suggest_parser.add_argument("partial_command", help="The partially typed command string")
    suggest_parser.add_argument("--raw", action="store_true", help="Print only raw suggestions for scripting")
    
    status_parser = subparsers.add_parser("status")
    
    stats_parser = subparsers.add_parser("stats")
    
    args = parser.parse_args()
    
    if args.command == "check":
        check_command(args.cmd_string)
    elif args.command == "suggest":
        suggest_command(args.partial_command, args.raw)
    elif args.command == "status":
        show_status()
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()


