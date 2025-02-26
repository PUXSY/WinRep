import os
from logger import Logger
import json
import subprocess
from pathlib import Path
from debloat_windows import *
from install_app import install_preset

log = Logger()
class App:
    def __init__(self, presets_path_dir:Path = Path("./../presets")) -> None:
        self.preset_path_dir: Path = presets_path_dir
        self.list_of_presets: list = self.Get_presets_list()
    
    def __enter__(self):
        """Context manager entry point."""
        self.list_of_presets: list = self.Get_presets_list()
        return self
    
    def Get_presets_list(self) -> list:
        try:
            if not self.preset_path_dir.exists() or not self.preset_path_dir.is_dir():
                log.log_error(f"Error: Directory '{self.preset_path_dir}' does not exist. Or is not a directory.")
                return None
            return [file for file in os.listdir(self.preset_path_dir) if os.path.isfile(os.path.join(self.preset_path_dir, file))]
        except FileNotFoundError:
            log.log_error(f"Error: File '{self.preset_path_dir}' not found.")
            return None
    
    def presets_in_list(self, preset_name:str ) -> bool:
        try:
            return preset_name in self.list_of_presets
        except FileNotFoundError:
            log.log_error(f"Error: File '{self.preset_path_dir}' not found.")
            return False
    
    def run_preset_test(self, preset_name:str ) -> str:
        try:
            if not self.presets_in_list(preset_name):
                log.log_error(f"Error: Preset '{preset_name}' not found in the list of presets.")
                print(f"Error: Preset '{preset_name}' not found in the list of presets.")
                return None

                
            with open(os.path.join(self.preset_path_dir, preset_name), 'r') as file:
                    preset_data = json.load(file)
                    print(preset_data)
                    return preset_data
            
        except FileNotFoundError:
            log.log_error(f"Error: File '{self.preset_path_dir}' not found.")
            return None
        
    def run_preset(self, preset_name:str ) -> None:
        try:
            if not self.presets_in_list(preset_name):
                log.log_error(f"Error: Preset '{preset_name}' not found in the list of presets.")
                print(f"Error: Preset '{preset_name}' not found in the list of presets.")
                return None
    
            # Load preset data to verify it before proceeding
            preset_data = self.run_preset_test(preset_name)
            if preset_data is None:
                log.log_error(f"Error: Failed to load preset data for '{preset_name}'")
                return None
                
            try:
                install_preset(preset_name)
            except Exception as e:
                log.log_error(f"Error installing preset '{preset_name}': {e}")
                return None
            
        except FileNotFoundError:
            log.log_error(f"Error: File '{self.preset_path_dir}' not found.")
            return None
    
        try:
            apply_registry_changes()
            run_winconfig()
        except Exception as e:
            log.log_error(f"Error: Failed to run debloat_windows: {e}")
            return None
