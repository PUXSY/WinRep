import os
import json
import subprocess
from logger import Logger
from pathlib import Path

current_dir = Path(__file__).parent
log = Logger(current_dir.parent / "logs")
preset_path_dir = current_dir.parent / "presets"

def get_presets_list() -> list:
    try:
        if not preset_path_dir.exists() or not preset_path_dir.is_dir():
            log.log_error(f"Error: Directory '{preset_path_dir}' does not exist or is not a directory.")
            print(f"Error: Directory '{preset_path_dir}' does not exist or is not a directory.")
            return []
        return [file for file in os.listdir(preset_path_dir) if os.path.isfile(os.path.join(preset_path_dir, file))]
    except Exception as e:
        log.log_error(f"Error accessing preset directory: {e}")
        return [] 

list_of_presets: list[str] = get_presets_list()

def presets_in_list(preset_name: str) -> bool:
    return preset_name in list_of_presets

def get_preset_data(preset_name: str) -> dict:
    if not presets_in_list(preset_name):
        log.log_error(f"Error: Preset '{preset_name}' not found in the list of presets.")
        print(f"Error: Preset '{preset_name}' not found in the list of presets.")
        return None

    try:
        with open(os.path.join(preset_path_dir, preset_name), 'r') as file:
            preset_data = json.load(file)
            return preset_data
    except FileNotFoundError:
        log.log_error(f"Error: File '{preset_path_dir}' not found.")
        return None

def install_with_package_manager(package_id: str, manager: str) -> bool:
    """Install a package using the specified package manager (winget or chocolatey)."""
    commands = {
        "winget": ['winget', 'install', '--id', package_id, '-e', '--accept-source-agreements', '--accept-package-agreements'],
        "choco": ['choco', 'install', package_id, '-y']
    }
    
    if manager not in commands:
        log.log_error(f"Unsupported package manager: {manager}")
        return False
    
    try:
        process = subprocess.Popen(
            commands[manager],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            log.log_info(f"Successfully installed {package_id} using {manager}")
            return True
        else:
            log.log_error(f"Error installing {package_id} with {manager}: {stderr}")
            return False
    except Exception as e:
        log.log_error(f"Error installing {package_id} with {manager}: {e}")
        return False
    
def install_preset(preset_name: str) -> bool:
    """Install applications from the specified preset."""
    try:
        # Convert preset_name to a Path object
        preset_path = Path(preset_name)
        
        # Check if the file exists directly
        if not preset_path.exists():
            # If not, try checking if it's in the presets directory
            preset_path = preset_path_dir / preset_name
            if not preset_path.exists():
                log.log_error(f"Error: Preset file not found at '{preset_path}'")
                return False
        
        # Load and parse preset file
        try:
            with open(preset_path, 'r', encoding='utf-8') as file:
                preset_data = json.load(file)
        except json.JSONDecodeError as e:
            log.log_error(f"Invalid JSON in preset file '{preset_path}': {e}")
            return False
        
        # Get list of applications to install
        install_list = preset_data.get("Install", [])
        if not install_list:
            log.log_warning(f"No applications to install in preset '{preset_path.name}'")
            return True
        
        # Install each application
        for app in install_list:
            app_name = app.get("name", "Unknown application")
            winget_id = app.get("winget")
            choco_id = app.get("choco")
            
            display_name = app_name if app_name != "Unknown application" else winget_id or choco_id
            log.log_info(f"Installing {display_name}...")
            
            # Try winget first if available
            if winget_id:
                try:
                    process = subprocess.Popen(
                        ['winget', 'install', '--id', winget_id, '-e', '--accept-source-agreements', '--accept-package-agreements'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        log.log_info(f"Successfully installed {winget_id} using winget")
                        continue  # Skip chocolatey if winget succeeds
                    else:
                        log.log_error(f"Error installing {winget_id} with winget: {stderr}")
                except Exception as e:
                    log.log_error(f"Error installing {winget_id} with winget: {e}")
            
            # Try chocolatey if winget failed or wasn't available
            if choco_id:
                try:
                    process = subprocess.Popen(
                        ['choco', 'install', choco_id, '-y'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        log.log_info(f"Successfully installed {choco_id} using chocolatey")
                    else:
                        log.log_error(f"Error installing {choco_id} with chocolatey: {stderr}")
                except Exception as e:
                    log.log_error(f"Error installing {choco_id} with chocolatey: {e}")
        
        return True

    except Exception as e:
        log.log_error(f"Error installing preset '{preset_name}': {e}")
        return False

if __name__ == "__main__":
    preset_filename = "Gaming.json"
    
    if not presets_in_list(preset_filename):
        log.log_error(f"Error: Preset '{preset_filename}' not found in the list of presets.")
        print(f"Error: Preset '{preset_filename}' not found in the list of presets.")
    else:
        install_preset(preset_filename)