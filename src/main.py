import os
from pathlib import Path
from PyQt5_UI import run_app, SubWindow
from app import App
from pathlib import Path
from logger import Logger
import ctypes
import sys

base_dir = Path(__file__).resolve().parent.parent
presets_dir = base_dir / "presets"

if not presets_dir.exists():
    os.makedirs(presets_dir, exist_ok=True)


app = App(presets_dir)
log = Logger()


def is_running_as_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0   
    except Exception as e:
        log.log_error(f"Error checking admin privileges: {e}")
        return False
    
def restart_as_admin():
    try:
        script = sys.argv[0]
        params = ' '.join(sys.argv[1:])
        log.log_info("Restarting with admin privileges...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit()
    except Exception as e:
        log.log_error(f"Error restarting as admin: {e}")

def main():
    if not is_running_as_admin():
        log.log_info("Program is not running as admin. Restarting with admin rights...")
        restart_as_admin()
        return

    try:
        exit_code = run_app(app)  
        sys.exit(exit_code)
    except Exception as e:
        log.log_error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()