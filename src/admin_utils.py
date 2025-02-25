import ctypes
import sys
import functools
from typing import Callable, Any, TypeVar, cast
from pathlib import Path
from logger import Logger

# Create a logger instance
log = Logger()

# Type variable for generic function type
F = TypeVar('F', bound=Callable[..., Any])

def is_admin() -> bool:
    """
    Check if the current process has administrator privileges.
    
    Returns:
        bool: True if running with admin privileges, False otherwise
    """
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception as e:
        log.log_error(f"Error checking admin privileges: {e}")
        return False

def restart_as_admin() -> None:
    """
    Restart the current script with administrator privileges.
    This function will terminate the current process.
    """
    try:
        script = sys.argv[0]
        params = ' '.join(sys.argv[1:])
        log.log_info("Restarting with administrator privileges...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit(0)
    except Exception as e:
        log.log_error(f"Error restarting as admin: {e}")
        sys.exit(1)

def require_admin(func: F) -> F:
    """
    Decorator to ensure a function runs with administrator privileges.
    
    Args:
        func: The function requiring admin privileges
        
    Returns:
        Function that will run with admin privileges or exit
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not is_admin():
            log.log_warning(f"Function {func.__name__} requires administrator privileges.")
            restart_as_admin()
        return func(*args, **kwargs)
    return cast(F, wrapper)

def confirm_action(prompt: str = "Do you want to continue?") -> bool:
    """
    Ask for user confirmation before proceeding with an action.
    
    Args:
        prompt: The message to display to the user
        
    Returns:
        bool: True if user confirms, False otherwise
    """
    response = input(f"{prompt} (y/n): ").strip().lower()
    return response == 'y' or response == 'yes'

def safe_system_restart(delay_seconds: int = 60) -> None:
    """
    Safely restart the system with a delay and user notification.
    
    Args:
        delay_seconds: Number of seconds to wait before restarting
    """
    if confirm_action("System needs to restart to apply changes. Restart now?"):
        try:
            import subprocess
            log.log_info(f"System will restart in {delay_seconds} seconds")
            subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)], check=True)
        except subprocess.SubprocessError as e:
            log.log_error(f"Error during restart command: {e}")
            print("Failed to initiate system restart. Please restart manually.")
    else:
        log.log_info("System restart postponed by user")
        print("Please restart your system manually to complete the installation.")