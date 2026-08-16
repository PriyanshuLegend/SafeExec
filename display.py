import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def display_risk_and_prompt(command: str, analysis: dict) -> tuple[str, str]:
    """
    Displays the risk analysis in a rich panel and prompts the user.
    Returns a tuple: (action, command_to_execute)
    action can be: 'proceed', 'abort', 'edit'
    """
    risk_level = analysis.get("risk_level", "UNKNOWN").upper()
    
    # Map risk levels to colors
    color_map = {
        "CRITICAL": "bold red on black",
        "HIGH": "red",
        "MEDIUM": "yellow",
        "LOW": "cyan",
        "UNKNOWN": "white"
    }
    
    border_color = color_map.get(risk_level, "white").split()[0]
    if risk_level == "CRITICAL":
        border_color = "red"
        
    content = Text()
    
    content.append("Command: ", style="bold")
    content.append(f"{command}\n\n", style="bold white")
    
    content.append("Risk Level: ", style="bold")
    content.append(f"{risk_level}\n", style=color_map.get(risk_level, "white"))
    
    content.append("Category: ", style="bold")
    content.append(f"{analysis.get('category', 'N/A')}\n\n", style="magenta")
    
    content.append("Explanation: ", style="bold")
    content.append(f"{analysis.get('plain_english_explanation', 'No explanation provided.')}\n\n")
    
    content.append("Impact: ", style="bold")
    content.append(f"{analysis.get('potential_impact', 'Unknown')}\n")
    
    safer_alt = analysis.get("safer_alternative")
    if safer_alt:
        content.append("\nSafer Alternative: ", style="bold green")
        content.append(f"{safer_alt}\n", style="italic green")
        
    panel = Panel(
        content,
        title="[bold red]SafeExec Warning[/bold red]",
        border_style=border_color,
        expand=False
    )
    
    console.print(panel)
    
    # Prompt the user
    choices = ["y", "n"]
    prompt_text = "Proceed anyway? [y/N]"
    
    if safer_alt:
        choices.append("edit")
        prompt_text = "Proceed anyway? [y/N/edit]"
        
    while True:
        console.print(f"[bold yellow]{prompt_text}: [/bold yellow]", end="")
        try:
            choice = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return 'abort', command
            
        if not choice:
            choice = 'n'
            
        if choice in ['y', 'yes']:
            return 'proceed', command
        elif choice in ['n', 'no']:
            return 'abort', command
        elif choice == 'edit' and safer_alt:
            return 'edit', safer_alt
        else:
            console.print("[red]Invalid choice. Please answer with y, n, or edit.[/red]")

if __name__ == "__main__":
    # Test cases
    test_analysis = {
        "risk_level": "HIGH",
        "category": "DESTRUCTIVE",
        "plain_english_explanation": "You are attempting to forcefully remove a system directory.",
        "potential_impact": "System instability and data loss.",
        "safer_alternative": "rm -i /var/log/app"
    }
    
    print("Testing Display (Press enter to default to No, or type y/n/edit)")
    # Since we can't interactively test input in the automated test cleanly without sending stdin,
    # we will mock input for the test
    
    def run_test(mocked_input):
        print(f"\n--- Testing with user input: '{mocked_input}' ---")
        original_input = __builtins__.input if hasattr(__builtins__, 'input') else input
        globals()['input'] = lambda: mocked_input
        try:
            action, final_cmd = display_risk_and_prompt("rm -rf /var/log/app", test_analysis)
            print(f"Result: Action={action}, Final Command={final_cmd}")
        finally:
            globals()['input'] = original_input

    run_test('n')
    run_test('y')
    run_test('edit')
