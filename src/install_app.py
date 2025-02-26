import os
from logger import Logger
import json
from pathlib import Path
import subprocess

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
    
    
def install_preset(preset_name: str) -> None:
    try:
        with open(preset_path_dir / preset_name, 'r') as file:
            preset_data = json.load(file)
            
        install_list = preset_data.get("Install", [])
        
        for app in install_list:
            winget_id = app.get("winget")
            choco_id = app.get("choco")
            
            # Install using winget
            if winget_id:
                try:
                    subprocess.run(['winget', 'install', '--id', winget_id, '-e'], check=True)
                except subprocess.CalledProcessError as e:
                    log.log_error(f"Error installing {winget_id} with winget: {e}")
            
            # Install using chocolatey
            if choco_id:
                try:
                    subprocess.run(['choco', 'install', choco_id, '-y'], check=True)
                except subprocess.CalledProcessError as e:
                    log.log_error(f"Error installing {choco_id} with chocolatey: {e}")
                    
    except Exception as e:
        log.log_error(f"Error installing preset '{preset_name}': {e}")

if __name__ == "__main__":
    preset_filename = "Gaming.json"
    
    if not presets_in_list(preset_filename):
        log.log_error(f"Error: Preset '{preset_filename}' not found in the list of presets.")
        print(f"Error: Preset '{preset_filename}' not found in the list of presets.")
    else:
        install_preset(preset_filename)