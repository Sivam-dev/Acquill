"""
Acquill - Your AI Learning Companion CLI
Interactive chat + background git-diff monitoring
"""

import os
import sys
import time
import threading
import subprocess
from typing import Optional

# Add project root to path for imports (cli.py is at Acquill/interface/cli.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from acquill.utils.api import process_message, process_diff, check_and_send_reminders, generate_weekly_digest, analyze_learning_patterns
from acquill.config.auth import signup as auth_signup, signin as auth_signin, signout as auth_signout, get_current_user, supabase

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
CHECK_INTERVAL = int(os.getenv("GIT_DIFF_CHECK_INTERVAL", "300"))  # seconds

# Rich console for styled output
console = Console()

# Global flag to stop background thread when chat exits
_stop_background = threading.Event()

app = typer.Typer(
    name="Acquill",
    help="AI Learning Companion - Chat and automatic code learning tracker",
    add_completion=False
)


def background_git_checker():
    """
    Background thread that periodically checks git diff and processes changes.
    Runs every CHECK_INTERVAL seconds until _stop_background is set.
    """
    console.print("[dim]🔍 Background git monitor started[/dim]")
    
    while not _stop_background.is_set():
        try:
            # Wait for the interval (but check stop flag every second)
            for _ in range(CHECK_INTERVAL):
                if _stop_background.is_set():
                    return
                time.sleep(1)
            
            # Run git diff
            result = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            diff_output = result.stdout.strip()
            
            # Skip if no changes
            if not diff_output:
                continue
            
            # Get changed files
            files_result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            changed_files = files_result.stdout.strip().split("\n")
            
            # Process each changed file
            for filepath in changed_files:
                if not filepath:
                    continue
                
                # Get diff for this specific file
                file_diff_result = subprocess.run(
                    ["git", "diff", filepath],
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                
                file_diff = file_diff_result.stdout.strip()
                
                if not file_diff:
                    continue
                
                # Process through orchestration
                response = process_diff(file_diff, filepath)
                
                # Only print if not skipped (skip_storage was not set)
                if response.get("reply"):
                    console.print("\n[dim]─── Background Code Analysis ───[/dim]")
                    console.print(f"[cyan]📁 File:[/cyan] {filepath}")
                    console.print(f"[yellow]📚 Topic:[/yellow] {response.get('topic', 'unknown')}")
                    console.print(f"[magenta]⚡ Event:[/magenta] {response.get('event_type', 'unknown')}")
                    console.print(f"[green]💬 Analysis:[/green] {response.get('reply', 'No analysis')}")
                    console.print("[dim]─────────────────────────────────[/dim]\n")
        
        except Exception as e:
            console.print(f"[red]Background check error: {str(e)}[/red]")
            # Don't kill the thread - just continue to next interval
            continue


@app.command()
def chat():
    """
    Start interactive chat with Acquill.
    Also starts background git-diff monitoring in a separate thread.
    """
    
    # Start background thread
    _stop_background.clear()
    bg_thread = threading.Thread(target=background_git_checker, daemon=True)
    bg_thread.start()
    
    # Welcome message
    console.print(Panel.fit(
        "[bold cyan]Acquill - Your AI Learning Companion[/bold cyan]\n"
        "Type your learning updates, questions, or struggles.\n"
        "[dim]Type 'exit' to quit.[/dim]",
        border_style="cyan"
    ))
    
    console.print(f"[dim]Git diff monitoring: every {CHECK_INTERVAL}s[/dim]\n")
    
    # Main chat loop
    while True:
        try:
            # Get user input
            user_input = console.input("[bold cyan]>[/bold cyan] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("[yellow]👋 See you next time! Keep learning![/yellow]")
                _stop_background.set()  # Stop background thread
                break
            
            # Process through orchestration
            response = process_message(user_input)
            
            # Display reply
            if response.get("error"):
                console.print(f"[red]❌ Error: {response['error']}[/red]")
            elif response.get("reply"):
                console.print(f"\n[green]{response['reply']}[/green]\n")
            else:
                console.print("[dim]Message received (no reply generated)[/dim]\n")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Interrupted. Goodbye![/yellow]")
            _stop_background.set()
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def remind():
    """Check for overdue review reminders"""
    
    console.print("\n⏰ [bold]Checking for overdue reviews...[/bold]\n")
    
    reminder = check_and_send_reminders()
    
    if reminder:
        console.print(Panel(Markdown(reminder), border_style="yellow"))
    else:
        console.print("[green]✅ All caught up! No reviews due right now.[/green]\n")


@app.command()
def digest(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to include in digest")
):
    """Generate a progress digest for the last N days"""
    
    console.print(f"\n📊 [bold]Generating {days}-day digest...[/bold]\n")
    
    digest_text = generate_weekly_digest(days)
    
    if digest_text:
        console.print(Panel(Markdown(digest_text), border_style="blue"))
    else:
        console.print("[yellow]No learning activity found in this period.[/yellow]\n")


@app.command()
def patterns():
    """Analyze recurring learning patterns"""
    
    console.print("\n🔍 [bold]Analyzing learning patterns...[/bold]\n")
    
    insights = analyze_learning_patterns()
    
    if insights:
        console.print(Panel(Markdown(insights), border_style="magenta"))
    else:
        console.print("[yellow]Not enough data for pattern analysis yet.[/yellow]\n")


@app.command()
def signup():
    """Create a new Acquill account"""
    console.print("\n[bold cyan]📝 Sign Up for Acquill[/bold cyan]\n")
    
    email = console.input("[cyan]Email:[/cyan] ").strip()
    
    if not email:
        console.print("[red]❌ Email is required[/red]")
        return
    
    password = console.input("[cyan]Password:[/cyan] ", password=True).strip()
    
    if not password:
        console.print("[red]❌ Password is required[/red]")
        return
    
    try:
        result = auth_signup(email, password)
        console.print(f"\n[green]✅ Account created successfully![/green]")
        console.print(f"[dim]Check your email to verify your account.[/dim]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Signup failed: {str(e)}[/red]\n")


@app.command()
def login():
    """Login to your Acquill account"""
    console.print("\n[bold cyan]🔐 Login to Acquill[/bold cyan]\n")
    
    email = console.input("[cyan]Email:[/cyan] ").strip()
    
    if not email:
        console.print("[red]❌ Email is required[/red]")
        return
    
    password = console.input("[cyan]Password:[/cyan] ", password=True).strip()
    
    if not password:
        console.print("[red]❌ Password is required[/red]")
        return
    
    try:
        result = auth_signin(email, password)
        console.print(f"\n[green]✅ Login successful![/green]")
        console.print(f"[dim]Welcome back! You can now use all Acquill features.[/dim]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Login failed: {str(e)}[/red]\n")


@app.command()
def logout():
    """Logout from your Acquill account"""
    console.print("\n[bold cyan]👋 Logout from Acquill[/bold cyan]\n")
    
    try:
        auth_signout()
        console.print("[green]✅ Logged out successfully![/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Logout failed: {str(e)}[/red]\n")


@app.command()
def whoami():
    """Show current logged in user"""
    console.print("\n[bold cyan]👤 Current User[/bold cyan]\n")
    
    try:
        user = get_current_user()
        if user and user.user:
            console.print(f"[green]Email:[/green] {user.user.email}")
            console.print(f"[dim]User ID: {user.user.id}[/dim]\n")
        else:
            console.print("[yellow]⚠️  Not logged in[/yellow]\n")
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]\n")


@app.command()
def reset_password():
    """Send password reset email"""
    console.print("\n[bold cyan]🔑 Reset Password[/bold cyan]\n")
    
    email = console.input("[cyan]Email:[/cyan] ").strip()
    
    if not email:
        console.print("[red]❌ Email is required[/red]")
        return
    
    try:
        supabase.auth.reset_password_email(email)
        console.print(f"\n[green]✅ Password reset email sent![/green]")
        console.print(f"[dim]Check your email for the reset link.[/dim]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Failed to send reset email: {str(e)}[/red]\n")


if __name__ == "__main__":
    app()
