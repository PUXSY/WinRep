""" Import necessary modules for the program to work """
import sys
import ctypes
import os
import tempfile
import subprocess
import requests
import winreg
import shutil
import time
from logger import Logger
from pathlib import Path


log = Logger()

""" Utility function to check if the program is running as administrator """
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

""" Apply modifications done via the Windows registry """
def apply_registry_changes():
    log.log_and_print("Applying registry changes...", "info")
    try:
        registry_modifications = [
            # Visual changes
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "AppsUseLightTheme", winreg.REG_DWORD, 0), # Set Windows to dark theme
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "SystemUsesLightTheme", winreg.REG_DWORD, 0), # Set Windows to dark theme
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR", "AppCaptureEnabled", winreg.REG_DWORD, 0), #Fix the  Get an app for 'ms-gamingoverlay' popup
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\PolicyManager\\default\\ApplicationManagement\\AllowGameDVR", "Value", winreg.REG_DWORD, 0), # Disable Game DVR (Reduces FPS Drops)
            (winreg.HKEY_CURRENT_USER, r"Control Panel\\Desktop", "MenuShowDelay", winreg.REG_SZ, "0"),# Reduce menu delay for snappier UI
            (winreg.HKEY_CURRENT_USER, r"Control Panel\\Desktop\\WindowMetrics", "MinAnimate", winreg.REG_DWORD, 0),# Disable minimize/maximize animations
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "ExtendedUIHoverTime", winreg.REG_DWORD, 1),# Reduce hover time for tooltips and UI elements
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "HideFileExt", winreg.REG_DWORD, 0),# Show file extensions in Explorer (useful for security and organization)
        ]
        
        success_count = 0
        for root_key, key_path, value_name, value_type, value in registry_modifications:
            try:
                with winreg.CreateKeyEx(root_key, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, value_name, 0, value_type, value)
                    success_count += 1
                    log.log_and_print(f"Applied {value_name} to {key_path}", "info")
            except Exception as e:
                log.log_and_print(f"Failed to modify {value_name} in {key_path}: {e}", "error")
        
        log.log_and_print(f"Registry changes: {success_count}/{len(registry_modifications)} successfully applied.", "info")
        
        try:
            # Restart explorer safely
            subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           check=False)  # Don't raise an exception if this fails
            
            # Wait briefly for explorer to terminate
            time.sleep(1)
            
            # Start explorer again
            subprocess.Popen("explorer.exe", shell=True)
            log.log_and_print("Explorer restarted to apply registry changes.", "info")
        except Exception as e:
            log.log_and_print(f"Error restarting explorer: {e}", "error")
            log.log_and_print("Continuing without restarting explorer.", "warning")
        
        # Check if we're in a VM before running Edge Vanisher
        if is_vm_environment():
            log.log_and_print("Detected VM environment. Skipping Edge Vanisher for stability.", "warning")
        else:
            run_edge_vanisher()
            log.log_and_print("Edge Vanisher completed", "info")
        
    except Exception as e:
        log.log_and_print(f"Error applying registry changes: {e}", "error")


""" Detect if running in a virtual machine environment """
def is_vm_environment():
    # Check for common VM indicators
    try:
        # Check for VMware-specific registry keys
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\VMware, Inc.\VMware Tools") as key:
                return True
        except FileNotFoundError:
            pass
        
        # Check for common VM services
        vm_services = ["vmtools", "vmmouse", "vmusbmouse", "vmvss", "vmscsi", "vmx_svga"]
        for service in vm_services:
            try:
                output = subprocess.check_output(f"sc query {service}", shell=True, stderr=subprocess.STDOUT)
                if b"RUNNING" in output:
                    return True
            except subprocess.CalledProcessError:
                pass
        
        # Check for VirtualBox
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\ACPI\DSDT\VBOX__") as key:
                return True
        except FileNotFoundError:
            pass
            
        # Check hardware information for VM indicators
        system_info = subprocess.check_output("systeminfo", shell=True).decode('utf-8', errors='ignore')
        vm_indicators = ["vmware", "virtual", "hypervisor", "vbox"]
        if any(indicator in system_info.lower() for indicator in vm_indicators):
            return True
            
    except Exception as e:
        log.log_and_print(f"Error checking VM environment: {e}", "error")
    
    return False


""" Safe file download function with better error handling """
def safe_download_file(url, target_path):
    log.log_and_print(f"Downloading from: {url}", "info")
    log.log_and_print(f"Target path: {target_path}", "info")
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            
            with open(target_path, "wb") as file:
                file.write(response.content)
                
            log.log_and_print(f"Download successful. File size: {len(response.content)} bytes", "info")
            return True
            
        except requests.exceptions.RequestException as e:
            retry_count += 1
            log.log_and_print(f"Download attempt {retry_count} failed: {e}", "warning")
            time.sleep(2)  # Wait before retrying
    
    log.log_and_print(f"All download attempts failed after {max_retries} retries", "error")
    return False


""" Run a script to remove Edge, and prevent reinstallation """
def run_edge_vanisher():
    log.log_and_print("Starting Edge Vanisher script execution...", "info")
    try:
        script_url = "https://code.ravendevteam.org/talon/edge_vanisher.ps1"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, "edge_vanisher.ps1")
        
        # First attempt direct download
        download_success = safe_download_file(script_url, script_path)
        
        if not download_success:
            log.log_and_print("Could not download Edge Vanisher script. Skipping this step.", "warning")
            run_oouninstall()
            return
        
        powershell_command = (
            f"Set-ExecutionPolicy Bypass -Scope Process -Force; "
            f"& '{script_path}' -Force; exit"  # Added -Force for VM environments
        )
        log.log_and_print(f"Executing PowerShell command: {powershell_command}", "info")
        
        try:
            process = subprocess.run(
                ["powershell", "-Command", powershell_command],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if process.returncode == 0:
                log.log_and_print("Edge Vanisher execution completed successfully", "info")
                log.log_and_print(f"Process output: {process.stdout[:500]}...", "info")  # Only log first 500 chars
                run_oouninstall()
            else:
                log.log_and_print(f"Edge Vanisher execution failed with return code: {process.returncode}", "error")
                log.log_and_print(f"Process error: {process.stderr[:500]}...", "error")
                run_oouninstall()
                
        except subprocess.TimeoutExpired:
            log.log_and_print("Edge Vanisher execution timed out. Proceeding to next step.", "warning")
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
        
        # First attempt direct download
        download_success = safe_download_file(script_url, script_path)
        
        if not download_success:
            log.log_and_print("Could not download Office uninstaller script. Skipping this step.", "warning")
            run_tweaks()
            return
        
        powershell_command = f"Set-ExecutionPolicy Bypass -Scope Process -Force; & '{script_path}'"
        log.log_and_print(f"Executing PowerShell command: {powershell_command}", "info")
        
        try:
            process = subprocess.run(
                ["powershell", "-Command", powershell_command],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if process.returncode == 0:
                log.log_and_print("Office Online uninstallation completed successfully", "info")
                run_tweaks()
            else:
                log.log_and_print(f"Office Online uninstallation failed with return code: {process.returncode}", "error")
                log.log_and_print(f"Process stderr: {process.stderr[:500]}...", "error")  # Only log first 500 chars
                run_tweaks()
                
        except subprocess.TimeoutExpired:
            log.log_and_print("Office uninstallation timed out. Proceeding to next step.", "warning")
            run_tweaks()
            
    except Exception as e:
        log.log_and_print(f"Unexpected error during OO uninstallation: {str(e)}", "error")
        run_tweaks()


""" Run ChrisTitusTech's WinUtil with VM-aware modifications """
def run_tweaks():
    if not is_admin():
        log.log_and_print("Must be run as an administrator.", "error")
        return False

    try:
        # If in a VM environment, use more conservative settings
        if is_vm_environment():
            log.log_and_print("VM environment detected. Using VM-safe tweaks configuration.", "info")
            json_path = os.path.join(os._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(__file__), "vm_safe.json")
            # If VM-safe config doesn't exist, create a minimal one
            if not os.path.exists(json_path):
                log.log_and_print("VM-safe config not found. Creating minimal configuration.", "info")
                minimal_config = {
                    "tweaks": ["RemoveW11Bloat", "DisableTelemetry", "EssentialTweaks"],
                    "preset": "minimal"
                }
                with open(json_path, "w") as f:
                    json.dump(minimal_config, f)
        else:
            json_path = os.path.join(os._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(__file__), "barebones.json")

        log.log_and_print(f"Using config from: {json_path}", "info")

        temp_dir = tempfile.gettempdir()
        log.log_file = os.path.join(temp_dir, "cttwinutil.log")

        # Use a safer command with timeout and error handling
        command = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"$ErrorActionPreference = 'SilentlyContinue'; " +
            f"try {{ " +
            f"iex \"& {{ $(irm christitus.com/win) }} -Config '{json_path}' -Run -Silent\" *>&1 | " +
            "Tee-Object -FilePath '" + log.log_file + "'; " +
            f"}} catch {{ Write-Error $_.Exception.Message }}"
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

        # Set a timeout for script execution
        start_time = time.time()
        timeout = 600  # 10 minutes
        
        while True:
            # Check for timeout
            if time.time() - start_time > timeout:
                log.log_and_print("Tweaks script timed out after 10 minutes. Terminating...", "warning")
                try:
                    process.terminate()
                except:
                    pass
                run_winconfig()
                return False
                
            output = process.stdout.readline()
            if output:
                output = output.strip()
                log.log_and_print(f"CTT Output: {output}", "info")
                if "Tweaks are Finished" in output:
                    log.log_and_print("Detected completion message. Terminating...", "info")

                    try:
                        subprocess.run(
                            ["powershell", "-Command", "Stop-Process -Name powershell -Force"],
                            capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    except:
                        pass

                    run_winconfig()
                    return True
            
            # Check if process has ended
            if process.poll() is not None:
                log.log_and_print("Tweaks process ended. Moving to next step.", "info")
                run_winconfig()
                return False
                
            # Add a small sleep to reduce CPU usage
            time.sleep(0.1)

    except Exception as e:
        log.log_and_print(f"Error in tweaks process: {str(e)}", "error")
        run_winconfig()
        return False


""" Run Raphi's Win11Debloat script with VM-specific optimizations """
def run_winconfig():
    log.log_and_print("Starting Windows configuration process...", "info")
    try:
        script_url = "https://win11debloat.raphi.re/"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, "Win11Debloat.ps1")
        
        # First attempt direct download
        download_success = safe_download_file(script_url, script_path)
        
        if not download_success:
            log.log_and_print("Could not download Windows configuration script. Skipping this step.", "warning")
            run_updatepolicychanger()
            return
        
        # Modify parameters for VM environment
        vm_detected = is_vm_environment()
        if vm_detected:
            log.log_and_print("VM detected. Using VM-friendly parameters for Windows configuration.", "info")
            powershell_command = (
                f"Set-ExecutionPolicy Bypass -Scope Process -Force; "
                f"& '{script_path}' -Silent -RemoveApps -DisableTelemetry "
                f"-DisableBing -DisableSuggestions -RevertContextMenu"
            )
        else:
            powershell_command = (
                f"Set-ExecutionPolicy Bypass -Scope Process -Force; "
                f"& '{script_path}' -Silent -RemoveApps -RemoveGamingApps -DisableTelemetry "
                f"-DisableBing -DisableSuggestions -DisableLockscreenTips -RevertContextMenu "
                f"-TaskbarAlignLeft -HideSearchTb -DisableWidgets -DisableCopilot -ExplorerToThisPC "
                f"-ClearStartAllUsers -DisableDVR -DisableStartRecommended -ExplorerToThisPC "
                f"-DisableMouseAcceleration"
            )
            
        log.log_and_print(f"Executing PowerShell command with parameters:", "info")
        log.log_and_print(f"Command: {powershell_command}", "info")
        
        try:
            process = subprocess.run(
                ["powershell", "-Command", powershell_command],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if process.returncode == 0:
                log.log_and_print("Windows configuration completed successfully", "info")
                log.log_and_print("Preparing to transition to UpdatePolicyChanger...", "info")
                try:
                    run_updatepolicychanger()
                except Exception as e:
                    log.log_and_print(f"Failed to start UpdatePolicyChanger: {e}", "error")
                    log.log_and_print("Attempting to continue with installation despite UpdatePolicyChanger failure", "warning")
                    run_updatepolicychanger()
            else:
                log.log_and_print(f"Windows configuration failed with return code: {process.returncode}", "error")
                log.log_and_print(f"Process stderr: {process.stderr[:500]}...", "error")  # Only log first 500 chars
                log.log_and_print("Attempting to continue with UpdatePolicyChanger despite WinConfig failure", "warning")
                try:
                    run_updatepolicychanger()
                except Exception as e:
                    log.log_and_print(f"Failed to start UpdatePolicyChanger after WinConfig failure: {e}", "error")
                    log.log_and_print("Proceeding to finalize installation...", "warning")
                    run_updatepolicychanger()
                    
        except subprocess.TimeoutExpired:
            log.log_and_print("Windows configuration timed out after 10 minutes", "warning")
            log.log_and_print("Proceeding to next step...", "info")
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
    
    # Skip this in VM environments to avoid potential issues
    if is_vm_environment():
        log.log_and_print("VM environment detected. Skipping update policy changes for stability.", "warning")
        finalize_installation(vm_mode=True)
        return
    
    try:
        script_url = "https://code.ravendevteam.org/talon/update_policy_changer.ps1"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, "UpdatePolicyChanger.ps1")
        
        # First attempt direct download
        download_success = safe_download_file(script_url, script_path)
        
        if not download_success:
            log.log_and_print("Could not download UpdatePolicyChanger script. Skipping this step.", "warning")
            finalize_installation()
            return
        
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
                timeout=300  # 5 minute timeout
            )
            
            log.log_and_print(f"PowerShell process completed with return code: {process.returncode}", "info")
            
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
            
    except Exception as e:
        log.log_and_print(f"Critical error in UpdatePolicyChanger: {e}", "error")
        log.log_and_print("Proceeding to finalization due to critical error...", "warning")
        finalize_installation()


""" Finalize installation with VM-aware restart option """
def finalize_installation(vm_mode=False):
    if vm_mode:
        log.log_and_print("Installation complete in VM environment.", "info")
        log.log_and_print("In VMs, it's recommended to restart manually after reviewing changes.", "info")
        log.log_and_print("You can restart now by running 'shutdown /r /t 0' in Command Prompt.", "info")
        return
        
    log.log_and_print("Installation complete. Preparing system restart...", "info")
    
    # Give a 30-second countdown for VM environments
    try:
        subprocess.run(["shutdown", "/r", "/t", "30", "/c", "WinRep installation complete. System will restart in 30 seconds."], check=True)
        log.log_and_print("System will restart in 30 seconds. Close this window to cancel restart.", "info")
    except subprocess.CalledProcessError as e:
        log.log_and_print(f"Error scheduling restart: {e}", "error")
        try:
            # Fallback to immediate restart
            log.log_and_print("Attempting immediate restart...", "info")
            os.system("shutdown /r /t 0")
        except Exception as e:
            log.log_and_print(f"Failed to restart system: {e}", "error")
            log.log_and_print("Please restart your system manually to complete installation.", "warning")


""" Run the program """
if __name__ == "__main__":
    # Only perform admin check and elevation here, not at module level
    if not is_admin():
        log.log_and_print("Attempting to restart with administrator privileges...", "info")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        except Exception as e:
            log.log_and_print(f"Failed to restart with admin privileges: {e}", "error")
            log.log_and_print("Please run this program as an administrator.", "warning")
            sys.exit(1)
    else:
        apply_registry_changes()