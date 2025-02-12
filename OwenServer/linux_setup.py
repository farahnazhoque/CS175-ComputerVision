import os
import shutil
import subprocess
import sys

# Configuration - all paths relative to script location
SCRIPT_DIR = os.getcwd()
VCPKG_DIR = os.path.join(SCRIPT_DIR, "vcpkg")
TRIPLET = "x64-linux"  # Change this if needed for your system

def check_commands():
    required = ['git', 'cmake', 'ninja', 'nvcc', 'g++']
    missing = [cmd for cmd in required if not shutil.which(cmd)]
    if missing:
        print(f"Error: Missing required commands: {', '.join(missing)}")
        print("Please ensure these are installed and in your PATH:")
        print("- git, cmake, ninja: build tools")
        print("- nvcc: CUDA compiler (install CUDA toolkit)")
        print("- g++: C++ compiler")
        sys.exit(1)

def setup_directories():
    os.makedirs(SCRIPT_DIR, exist_ok=True)
    print(f"Installing in current directory: {SCRIPT_DIR}")

def clone_vcpkg():
    if not os.path.exists(VCPKG_DIR):
        print("Cloning vcpkg repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/microsoft/vcpkg", VCPKG_DIR],
            check=True
        )

def bootstrap_vcpkg():
    bootstrap_script = os.path.join(VCPKG_DIR, "bootstrap-vcpkg.sh")
    print("Bootstrapping vcpkg...")
    subprocess.run([bootstrap_script], cwd=VCPKG_DIR, check=True)

def install_colmap():
    vcpkg_exe = os.path.join(VCPKG_DIR, "vcpkg")
    print("Installing COLMAP with CUDA support (this will take a while)...")
    subprocess.run(
        [vcpkg_exe, "install", f"colmap[cuda,tests]:{TRIPLET}"],
        cwd=VCPKG_DIR,
        check=True
    )

def create_env_script():
    env_script = os.path.join(SCRIPT_DIR, "setup_env.sh")
    installed_dir = os.path.join(VCPKG_DIR, "installed", TRIPLET)
    bin_path = os.path.join(installed_dir, "tools", "colmap")
    lib_path = os.path.join(installed_dir, "lib")
    
    content = f"""#!/bin/bash
export PATH="{bin_path}:$PATH"
export LD_LIBRARY_PATH="{lib_path}:$LD_LIBRARY_PATH"
echo "Environment variables set for COLMAP in {SCRIPT_DIR}"
echo "You can now run: colmap -h"
"""
    
    with open(env_script, "w") as f:
        f.write(content)
    
    os.chmod(env_script, 0o755)
    print(f"\nCreated environment setup script: {env_script}")
    print(f"Source it to use COLMAP:\n  source {env_script}")

def main():
    print("Starting COLMAP installation in current directory...")
    check_commands()
    setup_directories()
    clone_vcpkg()
    bootstrap_vcpkg()
    install_colmap()
    create_env_script()
    print("\nInstallation complete!")
    print(f"COLMAP installed in: {SCRIPT_DIR}")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nError during installation: {e}")
        sys.exit(1)