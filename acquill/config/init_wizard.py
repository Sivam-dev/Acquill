"""
Interactive initialization wizard for Acquill
Guides users through first-time setup
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .settings import (
    config_exists,
    save_config,
    migrate_from_env,
    get_config_path
)
from .validators import (
    validate_groq_key,
    validate_jina_key,
    validate_supabase,
    validate_checkpoint_db_url
)

console = Console()

# Simple ACQUILL branding for wizard
WIZARD_LOGO = """
   ___   _____  ____  __  __ _____ _      _     
  / _ \ / ____|/ __ \|  \/  |_   _| |    | |    
 / /_\ | |  __| |  | | \  / | | | | |    | |    
|  _  || | |_ | |  | | |\/| | | | | |    | |    
| | | || |__| | |__| | |  | |_| |_| |____| |____
|_| |_| \_____|\___\_\_|  |_|_____|______|______|
"""


def _prompt_with_default(prompt: str, default: str = "", password: bool = False) -> str:
    """Prompt user with optional default value"""
    if default and not password:
        display_prompt = f"{prompt} [{default}]: "
    else:
        display_prompt = f"{prompt}: "
    
    if password:
        value = console.input(f"[cyan]{display_prompt}[/cyan]", password=True).strip()
    else:
        value = console.input(f"[cyan]{display_prompt}[/cyan]").strip()
    
    return value if value else default


def _check_env_file() -> bool:
    """Check if .env file exists in current directory"""
    return Path(".env").exists()


def run_init_wizard(interactive: bool = True, force: bool = False) -> bool:
    """
    Run the interactive initialization wizard.
    
    Args:
        interactive: If False, use non-interactive mode (read from env)
        force: If True, overwrite existing config without confirmation
    
    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    console.print()
    
    # Display logo
    logo_text = Text()
    for line in WIZARD_LOGO.strip().split('\n'):
        logo_text.append(line + "\n", style="bright_cyan")
    console.print(logo_text, justify="center")
    
    console.print()
    console.print("[bold cyan]Initialization Wizard[/bold cyan]", justify="center")
    console.print("[dim]Your AI companion with persistent memory[/dim]", justify="center")
    console.print()
    
    # Check if config already exists
    if config_exists() and not force:
        console.print("[yellow]⚠️  Configuration already exists.[/yellow]")
        reconfigure = console.input("[cyan]Do you want to reconfigure? (y/N):[/cyan] ").strip().lower()
        
        if reconfigure not in ['y', 'yes']:
            console.print("[dim]Initialization cancelled.[/dim]\n")
            return False
        
        console.print()
    
    # Check for existing .env file
    env_exists = _check_env_file()
    import_from_env = False
    
    if env_exists and interactive:
        console.print("[green]✓[/green] Found existing .env file")
        import_choice = console.input("[cyan]Import credentials from .env? (Y/n):[/cyan] ").strip().lower()
        import_from_env = import_choice not in ['n', 'no']
        console.print()
    
    # Start building config
    config = {
        "version": "1.0",
        "providers": {
            "groq": {"model": "openai/gpt-oss-20b"},
            "jina": {"model": "jina-embeddings-v2-base-en"}
        },
        "database": {},
        "git_check_interval": 300
    }
    
    # Import from .env if requested
    if import_from_env:
        env_config = migrate_from_env()
        config["providers"]["groq"]["api_key"] = env_config["providers"]["groq"]["api_key"]
        config["providers"]["jina"]["api_key"] = env_config["providers"]["jina"]["api_key"]
        config["database"] = env_config["database"]
        config["git_check_interval"] = env_config["git_check_interval"]
    
    # Non-interactive mode: use environment variables
    if not interactive:
        if not import_from_env:
            env_config = migrate_from_env()
            config = env_config
        
        # Validate all credentials
        console.print("[dim]Validating credentials...[/dim]\n")
        
        groq_valid, groq_msg = validate_groq_key(config["providers"]["groq"]["api_key"])
        if not groq_valid:
            console.print(f"[red]✗ {groq_msg}[/red]\n")
            return False
        
        jina_valid, jina_msg = validate_jina_key(config["providers"]["jina"]["api_key"])
        if not jina_valid:
            console.print(f"[red]✗ {jina_msg}[/red]\n")
            return False
        
        save_config(config)
        console.print(f"[green]✓ Configuration saved to {get_config_path()}[/green]\n")
        return True
    
    # Interactive mode: prompt for each credential
    console.print("[bold]Step 1: Groq API Configuration[/bold]")
    console.print("[dim]Groq provides the LLM for chat and analysis[/dim]\n")
    
    while True:
        groq_key = _prompt_with_default(
            "Groq API Key",
            default=config["providers"]["groq"].get("api_key", ""),
            password=True
        )
        
        if not groq_key:
            console.print("[red]✗ Groq API key is required[/red]\n")
            continue
        
        console.print("[dim]Validating Groq API key...[/dim]")
        valid, message = validate_groq_key(groq_key)
        
        if valid:
            console.print(f"[green]✓ {message}[/green]\n")
            config["providers"]["groq"]["api_key"] = groq_key
            break
        else:
            console.print(f"[red]✗ {message}[/red]")
            retry = console.input("[cyan]Try again? (Y/n):[/cyan] ").strip().lower()
            if retry in ['n', 'no']:
                console.print("[yellow]Initialization cancelled.[/yellow]\n")
                return False
            console.print()
    
    console.print("[bold]Step 2: Jina AI API Configuration[/bold]")
    console.print("[dim]Jina AI provides embeddings for semantic search[/dim]\n")
    
    while True:
        jina_key = _prompt_with_default(
            "Jina AI API Key",
            default=config["providers"]["jina"].get("api_key", ""),
            password=True
        )
        
        if not jina_key:
            console.print("[red]✗ Jina AI API key is required[/red]\n")
            continue
        
        console.print("[dim]Validating Jina AI API key...[/dim]")
        valid, message = validate_jina_key(jina_key)
        
        if valid:
            console.print(f"[green]✓ {message}[/green]\n")
            config["providers"]["jina"]["api_key"] = jina_key
            break
        else:
            console.print(f"[red]✗ {message}[/red]")
            retry = console.input("[cyan]Try again? (Y/n):[/cyan] ").strip().lower()
            if retry in ['n', 'no']:
                console.print("[yellow]Initialization cancelled.[/yellow]\n")
                return False
            console.print()
    
    console.print("[bold]Step 3: Database Configuration[/bold]")
    console.print("[dim]Supabase stores your learning history and progress[/dim]\n")
    
    while True:
        supabase_url = _prompt_with_default(
            "Supabase URL",
            default=config["database"].get("supabase_url", "")
        )
        
        supabase_key = _prompt_with_default(
            "Supabase Key",
            default=config["database"].get("supabase_key", ""),
            password=True
        )
        
        if not supabase_url or not supabase_key:
            console.print("[red]✗ Both Supabase URL and key are required[/red]\n")
            continue
        
        console.print("[dim]Validating Supabase credentials...[/dim]")
        valid, message = validate_supabase(supabase_url, supabase_key)
        
        if valid:
            console.print(f"[green]✓ {message}[/green]\n")
            config["database"]["supabase_url"] = supabase_url
            config["database"]["supabase_key"] = supabase_key
            break
        else:
            console.print(f"[red]✗ {message}[/red]")
            retry = console.input("[cyan]Try again? (Y/n):[/cyan] ").strip().lower()
            if retry in ['n', 'no']:
                console.print("[yellow]Initialization cancelled.[/yellow]\n")
                return False
            console.print()
    
    console.print("[bold]Step 4: Checkpoint Database Configuration[/bold]")
    console.print("[dim]PostgreSQL URL for conversation persistence[/dim]\n")
    
    while True:
        checkpoint_url = _prompt_with_default(
            "Checkpoint DB URL",
            default=config["database"].get("checkpoint_db_url", "")
        )
        
        if not checkpoint_url:
            console.print("[red]✗ Checkpoint DB URL is required[/red]\n")
            continue
        
        console.print("[dim]Validating PostgreSQL URL...[/dim]")
        valid, message = validate_checkpoint_db_url(checkpoint_url)
        
        if valid:
            console.print(f"[green]✓ {message}[/green]\n")
            config["database"]["checkpoint_db_url"] = checkpoint_url
            break
        else:
            console.print(f"[red]✗ {message}[/red]")
            retry = console.input("[cyan]Try again? (Y/n):[/cyan] ").strip().lower()
            if retry in ['n', 'no']:
                console.print("[yellow]Initialization cancelled.[/yellow]\n")
                return False
            console.print()
    
    # Save configuration
    try:
        save_config(config)
        console.print(Panel.fit(
            f"[green]✓ Configuration saved successfully![/green]\n\n"
            f"[dim]Location: {get_config_path()}[/dim]\n\n"
            f"[cyan]Next steps:[/cyan]\n"
            f"  1. Run [bold]acquill login[/bold] to authenticate\n"
            f"  2. Run [bold]acquill chat[/bold] to start learning\n\n"
            f"[dim]Note: Your .env file was not modified.[/dim]",
            border_style="green",
            title="🎉 Setup Complete"
        ))
        return True
    
    except Exception as e:
        console.print(f"\n[red]✗ Failed to save configuration: {e}[/red]\n")
        return False
