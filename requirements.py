import os
import sys


current_dir = os.path.dirname(os.path.abspath(__file__))
requirements_path = os.path.join(current_dir, "requirements.txt")

if not os.path.exists(requirements_path) or not os.path.isfile(requirements_path):
    print("Requirements file not found at the expected path. Using default path.")
    requirements_path = "./requirements.txt"

def install_latest_version_pip():
    try:
        os.system("python -m pip install --upgrade pip")
        print("Successfully upgraded pip to the latest version")
    except Exception as e:
        print(f"Error upgrading pip: {e}")
        sys.exit(1)
        
def install_latest_version_requirements():
    try:
        os.system(f"python -m pip install -r \"{requirements_path}\"")
        print("Successfully installed requirements")
    except Exception as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1) 
        
def run() -> bool:
    install_latest_version_pip()
    
    if os.path.exists(requirements_path):
        install_latest_version_requirements()
        return True
    else:
        print(f"Requirements file not found at {requirements_path}, skipping installation of requirements.")
        return False

if __name__ == "__main__":
    run()