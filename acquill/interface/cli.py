"""
Acquill - Your AI Learning Companion CLI
Interactive chat + background git-diff monitoring
"""

import hashlib
from itertools import cycle
import os
import sys
import time
import threading
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from acquill.utils.api import process_message, process_diff, check_and_send_reminders, generate_weekly_digest, analyze_learning_patterns
from acquill.config.auth import signup as auth_signup, signin as auth_signin, signout as auth_signout, get_current_user, restore_session, supabase
from acquill.config import (
    config_exists,
    get_config,
    get_config_path,
    mask_credential,
    reset_config,
    run_init_wizard
)
from acquill.graphs.checkpoint import SessionLostError, init_session
from acquill.interface.ui_components import (
    render_startup_screen,
    render_welcome_panel,
    render_user_message,
    render_assistant_message,
    render_thinking_indicator,
    render_git_analysis,
    render_error_message,
    render_success_message,
    render_config_display,
    render_nudge_message,
    get_input_prompt
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
CHECK_INTERVAL = int(os.getenv("GIT_CHECK_INTERVAL", "300"))  # seconds
# Max diff characters sent to the model per analysis (Groq TPM limits).
MAX_DIFF_CHARS = int(os.getenv("GIT_DIFF_MAX_CHARS", "3000"))

# Shown when a check finds no uncommitted changes (used in order, then repeats)
NUDGE_MESSAGES = (
    "👀 No code changes yet — what are you working on? Start coding and I'll pick it up.",
    "🤔 Still nothing to review. Make an edit in your editor and I'll analyse it.",
    "💤 Quiet in here — no diff found. Time to write some code!",
    "🚀 Nothing to track yet. Save a change and I'll be right on it.",
)

# Shown when the diff itself contains emoji
EMOJI_NUDGE = "😄 Emojis in your code? I guess you're enjoying coding."


def _has_emoji(text):
    """Rough emoji check for diffs (pictographs and symbol blocks)."""
    return any(
        ord(ch) >= 0x1F000 or 0x2600 <= ord(ch) <= 0x27BF
        for ch in text
    )

# Make stdout/stderr safe for emoji on non-UTF-8 terminals (e.g. Windows cp1252)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Rich console for styled output
console = Console()

# Global flag to stop background thread when chat exits
_stop_background = threading.Event()

app = typer.Typer(
    name="Acquill",
    help="AI Learning Companion - Chat and automatic code learning tracker",
    add_completion=False
)


# ==================== Configuration Commands ====================

@app.command()
def init(
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Skip interactive prompts"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing configuration")
):
    """Initialize Acquill configuration"""
    success = run_init_wizard(interactive=not non_interactive, force=force)
    if not success:
        raise typer.Exit(code=1)


@app.command(name="config")
def config_cmd(
    action: str = typer.Argument(..., help="Action: show, update, or reset")
):
    """Manage Acquill configuration (show, update, reset)"""
    
    if action == "show":
        # Show current configuration with masked credentials
        if not config_exists():
            console.print("[yellow]⚠️  No configuration found. Run 'acquill init' first.[/yellow]\n")
            raise typer.Exit(code=1)
        
        try:
            config = get_config()
            
            # Mask credentials for display
            display_config = {
                'providers': {
                    'groq': {
                        'api_key': mask_credential(config['providers']['groq']['api_key']),
                        'model': config['providers']['groq']['model']
                    },
                    'jina': {
                        'api_key': mask_credential(config['providers']['jina']['api_key']),
                        'model': config['providers']['jina']['model']
                    }
                },
                'database': {
                    'supabase_url': config['database']['supabase_url'],
                    'supabase_key': mask_credential(config['database']['supabase_key']),
                    'checkpoint_db_url': mask_credential(config['database']['checkpoint_db_url'], visible_chars=10)
                }
            }
            
            render_config_display(console, display_config)
        
        except Exception as e:
            render_error_message(console, "Configuration Error", str(e))
            raise typer.Exit(code=1)
    
    elif action == "update":
        # Interactive update of credentials
        if not config_exists():
            console.print("[yellow]⚠️  No configuration found. Run 'acquill init' first.[/yellow]\n")
            raise typer.Exit(code=1)
        
        try:
            from acquill.config.validators import validate_groq_key, validate_jina_key
            config = get_config()
            
            console.print("\n[bold cyan]Update Acquill Configuration[/bold cyan]\n")
            console.print("What would you like to update?")
            console.print("  1. Groq API Key")
            console.print("  2. Jina AI API Key")
            console.print("  3. Database credentials")
            console.print("  0. Cancel\n")
            
            choice = console.input("[cyan]Enter choice (0-3):[/cyan] ").strip()
            
            if choice == "0":
                console.print("[dim]Update cancelled.[/dim]\n")
                return
            
            elif choice == "1":
                new_key = console.input("[cyan]New Groq API Key:[/cyan] ", password=True).strip()
                if new_key:
                    console.print("[dim]Validating...[/dim]")
                    valid, message = validate_groq_key(new_key)
                    if valid:
                        config["providers"]["groq"]["api_key"] = new_key
                        from acquill.config.settings import save_config
                        save_config(config)
                        render_success_message(console, "Groq API key updated", message)
                    else:
                        render_error_message(console, "Validation Failed", message)
            
            elif choice == "2":
                new_key = console.input("[cyan]New Jina AI API Key:[/cyan] ", password=True).strip()
                if new_key:
                    console.print("[dim]Validating...[/dim]")
                    valid, message = validate_jina_key(new_key)
                    if valid:
                        config["providers"]["jina"]["api_key"] = new_key
                        from acquill.config.settings import save_config
                        save_config(config)
                        render_success_message(console, "Jina AI API key updated", message)
                    else:
                        render_error_message(console, "Validation Failed", message)
            
            elif choice == "3":
                console.print("\n[bold]Update Database Credentials[/bold]\n")
                supabase_url = console.input(f"[cyan]Supabase URL [{config['database']['supabase_url']}]:[/cyan] ").strip()
                supabase_key = console.input("[cyan]Supabase Key:[/cyan] ", password=True).strip()
                checkpoint_url = console.input(f"[cyan]Checkpoint DB URL:[/cyan] ", password=True).strip()
                
                if supabase_url:
                    config["database"]["supabase_url"] = supabase_url
                if supabase_key:
                    config["database"]["supabase_key"] = supabase_key
                if checkpoint_url:
                    config["database"]["checkpoint_db_url"] = checkpoint_url
                
                from acquill.config.settings import save_config
                save_config(config)
                render_success_message(console, "Database credentials updated")
            
            else:
                console.print("[red]Invalid choice[/red]\n")
        
        except Exception as e:
            render_error_message(console, "Update Failed", str(e))
            raise typer.Exit(code=1)
    
    elif action == "reset":
        # Reset configuration
        if not config_exists():
            console.print("[yellow]⚠️  No configuration found.[/yellow]\n")
            return
        
        console.print("\n[bold red]⚠️  Reset Configuration[/bold red]\n")
        console.print("[yellow]This will delete your configuration file.[/yellow]")
        console.print("[dim]You can run 'acquill init' again to reconfigure.[/dim]\n")
        
        confirm = console.input("[cyan]Are you sure? Type 'yes' to confirm:[/cyan] ").strip()
        
        if confirm.lower() == "yes":
            reset_config()
            console.print(f"[green]✓ Configuration deleted: {get_config_path()}[/green]\n")
        else:
            console.print("[dim]Reset cancelled.[/dim]\n")
    
    else:
        console.print(f"[red]✗ Unknown action '{action}'. Use: show, update, or reset[/red]\n")
        raise typer.Exit(code=1)


# ==================== Main Commands ====================


def _require_session():
    """Restore the saved login into the in-memory client, or exit cleanly."""
    if not restore_session():
        console.print("[yellow]Not logged in. Run `acquill login` first.[/yellow]")
        raise typer.Exit()


def background_git_checker():
    """
    Background thread that periodically checks git diff and processes changes.
    Runs every CHECK_INTERVAL seconds until _stop_background is set.
    """
    # Silently start monitoring (no message on startup)
    
    last_seen = {}
    idle_ticks = 0
    nudges = cycle(NUDGE_MESSAGES)
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
                encoding='utf-8',
                errors='replace',
                cwd=os.getcwd()
            )
            
            diff_output = result.stdout.strip() if result.stdout else ""
            
            # Nothing changed: remind the user (first check, then every 4th)
            if not diff_output:
                if idle_ticks % 4 == 0:
                    render_nudge_message(console, next(nudges))
                idle_ticks += 1
                continue
            idle_ticks = 0
            
            # Get changed files
            files_result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=os.getcwd()
            )
            
            changed_files = files_result.stdout.strip().split("\n") if files_result.stdout else []
            
            # Filter out empty filenames
            changed_files = [f for f in changed_files if f]
            
            if not changed_files:
                continue
            
            # Check for emoji in the full diff
            if _has_emoji(diff_output):
                render_nudge_message(console, EMOJI_NUDGE)
            
            # Create a digest of the entire diff to avoid re-analyzing same changes
            diff_digest = hashlib.sha1(diff_output.encode("utf-8", "replace")).hexdigest()
            
            # Skip if we've already seen this exact diff
            if last_seen.get("__all__") == diff_digest:
                continue
            
            # Build a summary of changed files
            files_summary = ", ".join(changed_files[:5])  # Show max 5 files
            if len(changed_files) > 5:
                files_summary += f" and {len(changed_files) - 5} more"
            
            # Process the entire diff as one analysis (with error handling)
            try:
                # Stay inside the model's token limits: analyse the head only.
                trimmed = diff_output
                if len(trimmed) > MAX_DIFF_CHARS:
                    trimmed = trimmed[:MAX_DIFF_CHARS] + "\n... [diff truncated to fit the model]"
                response = process_diff(trimmed, files_summary)
                last_seen["__all__"] = diff_digest
                
                # Display single analysis for all changes using new UI
                if response.get("reply"):
                    render_git_analysis(
                        console,
                        files_changed=len(changed_files),
                        files_summary=files_summary,
                        topic=response.get('topic', 'unknown'),
                        event_type=response.get('event_type', 'unknown'),
                        analysis=response.get('reply', 'No analysis')
                    )
            except Exception as e:
                # Friendly message instead of showing the error
                render_nudge_message(
                    console, 
                    "I noticed some code changes but had trouble analyzing them. "
                    "No worries though—keep coding! Your placement prep is what matters most. 🚀"
                )
                last_seen["__all__"] = diff_digest  # Mark as seen to avoid re-trying
        except SessionLostError:
            # Session is gone for good - stop monitoring quietly.
            _stop_background.set()
            return

        except Exception as e:
            # Silently continue on errors
            continue


@app.command()
def chat(
    git: bool = typer.Option(None, "--git/--no-git", help="Auto-analyse code changes in the background (default: on, per config)")
):
    """
    Start interactive chat with Acquill.
    Also starts background git-diff monitoring in a separate thread (unless --no-git).
    """
    _require_session()
    init_session()  # fresh thread for this run + clear leftover threads

    # Git monitoring: CLI flag wins, otherwise the saved config (default on).
    try:
        from acquill.config import get_config
        git_enabled = get_config().get("git_monitoring", True)
    except Exception:
        git_enabled = True
    if git is not None:
        git_enabled = git

    # Display startup screen
    render_startup_screen(console)
    time.sleep(1)  # Brief pause for effect
    console.clear()
    
    # Welcome panel
    render_welcome_panel(console, CHECK_INTERVAL, git_enabled=git_enabled)

    # Start background thread (only when git monitoring is enabled)
    _stop_background.clear()
    if git_enabled:
        bg_thread = threading.Thread(target=background_git_checker, daemon=True)
        bg_thread.start()
    
    # Main chat loop
    while True:
        try:
            # Get user input with styled prompt
            user_input = console.input(get_input_prompt()).strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("\n[yellow]👋 See you next time! Keep learning![/yellow]\n")
                _stop_background.set()  # Stop background thread
                break
            
            # Show user message
            render_user_message(console, user_input)
            
            # Show thinking indicator
            render_thinking_indicator(console)
            
            # Process through orchestration
            response = process_message(user_input)
            
            # Clear thinking indicator line (move cursor up and clear)
            console.print("\033[A\033[K", end="")
            
            # Display reply
            if response.get("error"):
                render_error_message(console, "Processing Error", response['error'])
            elif response.get("reply"):
                render_assistant_message(console, response['reply'])
            else:
                console.print("[dim]Message received (no reply generated)[/dim]\n")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Interrupted. Goodbye![/yellow]\n")
            _stop_background.set()
            break
        except SessionLostError as e:
            render_error_message(console, "Session Lost", str(e))
            _stop_background.set()
            break
        except Exception as e:
            render_error_message(console, "Unexpected Error", str(e))


@app.command()
def remind():
    """Check for overdue review reminders"""
    _require_session()

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
    _require_session()

    console.print(f"\n📊 [bold]Generating {days}-day digest...[/bold]\n")
    
    digest_text = generate_weekly_digest(days)
    
    if digest_text:
        console.print(Panel(Markdown(digest_text), border_style="blue"))
    else:
        console.print("[yellow]No learning activity found in this period.[/yellow]\n")


@app.command()
def patterns():
    """Analyze recurring learning patterns"""
    _require_session()

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
        render_error_message(console, "Email is required")
        return
    
    password = console.input("[cyan]Password:[/cyan] ", password=True).strip()
    
    if not password:
        render_error_message(console, "Password is required")
        return
    
    try:
        result = auth_signup(email, password)
        render_success_message(
            console, 
            "Account created successfully!",
            "Check your email to verify your account."
        )
    except Exception as e:
        render_error_message(console, "Signup failed", str(e))


@app.command()
def login():
    """Login to your Acquill account"""
    console.print("\n[bold cyan]🔐 Login to Acquill[/bold cyan]\n")
    
    email = console.input("[cyan]Email:[/cyan] ").strip()
    
    if not email:
        render_error_message(console, "Email is required")
        return
    
    password = console.input("[cyan]Password:[/cyan] ", password=True).strip()
    
    if not password:
        render_error_message(console, "Password is required")
        return
    
    try:
        result = auth_signin(email, password)
        render_success_message(
            console,
            "Login successful!",
            "Welcome back! You can now use all Acquill features."
        )
    except Exception as e:
        render_error_message(console, "Login failed", str(e))


@app.command()
def logout():
    """Logout from your Acquill account"""
    console.print("\n[bold cyan]👋 Logout from Acquill[/bold cyan]\n")
    
    try:
        auth_signout()
        render_success_message(console, "Logged out successfully")
    except Exception as e:
        render_error_message(console, "Logout failed", str(e))


@app.command()
def whoami():
    """Show current logged in user"""
    _require_session()
    console.print("\n[bold cyan]👤 Current User[/bold cyan]\n")
    
    try:
        user = get_current_user()
        if user and user.user:
            console.print(f"[green]Email:[/green] {user.user.email}")
            console.print(f"[dim]User ID: {user.user.id}[/dim]\n")
        else:
            console.print("[yellow]⚠️  Not logged in[/yellow]\n")
    except Exception as e:
        render_error_message(console, "Error retrieving user info", str(e))


@app.command()
def reset_password():
    """Send password reset email"""
    console.print("\n[bold cyan]🔑 Reset Password[/bold cyan]\n")
    
    email = console.input("[cyan]Email:[/cyan] ").strip()
    
    if not email:
        render_error_message(console, "Email is required")
        return
    
    try:
        supabase.auth.reset_password_email(email)
        render_success_message(
            console,
            "Password reset email sent!",
            "Check your email for the reset link."
        )
    except Exception as e:
        render_error_message(console, "Failed to send reset email", str(e))


if __name__ == "__main__":
    app()
