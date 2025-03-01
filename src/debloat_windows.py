""" Import necessary modules for the program to work """
import sys
import ctypes
import os
import tempfile
import subprocess
import requests
import winreg
from logger import Logger
from pathlib import Path

print("Starting debloat_windows...")

""" Define the base directory for the program """
base_dir = Path(__file__).resolve().parent.parent
logs_dir = base_dir / "logs"
log = Logger(logs_dir)

print("debloat_windows started successfully")

""" Utility function to check if the program is running as administrator """
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

""" If the program is not running as administrator, attempt to elevate """
if not is_running_as_admin():
    log.log_info("Program is not running as admin. Restarting with admin rights...")
    restart_as_admin()

print("Checking admin privileges...")

""" Apply modifications done via the Windows registry """
def apply_registry_changes():
    log.log_and_print("Applying registry changes...", "info")
    try:
        registry_modifications = [
            # Visual changes
            #(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "TaskbarAl", winreg.REG_DWORD, 0), # Align taskbar to the left
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "AppsUseLightTheme", winreg.REG_DWORD, 0), # Set Windows to dark theme
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "SystemUsesLightTheme", winreg.REG_DWORD, 0), # Set Windows to dark theme
            #(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Accent", "AccentColorMenu", winreg.REG_DWORD, 1), # Makes accent color the color of the taskbar and start menu (1)  --.
            #(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\Personalize", "ColorPrevalence", winreg.REG_DWORD, 1), # Makes accent color the color of the taskbar and start menu (2)   |-- These are redundant. I know
            #(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\DWM", "AccentColorInStartAndTaskbar", winreg.REG_DWORD, 1), # Makes accent color the color of the taskbar and start menu (3)                   --'
            #(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Accent", "AccentPalette", winreg.REG_BINARY, b"\x00" * 32), # Makes the taskbar black
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR", "AppCaptureEnabled", winreg.REG_DWORD, 0), #Fix the  Get an app for 'ms-gamingoverlay' popup
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\PolicyManager\\default\\ApplicationManagement\\AllowGameDVR", "Value", winreg.REG_DWORD, 0), # Disable Game DVR (Reduces FPS Drops)
            (winreg.HKEY_CURRENT_USER, r"Control Panel\\Desktop", "MenuShowDelay", winreg.REG_SZ, "0"),# Reduce menu delay for snappier UI
            (winreg.HKEY_CURRENT_USER, r"Control Panel\\Desktop\\WindowMetrics", "MinAnimate", winreg.REG_DWORD, 0),# Disable minimize/maximize animations
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "ExtendedUIHoverTime", winreg.REG_DWORD, 1),# Reduce hover time for tooltips and UI elements
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "HideFileExt", winreg.REG_DWORD, 0),# Show file extensions in Explorer (useful for security and organization)
        ]
        for root_key, key_path, value_name, value_type, value in registry_modifications:
            try:
                with winreg.CreateKeyEx(root_key, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, value_name, 0, value_type, value)
                    log.log_and_print(f"Applied {value_name} to {key_path}", "info")
            except Exception as e:
                log.log_and_print(f"Failed to modify {value_name} in {key_path}: {e}", "error")
        log.log_and_print("Registry changes applied successfully.", "info")
        subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["start", "explorer.exe"], shell=True)
        log.log_and_print("Explorer restarted to apply registry changes.", "info")
        run_edge_vanisher()
        log.log_and_print("Edge Vanisher started successfully", "info")
        
    except Exception as e:
        log.log_and_print(f"Error applying registry changes: {e}", "error")



""" Run a script to remove Edge, and prevent reinstallation """
def run_edge_vanisher():
    log.log_and_print("Starting Edge Vanisher script execution...", "info")
    try:
        script_url = "https://code.ravendevteam.org/talon/edge_vanisher.ps1"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, "edge_vanisher.ps1")
        log.log_and_print(f"Attempting to download Edge Vanisher script from: {script_url}", "info")
        log.log_and_print(f"Target script path: {script_path}", "info")
        
        response = requests.get(script_url)
        log.log_and_print(f"Download response status code: {response.status_code}", "info")
        
        with open(script_path, "wb") as file:
            file.write(response.content)
        log.log_and_print("Edge Vanisher script successfully saved to disk", "info")
        
        powershell_command = (
            f"Set-ExecutionPolicy Bypass -Scope Process -Force; "
            f"& '{script_path}'; exit" 
        )
        log.log_and_print(f"Executing PowerShell command: {powershell_command}", "info")
        
        process = subprocess.run(
            ["powershell", "-Command", powershell_command],
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            log.log_and_print("Edge Vanisher execution completed successfully", "info")
            log.log_and_print(f"Process output: {process.stdout}", "info")
            run_oouninstall()
        else:
            log.log_and_print(f"Edge Vanisher execution failed with return code: {process.returncode}", "error")
            log.log_and_print(f"Process error: {process.stderr}", "error")
            run_oouninstall()
            
    except requests.exceptions.RequestException as e:
        log.log_and_print(f"Network error during Edge Vanisher script download: {str(e)}", "error")
        run_oouninstall()
    except IOError as e:
        log.log_and_print(f"File I/O error while saving Edge Vanisher script: {str(e)}", "error")
        run_oouninstall()
    except Exception as e:
        log.log_and_print(f"Unexpected error during Edge Vanisher execution: {str(e)}", "error")
        run_oouninstall()



""" Run a script to remove OneDrive and Outlook """
def run_oouninstall():
    log.log_and_print("Starting Office Online uninstallation process...", "info")
    try:
        script_url = "https://code.ravendevteam.org/talon/uninstall_oo.ps1"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, "uninstall_oo.ps1")
        log.log_and_print(f"Attempting to download OO uninstall script from: {script_url}", "info")
        log.log_and_print(f"Target script path: {script_path}", "info")
        
        response = requests.get(script_url)
        log.log_and_print(f"Download response status code: {response.status_code}", "info")
        
        with open(script_path, "wb") as file:
            file.write(response.content)
        log.log_and_print("OO uninstall script successfully saved to disk", "info")
        
        powershell_command = f"Set-ExecutionPolicy Bypass -Scope Process -Force; & '{script_path}'"
        log.log_and_print(f"Executing PowerShell command: {powershell_command}", "info")
        
        process = subprocess.run(
            ["powershell", "-Command", powershell_command],
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            log.log_and_print("Office Online uninstallation completed successfully", "info")
            log.log_and_print(f"Process stdout: {process.stdout}", "info")
            run_tweaks()
        else:
            log.log_and_print(f"Office Online uninstallation failed with return code: {process.returncode}", "error")
            log.log_and_print(f"Process stderr: {process.stderr}", "error")
            log.log_and_print(f"Process stdout: {process.stdout}", "info")
            run_tweaks()
            
    except Exception as e:
        log.log_and_print(f"Unexpected error during OO uninstallation: {str(e)}", "error")
        run_tweaks()



""" Run ChrisTitusTech's WinUtil to debloat the system (Thanks Chris, you're a legend!) """
def run_tweaks():
    if not is_running_as_admin():
        log.log_and_print("Must be run as an administrator.", "error")
        restart_as_admin()

    try:
        json_path = os.path.join(sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(__file__), "barebones.json")

        log.log_and_print(f"Using config from: {json_path}", "info")

        temp_dir = tempfile.gettempdir()
        log.log_file = os.path.join(temp_dir, "cttwinutil.log.log")

        command = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"$ErrorActionPreference = 'SilentlyContinue'; " +
            f"iex \"& {{ $(irm christitus.com/win) }} -Config '{json_path}' -Run\" *>&1 | " +
            "Tee-Object -FilePath '" + log.log_file + "'"
        ]
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        while True:
            output = process.stdout.readline()
            if output:
                output = output.strip()
                log.log_and_print(f"CTT Output: {output}", "info")
                if "Tweaks are Finished" in output:
                    log.log_and_print("Detected completion message. Terminating...", "info")

                    subprocess.run(
                        ["powershell", "-Command", "Stop-Process -Name powershell -Force"],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )

                    run_winconfig()
                    os._exit(0)
            
            if process.poll() is not None:
                run_winconfig()
                os._exit(1)

        return False

    except Exception as e:
        log.log_and_print(f"Error: {str(e)}", "error")
        run_winconfig()
        os._exit(1)



""" Run Raphi's Win11Debloat script to further debloat the system (Thanks Raphire!) """
def run_winconfig():
    log.log_and_print("Starting Windows configuration process...", "info")
    try:
        script_url = "https://win11debloat.raphi.re/"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, "Win11Debloat.ps1")
        log.log_and_print(f"Attempting to download Windows configuration script from: {script_url}", "info")
        log.log_and_print(f"Target script path: {script_path}", "info")
        
        response = requests.get(script_url)
        log.log_and_print(f"Download response status code: {response.status_code}", "info")
        
        with open(script_path, "wb") as file:
            file.write(response.content)
        log.log_and_print("Windows configuration script successfully saved to disk", "info")
        
        powershell_command = (
            f"Set-ExecutionPolicy Bypass -Scope Process -Force; "
            f"& '{script_path}' -Silent -RemoveApps -RemoveGamingApps -DisableTelemetry "
            f"-DisableBing -DisableSuggestions -DisableLockscreenTips -RevertContextMenu "
            f"-TaskbarAlignLeft -HideSearchTb -DisableWidgets -DisableCopilot -ExplorerToThisPC"
            f"-ClearStartAllUsers -DisableDVR -DisableStartRecommended -ExplorerToThisPC"
            f"-DisableMouseAcceleration"
        )
        log.log_and_print(f"Executing PowerShell command with parameters:", "info")
        log.log_and_print(f"Command: {powershell_command}", "info")
        
        process = subprocess.run(
            ["powershell", "-Command", powershell_command],
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            log.log_and_print("Windows configuration completed successfully", "info")
            log.log_and_print(f"Process stdout: {process.stdout}", "info")
            log.log_and_print("Preparing to transition to UpdatePolicyChanger...", "info")
            try:
                log.log_and_print("Initiating UpdatePolicyChanger process...", "info")
                run_updatepolicychanger()
            except Exception as e:
                log.log_and_print(f"Failed to start UpdatePolicyChanger: {e}", "error")
                log.log_and_print("Attempting to continue with installation despite UpdatePolicyChanger failure", "warning")
                run_updatepolicychanger()
        else:
            log.log_and_print(f"Windows configuration failed with return code: {process.returncode}", "error")
            log.log_and_print(f"Process stderr: {process.stderr}", "error")
            log.log_and_print(f"Process stdout: {process.stdout}", "info")
            log.log_and_print("Attempting to continue with UpdatePolicyChanger despite WinConfig failure", "warning")
            try:
                log.log_and_print("Initiating UpdatePolicyChanger after WinConfig failure...", "info")
                run_updatepolicychanger()
            except Exception as e:
                log.log_and_print(f"Failed to start UpdatePolicyChanger after WinConfig failure: {e}", "error")
                log.log_and_print("Proceeding to finalize installation...", "warning")
                run_updatepolicychanger()
            
    except requests.exceptions.RequestException as e:
        log.log_and_print(f"Network error during Windows configuration script download: {str(e)}", "error")
        log.log_and_print("Attempting to continue with UpdatePolicyChanger despite network error", "warning")
        try:
            run_updatepolicychanger()
        except Exception as inner_e:
            log.log_and_print(f"Failed to start UpdatePolicyChanger after network error: {inner_e}", "error")
            run_updatepolicychanger()
    except IOError as e:
        log.log_and_print(f"File I/O error while saving Windows configuration script: {str(e)}", "error")
        log.log_and_print("Attempting to continue with UpdatePolicyChanger despite I/O error", "warning")
        try:
            run_updatepolicychanger()
        except Exception as inner_e:
            log.log_and_print(f"Failed to start UpdatePolicyChanger after I/O error: {inner_e}", "error")
            run_updatepolicychanger()
    except Exception as e:
        log.log_and_print(f"Unexpected error during Windows configuration: {str(e)}", "error")
        log.log_and_print("Attempting to continue with UpdatePolicyChanger despite unexpected error", "warning")
        try:
            run_updatepolicychanger()
        except Exception as inner_e:
            log.log_and_print(f"Failed to start UpdatePolicyChanger after unexpected error: {inner_e}", "error")
            run_updatepolicychanger()



""" Run a script to establish an update policy which only accepts security updates """
def run_updatepolicychanger():
    log.log_and_print("Starting UpdatePolicyChanger script execution...", "info")
    log.log_and_print("Checking system state before UpdatePolicyChanger execution...", "info")
    try:
        script_url = "https://code.ravendevteam.org/talon/update_policy_changer.ps1"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, "UpdatePolicyChanger.ps1")
        log.log_and_print(f"Attempting to download UpdatePolicyChanger script from: {script_url}", "info")
        log.log_and_print(f"Target script path: {script_path}", "info")
        
        try:
            response = requests.get(script_url)
            log.log_and_print(f"Download response status code: {response.status_code}", "info")
            log.log_and_print(f"Response headers: {response.headers}", "info")
            
            if response.status_code != 200:
                log.log_and_print(f"Unexpected status code: {response.status_code}", "warning")
                raise requests.exceptions.RequestException(f"Failed to download: Status code {response.status_code}")
                
            content_length = len(response.content)
            log.log_and_print(f"Downloaded content length: {content_length} bytes", "info")
            
            with open(script_path, "wb") as file:
                file.write(response.content)
            log.log_and_print("UpdatePolicyChanger script successfully saved to disk", "info")
            log.log_and_print(f"Verifying file exists at {script_path}", "info")
            
            if not os.path.exists(script_path):
                raise IOError("Script file not found after saving")
            
            file_size = os.path.getsize(script_path)
            log.log_and_print(f"Saved file size: {file_size} bytes", "info")
            
        except requests.exceptions.RequestException as e:
            log.log_and_print(f"Network error during script download: {e}", "error")
            raise
        
        log.log_and_print("Preparing PowerShell command execution...", "info")
        powershell_command = (
            f"Set-ExecutionPolicy Bypass -Scope Process -Force; "
            f"& '{script_path}'; exit" 
        )
        log.log_and_print(f"PowerShell command prepared: {powershell_command}", "info")
        
        try:
            log.log_and_print("Executing PowerShell command...", "info")
            process = subprocess.run(
                ["powershell", "-Command", powershell_command],
                capture_output=True,
                text=True,
            )
            
            log.log_and_print(f"PowerShell process completed with return code: {process.returncode}", "info")
            log.log_and_print(f"Process stdout length: {len(process.stdout)}", "info")
            log.log_and_print(f"Process stderr length: {len(process.stderr)}", "info")
            
            if process.stdout:
                log.log_and_print(f"Process output: {process.stdout}", "info")
            if process.stderr:
                log.log_and_print(f"Process errors: {process.stderr}", "error")
            
            if process.returncode == 0:
                log.log_and_print("UpdatePolicyChanger execution completed successfully", "info")
                log.log_and_print("Preparing to finalize installation...", "info")
                finalize_installation()
            else:
                log.log_and_print(f"UpdatePolicyChanger execution failed with return code: {process.returncode}", "error")
                log.log_and_print("Proceeding with finalization despite failure...", "warning")
                finalize_installation()
                
        except subprocess.TimeoutExpired:
            log.log_and_print("PowerShell command execution timed out after 5 minutes", "error")
            finalize_installation()
        except subprocess.SubprocessError as e:
            log.log_and_print(f"Error executing PowerShell command: {e}", "error")
            finalize_installation()
            
    except Exception as e:
        log.log_and_print(f"Critical error in UpdatePolicyChanger: {e}", "error")
        log.log_and_print("Proceeding to finalization due to critical error...", "warning")
        finalize_installation()



""" Finalize installation by restarting """
def finalize_installation():
    log.log_and_print("Installation complete. Restarting system...", "info")
    try:
        subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
    except subprocess.CalledProcessError as e:
        log.log_and_print(f"Error during restart: {e}", "error")
        try:
            os.system("shutdown /r /t 0")
        except Exception as e:
            log.log_and_print(f"Failed to restart system: {e}", "error")



""" Run the program """
if __name__ == "__main__":
    apply_registry_changes()