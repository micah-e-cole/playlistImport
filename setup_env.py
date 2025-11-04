#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def create_venv(venv_dir="venv"):
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path(venv_dir)
    if not venv_path.exists():
        print(f"Creating virtual environment in '{venv_dir}'...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
    else:
        print("Virtual environment already exists.")
    return venv_path

def install_dependencies(venv_path, requirements_file="requirements.txt"):
    """Activate the virtual environment and install dependencies."""
    pip_executable = venv_path / "Scripts" / "pip.exe" if os.name == "nt" else venv_path / "bin" / "pip"
    if not pip_executable.exists():
        raise FileNotFoundError(f"pip not found in virtual environment: {pip_executable}")

    if Path(requirements_file).exists():
        print(f"Installing dependencies from {requirements_file}...")
        subprocess.run([str(pip_executable), "install", "-r", requirements_file], check=True)
    else:
        print(f"No {requirements_file} found. Skipping dependency installation.")

def main():
    venv_path = create_venv()
    install_dependencies(venv_path)
    print("\n✅ Environment ready!")
    print(f"To activate it, run:\n  source {venv_path}/bin/activate" if os.name != "nt"
          else f"  {venv_path}\\Scripts\\activate")

if __name__ == "__main__":
    main()
