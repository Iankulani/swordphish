#!/usr/bin/env python3
"""
SWORDPHISH - Requirements Checker
Checks all dependencies and provides installation instructions
"""

import sys
import subprocess
import importlib
import platform

# Required packages and their import names
REQUIREMENTS = {
    # Core
    'cryptography': 'cryptography',
    'requests': 'requests',
    'psutil': 'psutil',
    'paramiko': 'paramiko',
    'python-whois': 'whois',
    
    # Optional - Messaging platforms
    'discord.py': 'discord',
    'telethon': 'telethon',
    'slack-sdk': 'slack_sdk',
    'selenium': 'selenium',
    'webdriver-manager': 'webdriver_manager',
    'google-auth': 'google.oauth2',
    'google-api-python-client': 'googleapiclient',
    
    # Optional - Utilities
    'colorama': 'colorama',
    'tqdm': 'tqdm',
}

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python 3.7+ required (found {version.major}.{version.minor})")
        return False

def check_package(package_name, import_name):
    """Check if a package is installed"""
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} - Installed")
        return True
    except ImportError:
        print(f"❌ {package_name} - NOT INSTALLED")
        return False

def check_system_tools():
    """Check system tools availability"""
    tools = {
        'ping': ['ping', '-c', '1', '127.0.0.1'],
        'whois': ['whois', '-h'],
        'ssh': ['ssh', '-V'],
    }
    
    if platform.system().lower() == 'linux':
        tools['iptables'] = ['iptables', '--version']
        tools['traceroute'] = ['traceroute', '--version']
    elif platform.system().lower() == 'windows':
        tools['tracert'] = ['tracert', '127.0.0.1']
        tools['netsh'] = ['netsh', '--version']
    elif platform.system().lower() == 'darwin':
        tools['traceroute'] = ['traceroute', '--version']
    
    results = {}
    for tool, cmd in tools.items():
        try:
            subprocess.run(cmd, capture_output=True, timeout=5)
            print(f"✅ {tool} - Available")
            results[tool] = True
        except (subprocess.SubprocessError, FileNotFoundError):
            print(f"⚠️ {tool} - Not found (optional)")
            results[tool] = False
    
    return results

def print_installation_commands(missing):
    """Print installation commands for missing packages"""
    if not missing:
        return
    
    print("\n" + "="*50)
    print("INSTALLATION COMMANDS")
    print("="*50)
    
    print("\n# Install all requirements:")
    print("pip install -r requirements.txt")
    
    print("\n# Install minimal requirements:")
    print("pip install -r requirements_minimal.txt")
    
    if missing:
        print("\n# Install missing packages individually:")
        for pkg in missing:
            print(f"pip install {pkg}")

def main():
    """Main checker function"""
    print("="*50)
    print("SWORDPHISH - Requirements Checker")
    print("="*50 + "\n")
    
    # Check Python version
    python_ok = check_python_version()
    print()
    
    # Check Python packages
    print("Checking Python Packages:")
    print("-"*30)
    
    missing_packages = []
    for package, import_name in REQUIREMENTS.items():
        if not check_package(package, import_name):
            missing_packages.append(package)
    
    print()
    
    # Check system tools
    print("Checking System Tools:")
    print("-"*30)
    system_tools = check_system_tools()
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    if not missing_packages and python_ok:
        print("✅ All core requirements are satisfied!")
    else:
        print(f"⚠️ Missing {len(missing_packages)} package(s)")
    
    # Optional platform status
    print("\nPlatform Availability:")
    print("-"*30)
    
    platforms = {
        'Discord': 'discord',
        'Telegram': 'telethon',
        'Slack': 'slack_sdk',
        'WhatsApp': 'selenium',
        'Google Chat': 'googleapiclient',
    }
    
    for name, module in platforms.items():
        try:
            importlib.import_module(module)
            print(f"  ✅ {name}: Available")
        except ImportError:
            print(f"  ❌ {name}: Not available (optional)")
    
    print("\n" + "="*50)
    
    # Installation commands
    print_installation_commands(missing_packages)
    
    return 0 if not missing_packages and python_ok else 1

if __name__ == "__main__":
    sys.exit(main())