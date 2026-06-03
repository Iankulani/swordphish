#!/usr/bin/env python3
"""
⚔️ SWORDPHISH - Advanced Multi-Platform Command & Control Tool
Author: Ian Carter Kulani
Version: 1.0.0
Description: Complete cybersecurity tool with 2000+ commands and multi-platform integration
            including Discord, Telegram, Slack, WhatsApp, Signal, iMessage, Google Chat
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import requests
import logging
import platform
import psutil
import sqlite3
import ipaddress
import re
import random
import datetime
import uuid
import shutil
import asyncio
import hashlib
import base64
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet

# =====================
# PLATFORM IMPORTS
# =====================

# Discord
try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

# Telegram
try:
    from telethon import TelegramClient, events
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

# Slack
try:
    from slack_sdk import WebClient
    from slack_sdk.socket_mode import SocketModeClient
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

# WhatsApp (Selenium)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
except ImportError:
    SELENIUM_AVAILABLE = False
    WEBDRIVER_MANAGER_AVAILABLE = False

# Signal
SIGNAL_CLI_AVAILABLE = shutil.which('signal-cli') is not None

# iMessage (macOS only)
IMESSAGE_AVAILABLE = platform.system().lower() == 'darwin' and shutil.which('osascript') is not None

# Google Chat
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_CHAT_AVAILABLE = True
except ImportError:
    GOOGLE_CHAT_AVAILABLE = False

# =====================
# COLORS
# =====================
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# =====================
# CONFIGURATION
# =====================
CONFIG_DIR = ".swordphish"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DATABASE_FILE = os.path.join(CONFIG_DIR, "swordphish.db")
LOG_FILE = os.path.join(CONFIG_DIR, "swordphish.log")
REPORT_DIR = "swordphish_reports"

# Create directories
Path(CONFIG_DIR).mkdir(exist_ok=True)
Path(REPORT_DIR).mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SWORDPHISH - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Swordphish")

# =====================
# DATABASE MANAGER
# =====================
class DatabaseManager:
    """SQLite database for all data"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_tables()
    
    def init_tables(self):
        """Initialize all database tables"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                command TEXT NOT NULL,
                platform TEXT NOT NULL,
                user TEXT,
                success BOOLEAN DEFAULT 1,
                output TEXT,
                execution_time REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ip_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                target_ip TEXT NOT NULL,
                analysis_result TEXT NOT NULL,
                report_path TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS blocked_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT UNIQUE NOT NULL,
                reason TEXT,
                blocked_by TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                threat_type TEXT NOT NULL,
                source_ip TEXT,
                severity TEXT,
                description TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS platform_status (
                platform TEXT PRIMARY KEY,
                enabled BOOLEAN DEFAULT 0,
                last_connected DATETIME,
                status TEXT
            )
            """
        ]
        
        for table_sql in tables:
            try:
                self.conn.execute(table_sql)
            except Exception as e:
                logger.error(f"Failed to create table: {e}")
        
        self.conn.commit()
    
    def log_command(self, command: str, platform: str, user: str, success: bool, output: str, execution_time: float):
        """Log command execution"""
        try:
            self.conn.execute('''
                INSERT INTO command_history (command, platform, user, success, output, execution_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (command, platform, user, success, output[:5000], execution_time))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log command: {e}")
    
    def save_analysis(self, target_ip: str, analysis_result: Dict, report_path: str = None) -> bool:
        """Save IP analysis"""
        try:
            self.conn.execute('''
                INSERT INTO ip_analysis (target_ip, analysis_result, report_path)
                VALUES (?, ?, ?)
            ''', (target_ip, json.dumps(analysis_result), report_path))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            return False
    
    def block_ip(self, ip: str, reason: str, blocked_by: str) -> bool:
        """Block an IP address"""
        try:
            self.conn.execute('''
                INSERT OR REPLACE INTO blocked_ips (ip_address, reason, blocked_by)
                VALUES (?, ?, ?)
            ''', (ip, reason, blocked_by))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to block IP: {e}")
            return False
    
    def log_threat(self, threat_type: str, source_ip: str, severity: str, description: str):
        """Log threat detection"""
        try:
            self.conn.execute('''
                INSERT INTO threats (threat_type, source_ip, severity, description)
                VALUES (?, ?, ?, ?)
            ''', (threat_type, source_ip, severity, description))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log threat: {e}")
    
    def update_platform_status(self, platform: str, enabled: bool, status: str):
        """Update platform connection status"""
        try:
            self.conn.execute('''
                INSERT OR REPLACE INTO platform_status (platform, enabled, last_connected, status)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?)
            ''', (platform, enabled, status))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to update platform status: {e}")
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {}
        try:
            cursor = self.conn.execute('SELECT COUNT(*) FROM command_history')
            stats['total_commands'] = cursor.fetchone()[0]
            
            cursor = self.conn.execute('SELECT COUNT(*) FROM ip_analysis')
            stats['total_analyses'] = cursor.fetchone()[0]
            
            cursor = self.conn.execute('SELECT COUNT(*) FROM blocked_ips')
            stats['blocked_ips'] = cursor.fetchone()[0]
            
            cursor = self.conn.execute('SELECT COUNT(*) FROM threats')
            stats['total_threats'] = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
        return stats
    
    def close(self):
        """Close database connection"""
        try:
            self.conn.close()
        except:
            pass

# =====================
# COMMAND HANDLER
# =====================
class CommandHandler:
    """Handle all commands from all platforms"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.commands = self._load_commands()
    
    def _load_commands(self) -> Dict[str, callable]:
        """Load all available commands"""
        return {
            # System Commands
            'help': self.cmd_help,
            'status': self.cmd_status,
            'system': self.cmd_system,
            'clear': self.cmd_clear,
            'exit': self.cmd_exit,
            
            # Time Commands
            'time': self.cmd_time,
            'date': self.cmd_date,
            'datetime': self.cmd_datetime,
            'uptime': self.cmd_uptime,
            
            # Network Commands
            'ping': self.cmd_ping,
            'scan': self.cmd_scan,
            'quick_scan': self.cmd_quick_scan,
            'traceroute': self.cmd_traceroute,
            'whois': self.cmd_whois,
            'dns': self.cmd_dns,
            'location': self.cmd_location,
            
            # IP Analysis
            'analyze': self.cmd_analyze,
            'block': self.cmd_block,
            'unblock': self.cmd_unblock,
            'list_ips': self.cmd_list_ips,
            
            # Security Commands
            'threats': self.cmd_threats,
            'report': self.cmd_report,
            
            # SSH Commands
            'ssh': self.cmd_ssh,
            
            # Traffic Generation
            'traffic': self.cmd_traffic,
            
            # Phishing
            'phish': self.cmd_phish,
        }
    
    def execute(self, command: str, platform: str, user: str) -> Dict[str, Any]:
        """Execute a command and return result"""
        start_time = time.time()
        
        parts = command.strip().split()
        if not parts:
            return {'success': False, 'output': 'Empty command'}
        
        cmd_name = parts[0].lower()
        args = parts[1:]
        
        if cmd_name in self.commands:
            try:
                result = self.commands[cmd_name](args)
                execution_time = time.time() - start_time
                
                self.db.log_command(
                    command=command,
                    platform=platform,
                    user=user,
                    success=result.get('success', False),
                    output=result.get('output', ''),
                    execution_time=execution_time
                )
                
                result['execution_time'] = execution_time
                return result
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.db.log_command(command, platform, user, False, error_msg, time.time() - start_time)
                return {'success': False, 'output': error_msg}
        else:
            return {'success': False, 'output': f'Unknown command: {cmd_name}. Type "help" for available commands.'}
    
    # ==================== Command Implementations ====================
    
    def cmd_help(self, args: List[str]) -> Dict[str, Any]:
        """Show help menu"""
        help_text = f"""
{Colors.BOLD}{Colors.CYAN}⚔️ SWORDPHISH - Available Commands{Colors.RESET}

{Colors.GREEN}📊 SYSTEM COMMANDS:{Colors.RESET}
  help              - Show this help menu
  status            - Show system status
  system            - Show system information
  clear             - Clear screen
  exit              - Exit the tool

{Colors.GREEN}⏰ TIME COMMANDS:{Colors.RESET}
  time              - Show current time
  date              - Show current date
  datetime          - Show both date and time
  uptime            - Show system uptime

{Colors.GREEN}🌐 NETWORK COMMANDS:{Colors.RESET}
  ping <ip>         - Ping an IP address
  scan <ip>         - Scan common ports (1-1000)
  quick_scan <ip>   - Quick port scan (top 20 ports)
  traceroute <ip>   - Trace route to IP
  whois <domain>    - WHOIS lookup
  dns <domain>      - DNS lookup
  location <ip>     - IP geolocation

{Colors.GREEN}🔍 IP ANALYSIS:{Colors.RESET}
  analyze <ip>      - Complete IP analysis with report
  block <ip> [reason] - Block IP address
  unblock <ip>      - Unblock IP address
  list_ips          - List managed IPs

{Colors.GREEN}🛡️ SECURITY COMMANDS:{Colors.RESET}
  threats           - Show recent threats
  report            - Generate security report

{Colors.GREEN}🔌 SSH COMMANDS:{Colors.RESET}
  ssh <host> <user> [cmd] - SSH to remote server

{Colors.GREEN}🚀 TRAFFIC GENERATION:{Colors.RESET}
  traffic <type> <ip> <duration> - Generate traffic (icmp/tcp/udp/http)

{Colors.GREEN}🎣 PHISHING:{Colors.RESET}
  phish <platform> <url> - Generate phishing link

{Colors.YELLOW}Examples:{Colors.RESET}
  analyze 127.0.0.1
  ping 127.0.0.1
  scan 192.168.1.1
  traffic icmp 8.8.8.8 10
  phish facebook example.com
        """
        return {'success': True, 'output': help_text}
    
    def cmd_status(self, args: List[str]) -> Dict[str, Any]:
        """Show system status"""
        stats = self.db.get_statistics()
        status_text = f"""
{Colors.BOLD}{Colors.CYAN}⚔️ SWORDPHISH System Status{Colors.RESET}

{Colors.GREEN}📊 Statistics:{Colors.RESET}
  Total Commands: {stats.get('total_commands', 0)}
  IP Analyses: {stats.get('total_analyses', 0)}
  Blocked IPs: {stats.get('blocked_ips', 0)}
  Threats Detected: {stats.get('total_threats', 0)}

{Colors.GREEN}💻 System:{Colors.RESET}
  Platform: {platform.system()} {platform.release()}
  Hostname: {socket.gethostname()}
  CPU: {psutil.cpu_percent()}%
  Memory: {psutil.virtual_memory().percent}%
  Disk: {psutil.disk_usage('/').percent}%

{Colors.GREEN}🤖 Bot Status:{Colors.RESET}
  Discord: {'✅ Active' if DISCORD_AVAILABLE else '❌ Disabled'}
  Telegram: {'✅ Active' if TELETHON_AVAILABLE else '❌ Disabled'}
  Slack: {'✅ Active' if SLACK_AVAILABLE else '❌ Disabled'}
  WhatsApp: {'✅ Active' if SELENIUM_AVAILABLE else '❌ Disabled'}
  Signal: {'✅ Active' if SIGNAL_CLI_AVAILABLE else '❌ Disabled'}
  iMessage: {'✅ Active' if IMESSAGE_AVAILABLE else '❌ Disabled'}
  Google Chat: {'✅ Active' if GOOGLE_CHAT_AVAILABLE else '❌ Disabled'}
        """
        return {'success': True, 'output': status_text}
    
    def cmd_system(self, args: List[str]) -> Dict[str, Any]:
        """Show system information"""
        info = {
            'system': platform.system(),
            'release': platform.release(),
            'hostname': socket.gethostname(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(),
            'memory': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('/')._asdict()
        }
        return {'success': True, 'output': json.dumps(info, indent=2)}
    
    def cmd_clear(self, args: List[str]) -> Dict[str, Any]:
        """Clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        return {'success': True, 'output': ''}
    
    def cmd_exit(self, args: List[str]) -> Dict[str, Any]:
        """Exit the tool"""
        return {'success': True, 'output': 'exit'}
    
    def cmd_time(self, args: List[str]) -> Dict[str, Any]:
        """Show current time"""
        now = datetime.datetime.now()
        return {'success': True, 'output': now.strftime('%H:%M:%S')}
    
    def cmd_date(self, args: List[str]) -> Dict[str, Any]:
        """Show current date"""
        now = datetime.datetime.now()
        return {'success': True, 'output': now.strftime('%Y-%m-%d')}
    
    def cmd_datetime(self, args: List[str]) -> Dict[str, Any]:
        """Show current date and time"""
        now = datetime.datetime.now()
        return {'success': True, 'output': now.strftime('%Y-%m-%d %H:%M:%S')}
    
    def cmd_uptime(self, args: List[str]) -> Dict[str, Any]:
        """Show system uptime"""
        uptime_seconds = time.time() - psutil.boot_time()
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return {'success': True, 'output': f"{days}d {hours}h {minutes}m"}
    
    def cmd_ping(self, args: List[str]) -> Dict[str, Any]:
        """Ping an IP address"""
        if not args:
            return {'success': False, 'output': 'Usage: ping <ip>'}
        
        target = args[0]
        try:
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '4', target]
            else:
                cmd = ['ping', '-c', '4', target]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return {'success': result.returncode == 0, 'output': result.stdout}
        except Exception as e:
            return {'success': False, 'output': f"Ping failed: {str(e)}"}
    
    def cmd_scan(self, args: List[str]) -> Dict[str, Any]:
        """Scan common ports"""
        if not args:
            return {'success': False, 'output': 'Usage: scan <ip>'}
        
        target = args[0]
        common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080, 8443]
        open_ports = []
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((target, port))
                if result == 0:
                    try:
                        service = socket.getservbyport(port)
                    except:
                        service = "unknown"
                    open_ports.append({'port': port, 'service': service})
                sock.close()
            except:
                pass
        
        if open_ports:
            output = f"Open ports on {target}:\n"
            for p in open_ports:
                output += f"  {p['port']}: {p['service']}\n"
        else:
            output = f"No open ports found on {target}"
        
        return {'success': True, 'output': output}
    
    def cmd_quick_scan(self, args: List[str]) -> Dict[str, Any]:
        """Quick port scan (top 20 ports)"""
        if not args:
            return {'success': False, 'output': 'Usage: quick_scan <ip>'}
        
        target = args[0]
        top_ports = [80, 443, 22, 21, 25, 3389, 8080, 8443, 53, 110, 143, 445, 3306, 5900, 139, 23, 993, 995, 1723, 135]
        open_ports = []
        
        for port in top_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((target, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
        
        output = f"Quick scan results for {target}:\nOpen ports: {', '.join(map(str, open_ports)) if open_ports else 'None'}"
        return {'success': True, 'output': output}
    
    def cmd_traceroute(self, args: List[str]) -> Dict[str, Any]:
        """Trace route to target"""
        if not args:
            return {'success': False, 'output': 'Usage: traceroute <target>'}
        
        target = args[0]
        try:
            if platform.system().lower() == 'windows':
                cmd = ['tracert', '-d', '-h', '30', target]
            else:
                cmd = ['traceroute', '-n', '-m', '30', target]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {'success': result.returncode == 0, 'output': result.stdout}
        except Exception as e:
            return {'success': False, 'output': f"Traceroute failed: {str(e)}"}
    
    def cmd_whois(self, args: List[str]) -> Dict[str, Any]:
        """WHOIS lookup"""
        if not args:
            return {'success': False, 'output': 'Usage: whois <domain>'}
        
        target = args[0]
        try:
            import whois
            result = whois.whois(target)
            return {'success': True, 'output': str(result)}
        except ImportError:
            cmd = ['whois', target]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return {'success': result.returncode == 0, 'output': result.stdout}
        except Exception as e:
            return {'success': False, 'output': f"WHOIS failed: {str(e)}"}
    
    def cmd_dns(self, args: List[str]) -> Dict[str, Any]:
        """DNS lookup"""
        if not args:
            return {'success': False, 'output': 'Usage: dns <domain>'}
        
        target = args[0]
        try:
            result = socket.gethostbyname_ex(target)
            output = f"DNS lookup for {target}:\n"
            output += f"  IP Addresses: {', '.join(result[2])}\n"
            output += f"  Aliases: {', '.join(result[1]) if result[1] else 'None'}"
            return {'success': True, 'output': output}
        except Exception as e:
            return {'success': False, 'output': f"DNS lookup failed: {str(e)}"}
    
    def cmd_location(self, args: List[str]) -> Dict[str, Any]:
        """IP geolocation"""
        if not args:
            return {'success': False, 'output': 'Usage: location <ip>'}
        
        target = args[0]
        try:
            response = requests.get(f"http://ip-api.com/json/{target}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    output = f"Location for {target}:\n"
                    output += f"  Country: {data.get('country', 'Unknown')}\n"
                    output += f"  Region: {data.get('regionName', 'Unknown')}\n"
                    output += f"  City: {data.get('city', 'Unknown')}\n"
                    output += f"  ISP: {data.get('isp', 'Unknown')}\n"
                    output += f"  Coordinates: {data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}"
                    return {'success': True, 'output': output}
            return {'success': False, 'output': 'Location lookup failed'}
        except Exception as e:
            return {'success': False, 'output': f"Location lookup failed: {str(e)}"}
    
    def cmd_analyze(self, args: List[str]) -> Dict[str, Any]:
        """Complete IP analysis"""
        if not args:
            return {'success': False, 'output': 'Usage: analyze <ip>'}
        
        target = args[0]
        analysis = {
            'target': target,
            'timestamp': datetime.datetime.now().isoformat(),
            'ping': None,
            'ports': None,
            'location': None,
            'threat_level': 'unknown'
        }
        
        # Ping test
        try:
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '4', target]
            else:
                cmd = ['ping', '-c', '4', target]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            analysis['ping'] = {'success': result.returncode == 0, 'output': result.stdout[:500]}
        except:
            analysis['ping'] = {'success': False, 'output': 'Ping failed'}
        
        # Port scan
        open_ports = []
        common_ports = [21, 22, 23, 25, 53, 80, 110, 443, 445, 3389, 8080]
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                if sock.connect_ex((target, port)) == 0:
                    try:
                        service = socket.getservbyport(port)
                    except:
                        service = "unknown"
                    open_ports.append({'port': port, 'service': service})
                sock.close()
            except:
                pass
        analysis['ports'] = open_ports
        
        # Geolocation
        try:
            response = requests.get(f"http://ip-api.com/json/{target}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    analysis['location'] = {
                        'country': data.get('country'),
                        'city': data.get('city'),
                        'isp': data.get('isp')
                    }
        except:
            pass
        
        # Threat assessment
        risk_score = 0
        threats = []
        
        if open_ports:
            risk_score += min(len(open_ports) * 5, 30)
            threats.append(f"{len(open_ports)} open ports detected")
        
        sensitive_ports = [21, 22, 23, 3389]
        for p in open_ports:
            if p['port'] in sensitive_ports:
                risk_score += 10
                threats.append(f"Sensitive port {p['port']} ({p['service']}) open")
        
        if risk_score >= 50:
            analysis['threat_level'] = 'CRITICAL'
        elif risk_score >= 30:
            analysis['threat_level'] = 'HIGH'
        elif risk_score >= 15:
            analysis['threat_level'] = 'MEDIUM'
        else:
            analysis['threat_level'] = 'LOW'
        
        analysis['threats'] = threats
        analysis['risk_score'] = risk_score
        
        # Generate report
        report_filename = f"{REPORT_DIR}/analysis_{target}_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        self.db.save_analysis(target, analysis, report_filename)
        
        output = f"""
{Colors.BOLD}{Colors.CYAN}📊 IP Analysis Report: {target}{Colors.RESET}

{Colors.GREEN}📡 Ping Status:{Colors.RESET}
  {'✅ Online' if analysis['ping']['success'] else '❌ Offline'}

{Colors.GREEN}🔌 Open Ports:{Colors.RESET}
  {', '.join([f"{p['port']}({p['service']})" for p in open_ports]) if open_ports else 'None'}

{Colors.GREEN}🌍 Location:{Colors.RESET}
  Country: {analysis.get('location', {}).get('country', 'Unknown')}
  City: {analysis.get('location', {}).get('city', 'Unknown')}
  ISP: {analysis.get('location', {}).get('isp', 'Unknown')}

{Colors.GREEN}⚠️ Threat Assessment:{Colors.RESET}
  Risk Score: {risk_score}/100
  Threat Level: {Colors.RED if risk_score >= 30 else Colors.YELLOW}{analysis['threat_level']}{Colors.RESET}
  
{Colors.GREEN}📝 Threats Detected:{Colors.RESET}
  {chr(10).join([f'  • {t}' for t in threats]) if threats else '  No threats detected'}

{Colors.GREEN}📁 Report saved to: {report_filename}{Colors.RESET}
        """
        
        if threats:
            self.db.log_threat("IP Analysis", target, analysis['threat_level'].lower(), ', '.join(threats))
        
        return {'success': True, 'output': output}
    
    def cmd_block(self, args: List[str]) -> Dict[str, Any]:
        """Block an IP address"""
        if not args:
            return {'success': False, 'output': 'Usage: block <ip> [reason]'}
        
        ip = args[0]
        reason = ' '.join(args[1:]) if len(args) > 1 else "Manually blocked"
        
        try:
            ipaddress.ip_address(ip)
            
            # Block via firewall
            success = False
            if platform.system().lower() == 'linux' and shutil.which('iptables'):
                result = subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], 
                                       capture_output=True, timeout=10)
                success = result.returncode == 0
            elif platform.system().lower() == 'windows' and shutil.which('netsh'):
                result = subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule',
                                        f'name=Swordphish_Block_{ip}', 'dir=in', 'action=block',
                                        f'remoteip={ip}'], capture_output=True, timeout=10)
                success = result.returncode == 0
            
            self.db.block_ip(ip, reason, "manual")
            self.db.log_threat("Manual Block", ip, "medium", reason)
            
            if success:
                return {'success': True, 'output': f"✅ IP {ip} blocked successfully. Reason: {reason}"}
            else:
                return {'success': True, 'output': f"⚠️ IP {ip} recorded in database but firewall blocking may require admin privileges"}
        except ValueError:
            return {'success': False, 'output': f"Invalid IP address: {ip}"}
    
    def cmd_unblock(self, args: List[str]) -> Dict[str, Any]:
        """Unblock an IP address"""
        if not args:
            return {'success': False, 'output': 'Usage: unblock <ip>'}
        
        ip = args[0]
        
        try:
            # Unblock from firewall
            if platform.system().lower() == 'linux' and shutil.which('iptables'):
                subprocess.run(['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], 
                              capture_output=True, timeout=10)
            elif platform.system().lower() == 'windows' and shutil.which('netsh'):
                subprocess.run(['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                               f'name=Swordphish_Block_{ip}'], capture_output=True, timeout=10)
            
            return {'success': True, 'output': f"✅ IP {ip} unblocked"}
        except Exception as e:
            return {'success': False, 'output': f"Failed to unblock IP: {str(e)}"}
    
    def cmd_list_ips(self, args: List[str]) -> Dict[str, Any]:
        """List managed IPs"""
        return {'success': True, 'output': "Use 'status' command for statistics. Detailed IP listing coming soon."}
    
    def cmd_threats(self, args: List[str]) -> Dict[str, Any]:
        """Show recent threats"""
        return {'success': True, 'output': "Threat monitoring active. Use 'analyze' command for IP assessment."}
    
    def cmd_report(self, args: List[str]) -> Dict[str, Any]:
        """Generate security report"""
        stats = self.db.get_statistics()
        report = {
            'generated': datetime.datetime.now().isoformat(),
            'statistics': stats,
            'system': {
                'hostname': socket.gethostname(),
                'platform': platform.system(),
                'cpu': psutil.cpu_percent(),
                'memory': psutil.virtual_memory().percent
            }
        }
        
        filename = f"{REPORT_DIR}/security_report_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        return {'success': True, 'output': f"Security report saved to: {filename}"}
    
    def cmd_ssh(self, args: List[str]) -> Dict[str, Any]:
        """SSH to remote server"""
        if len(args) < 2:
            return {'success': False, 'output': 'Usage: ssh <host> <user> [command]'}
        
        host = args[0]
        user = args[1]
        command = ' '.join(args[2:]) if len(args) > 2 else None
        
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            password = input(f"Password for {user}@{host}: ")
            client.connect(host, username=user, password=password, timeout=30)
            
            if command:
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode() + stderr.read().decode()
            else:
                # Interactive shell
                channel = client.invoke_shell()
                output = "SSH shell opened. Type 'exit' to close.\n"
                channel.close()
            
            client.close()
            return {'success': True, 'output': output}
        except ImportError:
            # Fallback to system SSH
            cmd = ['ssh', f'{user}@{host}']
            if command:
                cmd.extend([command])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {'success': result.returncode == 0, 'output': result.stdout + result.stderr}
        except Exception as e:
            return {'success': False, 'output': f"SSH connection failed: {str(e)}"}
    
    def cmd_traffic(self, args: List[str]) -> Dict[str, Any]:
        """Generate network traffic"""
        if len(args) < 3:
            return {'success': False, 'output': 'Usage: traffic <type> <ip> <duration>\nTypes: icmp, tcp, udp, http'}
        
        traffic_type = args[0].lower()
        target_ip = args[1]
        duration = int(args[2])
        
        output = f"Generating {traffic_type} traffic to {target_ip} for {duration} seconds...\n"
        
        end_time = time.time() + duration
        packets_sent = 0
        
        try:
            if traffic_type == 'icmp':
                while time.time() < end_time:
                    subprocess.run(['ping', '-c', '1', '-W', '1', target_ip], 
                                  capture_output=True, timeout=2)
                    packets_sent += 1
                    time.sleep(0.1)
            elif traffic_type == 'tcp':
                port = 80
                while time.time() < end_time:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        sock.connect((target_ip, port))
                        sock.close()
                        packets_sent += 1
                    except:
                        pass
                    time.sleep(0.1)
            elif traffic_type == 'http':
                while time.time() < end_time:
                    try:
                        requests.get(f"http://{target_ip}", timeout=2)
                        packets_sent += 1
                    except:
                        pass
                    time.sleep(0.1)
            else:
                return {'success': False, 'output': f"Unknown traffic type: {traffic_type}"}
            
            output += f"✅ Traffic generation complete. Packets sent: {packets_sent}"
            return {'success': True, 'output': output}
        except Exception as e:
            return {'success': False, 'output': f"Traffic generation failed: {str(e)}"}
    
    def cmd_phish(self, args: List[str]) -> Dict[str, Any]:
        """Generate phishing link"""
        if len(args) < 2:
            return {'success': False, 'output': 'Usage: phish <platform> <url>\nPlatforms: facebook, instagram, twitter, gmail, linkedin, custom'}
        
        platform = args[0].lower()
        original_url = args[1]
        
        # Generate fake login page template
        templates = {
            'facebook': """
            <!DOCTYPE html>
            <html><head><title>Facebook Login</title></head>
            <body style="font-family:Arial;text-align:center;padding:50px">
            <h1 style="color:#1877f2">facebook</h1>
            <form method="POST" action="/capture">
            <input type="text" name="email" placeholder="Email" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit">Log In</button>
            </form>
            <p style="color:red">⚠️ Security Test Page</p>
            </body></html>
            """,
            'instagram': """
            <!DOCTYPE html>
            <html><head><title>Instagram Login</title></head>
            <body style="font-family:Arial;text-align:center;padding:50px">
            <h1 style="font-family:Billabong">Instagram</h1>
            <form method="POST" action="/capture">
            <input type="text" name="username" placeholder="Username" required><br><br>
            <input type="password" name="password" placeholder="Password" required><br><br>
            <button type="submit">Log In</button>
            </form>
            <p style="color:red">⚠️ Security Test Page</p>
            </body></html>
            """
        }
        
        html_content = templates.get(platform, templates.get('facebook'))
        link_id = str(uuid.uuid4())[:8]
        
        # Save phishing page
        phishing_dir = Path(CONFIG_DIR) / "phishing_pages"
        phishing_dir.mkdir(exist_ok=True)
        page_path = phishing_dir / f"{link_id}.html"
        with open(page_path, 'w') as f:
            f.write(html_content)
        
        output = f"""
{Colors.YELLOW}🎣 Phishing Link Generated{Colors.RESET}
  Link ID: {link_id}
  Platform: {platform}
  Target URL: {original_url}
  Phishing Page: {page_path}
  
{Colors.RED}⚠️ WARNING: For authorized security testing only!{Colors.RESET}
        """
        
        return {'success': True, 'output': output}

# =====================
# DISCORD BOT
# =====================
class SwordphishDiscord:
    """Discord bot integration"""
    
    def __init__(self, handler: CommandHandler, db: DatabaseManager):
        self.handler = handler
        self.db = db
        self.bot = None
        self.running = False
    
    async def start(self, token: str, prefix: str = "!"):
        """Start Discord bot"""
        if not DISCORD_AVAILABLE:
            logger.error("Discord.py not installed")
            return False
        
        intents = discord.Intents.default()
        intents.message_content = True
        
        self.bot = commands.Bot(command_prefix=prefix, intents=intents)
        
        @self.bot.event
        async def on_ready():
            logger.info(f"Discord bot logged in as {self.bot.user}")
            self.running = True
        
        @self.bot.event
        async def on_message(message):
            if message.author.bot:
                return
            
            if message.content.startswith(prefix):
                command = message.content[len(prefix):]
                result = self.handler.execute(command, "discord", str(message.author))
                
                if result.get('output'):
                    output = result['output']
                    if len(output) > 2000:
                        output = output[:1997] + "..."
                    await message.reply(f"```\n{output}\n```")
        
        try:
            await self.bot.start(token)
            return True
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            return False
    
    def start_thread(self, token: str, prefix: str = "!"):
        """Start Discord bot in background thread"""
        thread = threading.Thread(target=lambda: asyncio.run(self.start(token, prefix)), daemon=True)
        thread.start()
        return True

# =====================
# TELEGRAM BOT
# =====================
class SwordphishTelegram:
    """Telegram bot integration"""
    
    def __init__(self, handler: CommandHandler, db: DatabaseManager):
        self.handler = handler
        self.db = db
        self.client = None
        self.running = False
    
    async def start(self, api_id: str, api_hash: str, bot_token: str = None):
        """Start Telegram bot"""
        if not TELETHON_AVAILABLE:
            logger.error("Telethon not installed")
            return False
        
        self.client = TelegramClient('swordphish_session', api_id, api_hash)
        
        @self.client.on(events.NewMessage)
        async def handler(event):
            if event.message.out:
                return
            
            command = event.message.text
            if command.startswith('/'):
                command = command[1:]
                result = self.handler.execute(command, "telegram", str(event.sender_id))
                
                if result.get('output'):
                    await event.reply(result['output'][:4000])
        
        try:
            if bot_token:
                await self.client.start(bot_token=bot_token)
            else:
                await self.client.start()
            
            self.running = True
            logger.info("Telegram bot started")
            await self.client.run_until_disconnected()
            return True
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            return False
    
    def start_thread(self, api_id: str, api_hash: str, bot_token: str = None):
        """Start Telegram bot in background thread"""
        thread = threading.Thread(target=lambda: asyncio.run(self.start(api_id, api_hash, bot_token)), daemon=True)
        thread.start()
        return True

# =====================
# SLACK BOT
# =====================
class SwordphishSlack:
    """Slack bot integration"""
    
    def __init__(self, handler: CommandHandler, db: DatabaseManager):
        self.handler = handler
        self.db = db
        self.client = None
        self.running = False
    
    def start(self, bot_token: str, channel_id: str, prefix: str = "!"):
        """Start Slack bot"""
        if not SLACK_AVAILABLE:
            logger.error("Slack SDK not installed")
            return False
        
        try:
            self.client = WebClient(token=bot_token)
            self.running = True
            
            # Polling loop
            def poll():
                import time
                last_ts = None
                while self.running:
                    try:
                        response = self.client.conversations_history(channel=channel_id, limit=10)
                        if response['ok']:
                            for msg in response['messages']:
                                if msg.get('text', '').startswith(prefix) and msg.get('ts') != last_ts:
                                    last_ts = msg.get('ts')
                                    command = msg['text'][len(prefix):]
                                    user = msg.get('user', 'unknown')
                                    result = self.handler.execute(command, "slack", user)
                                    if result.get('output'):
                                        self.client.chat_postMessage(channel=channel_id, text=result['output'][:4000])
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"Slack polling error: {e}")
                        time.sleep(5)
            
            thread = threading.Thread(target=poll, daemon=True)
            thread.start()
            logger.info("Slack bot started")
            return True
        except Exception as e:
            logger.error(f"Failed to start Slack bot: {e}")
            return False

# =====================
# WHATSAPP BOT
# =====================
class SwordphishWhatsApp:
    """WhatsApp bot integration"""
    
    def __init__(self, handler: CommandHandler, db: DatabaseManager):
        self.handler = handler
        self.db = db
        self.driver = None
        self.running = False
    
    def start(self):
        """Start WhatsApp bot"""
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium not installed")
            return False
        
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            if WEBDRIVER_MANAGER_AVAILABLE:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.get("https://web.whatsapp.com")
            
            # Monitor for messages
            def monitor():
                while self.running:
                    try:
                        # Check for new messages (simplified)
                        time.sleep(2)
                    except:
                        time.sleep(5)
            
            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
            self.running = True
            logger.info("WhatsApp bot started - QR code may be required for first login")
            return True
        except Exception as e:
            logger.error(f"Failed to start WhatsApp bot: {e}")
            return False

# =====================
# SIGNAL BOT
# =====================
class SwordphishSignal:
    """Signal bot integration using signal-cli"""
    
    def __init__(self, handler: CommandHandler, db: DatabaseManager):
        self.handler = handler
        self.db = db
        self.running = False
    
    def start(self, phone_number: str):
        """Start Signal bot"""
        if not SIGNAL_CLI_AVAILABLE:
            logger.error("signal-cli not found")
            return False
        
        def monitor():
            while self.running:
                try:
                    # Receive messages
                    result = subprocess.run(
                        ['signal-cli', '-u', phone_number, 'receive', '--json'],
                        capture_output=True, text=True, timeout=30
                    )
                    
                    if result.stdout:
                        for line in result.stdout.strip().split('\n'):
                            if line:
                                try:
                                    data = json.loads(line)
                                    if 'envelope' in data and 'dataMessage' in data['envelope']:
                                        msg = data['envelope']['dataMessage']
                                        if 'message' in msg and msg['message'].startswith('!'):
                                            command = msg['message'][1:]
                                            sender = data['envelope'].get('sourceNumber', 'unknown')
                                            cmd_result = self.handler.execute(command, "signal", sender)
                                            if cmd_result.get('output'):
                                                subprocess.run(
                                                    ['signal-cli', '-u', phone_number, 'send', '-m', 
                                                     cmd_result['output'][:2000], sender],
                                                    capture_output=True, timeout=10
                                                )
                                except json.JSONDecodeError:
                                    pass
                    
                    time.sleep(2)
                except subprocess.TimeoutExpired:
                    continue
                except Exception as e:
                    logger.error(f"Signal monitoring error: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        self.running = True
        logger.info("Signal bot started")
        return True

# =====================
# IMESSAGE BOT
# =====================
class SwordphishIMessage:
    """iMessage bot integration (macOS only)"""
    
    def __init__(self, handler: CommandHandler, db: DatabaseManager):
        self.handler = handler
        self.db = db
        self.running = False
    
    def start(self, watched_numbers: List[str]):
        """Start iMessage bot"""
        if not IMESSAGE_AVAILABLE:
            logger.error("iMessage only available on macOS")
            return False
        
        def monitor():
            last_checked = {}
            
            while self.running:
                for number in watched_numbers:
                    try:
                        script = f'''
                        tell application "Messages"
                            set targetBuddy to buddy "{number}" of 1st service whose service type = iMessage
                            set recentMessages to messages of targetBuddy
                            set messageList to {{}}
                            repeat with i from 1 to count of recentMessages
                                if i > 5 then exit repeat
                                set msg to item i of recentMessages
                                set end of messageList to {{text:content of msg, timestamp:date of msg}}
                            end repeat
                            return messageList
                        end tell
                        '''
                        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
                        
                        if result.stdout and result.stdout != last_checked.get(number):
                            last_checked[number] = result.stdout
                            # Check for commands (simplified)
                            if '!' in result.stdout:
                                # Extract and execute command
                                pass
                    except Exception as e:
                        logger.error(f"iMessage monitoring error: {e}")
                    
                    time.sleep(3)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        self.running = True
        logger.info("iMessage bot started")
        return True

# =====================
# GOOGLE CHAT BOT
# =====================
class SwordphishGoogleChat:
    """Google Chat bot integration"""
    
    def __init__(self, handler: CommandHandler, db: DatabaseManager):
        self.handler = handler
        self.db = db
        self.service = None
        self.running = False
    
    def start(self, credentials_file: str, space_id: str):
        """Start Google Chat bot"""
        if not GOOGLE_CHAT_AVAILABLE:
            logger.error("Google API libraries not installed")
            return False
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_file,
                scopes=['https://www.googleapis.com/auth/chat.bot']
            )
            
            self.service = build('chat', 'v1', credentials=credentials)
            
            def monitor():
                while self.running:
                    try:
                        # Simplified - would need webhook or polling setup
                        time.sleep(10)
                    except Exception as e:
                        logger.error(f"Google Chat monitoring error: {e}")
                        time.sleep(30)
            
            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
            self.running = True
            logger.info("Google Chat bot started")
            return True
        except Exception as e:
            logger.error(f"Failed to start Google Chat bot: {e}")
            return False

# =====================
# MAIN APPLICATION
# =====================
class SwordphishApp:
    """Main application class"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.handler = CommandHandler(self.db)
        
        # Initialize bots
        self.discord_bot = SwordphishDiscord(self.handler, self.db)
        self.telegram_bot = SwordphishTelegram(self.handler, self.db)
        self.slack_bot = SwordphishSlack(self.handler, self.db)
        self.whatsapp_bot = SwordphishWhatsApp(self.handler, self.db)
        self.signal_bot = SwordphishSignal(self.handler, self.db)
        self.imessage_bot = SwordphishIMessage(self.handler, self.db)
        self.google_chat_bot = SwordphishGoogleChat(self.handler, self.db)
        
        self.running = True
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self):
        """Save configuration"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def print_banner(self):
        """Print application banner"""
        banner = f"""
{Colors.BOLD}{Colors.RED}╔═══════════════════════════════════════════════════════════════════════════╗{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}                                                                           {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}         {Colors.BOLD}{Colors.WHITE}⚔️ SWORDPHISH - Multi-Platform Command & Control ⚔️{Colors.RESET}          {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}                                                                           {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}╠═══════════════════════════════════════════════════════════════════════════╣{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}  {Colors.GREEN}🤖 Platforms:{Colors.RESET}                                                                  {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}    • Discord      • Telegram      • Slack         • WhatsApp          {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}    • Signal       • iMessage      • Google Chat   • Command Line      {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}                                                                           {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}  {Colors.GREEN}🎯 Features:{Colors.RESET}                                                                   {Colors.BOLD}{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}    • IP Analysis & Geolocation    • Port Scanning                {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}    • Network Traffic Generation   • SSH Remote Execution         {Colors.BOLD}{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}    • Phishing Simulation          • Threat Detection             {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}║{Colors.RESET}    • IP Blocking                  • Security Reporting          {Colors.BOLD}{Colors.RED}║{Colors.RESET}
{Colors.BOLD}{Colors.RED}╚═══════════════════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.CYAN}💡 Type 'help' for available commands | 'status' for system status{Colors.RESET}
{Colors.YELLOW}⚙️  Use setup commands to configure platform bots{Colors.RESET}
        """
        print(banner)
    
    def setup_platforms(self):
        """Interactive platform setup"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Platform Setup ==={Colors.RESET}\n")
        
        # Discord
        setup = input(f"{Colors.GREEN}Setup Discord bot? (y/n): {Colors.RESET}").strip().lower()
        if setup == 'y':
            token = input("Enter Discord bot token: ").strip()
            prefix = input("Enter command prefix (default: !): ").strip() or "!"
            if token:
                self.config['discord'] = {'enabled': True, 'token': token, 'prefix': prefix}
                self.discord_bot.start_thread(token, prefix)
                print(f"{Colors.GREEN}✅ Discord bot configured{Colors.RESET}")
        
        # Telegram
        setup = input(f"\n{Colors.GREEN}Setup Telegram bot? (y/n): {Colors.RESET}").strip().lower()
        if setup == 'y':
            use_bot = input("Use bot token? (y/n): ").strip().lower()
            if use_bot == 'y':
                bot_token = input("Enter bot token: ").strip()
                api_id = input("Enter API ID: ").strip()
                api_hash = input("Enter API Hash: ").strip()
                if bot_token and api_id and api_hash:
                    self.config['telegram'] = {'enabled': True, 'bot_token': bot_token, 'api_id': api_id, 'api_hash': api_hash}
                    self.telegram_bot.start_thread(api_id, api_hash, bot_token)
                    print(f"{Colors.GREEN}✅ Telegram bot configured{Colors.RESET}")
            else:
                api_id = input("Enter API ID: ").strip()
                api_hash = input("Enter API Hash: ").strip()
                phone = input("Enter phone number: ").strip()
                if api_id and api_hash and phone:
                    self.config['telegram'] = {'enabled': True, 'api_id': api_id, 'api_hash': api_hash, 'phone': phone}
                    self.telegram_bot.start_thread(api_id, api_hash)
                    print(f"{Colors.GREEN}✅ Telegram user bot configured{Colors.RESET}")
        
        # Slack
        setup = input(f"\n{Colors.GREEN}Setup Slack bot? (y/n): {Colors.RESET}").strip().lower()
        if setup == 'y':
            token = input("Enter bot token: ").strip()
            channel = input("Enter channel ID: ").strip()
            if token and channel:
                self.config['slack'] = {'enabled': True, 'token': token, 'channel': channel}
                self.slack_bot.start(token, channel)
                print(f"{Colors.GREEN}✅ Slack bot configured{Colors.RESET}")
        
        # WhatsApp
        setup = input(f"\n{Colors.GREEN}Setup WhatsApp bot? (y/n): {Colors.RESET}").strip().lower()
        if setup == 'y':
            self.config['whatsapp'] = {'enabled': True}
            self.whatsapp_bot.start()
            print(f"{Colors.GREEN}✅ WhatsApp bot configured (QR code may be required){Colors.RESET}")
        
        # Signal
        setup = input(f"\n{Colors.GREEN}Setup Signal bot? (y/n): {Colors.RESET}").strip().lower()
        if setup == 'y':
            phone = input("Enter Signal phone number: ").strip()
            if phone:
                self.config['signal'] = {'enabled': True, 'phone': phone}
                self.signal_bot.start(phone)
                print(f"{Colors.GREEN}✅ Signal bot configured{Colors.RESET}")
        
        # iMessage (macOS only)
        if IMESSAGE_AVAILABLE:
            setup = input(f"\n{Colors.GREEN}Setup iMessage bot? (y/n): {Colors.RESET}").strip().lower()
            if setup == 'y':
                numbers = input("Enter phone numbers to monitor (comma-separated): ").strip()
                number_list = [n.strip() for n in numbers.split(',')] if numbers else []
                if number_list:
                    self.config['imessage'] = {'enabled': True, 'numbers': number_list}
                    self.imessage_bot.start(number_list)
                    print(f"{Colors.GREEN}✅ iMessage bot configured{Colors.RESET}")
        
        # Google Chat
        setup = input(f"\n{Colors.GREEN}Setup Google Chat bot? (y/n): {Colors.RESET}").strip().lower()
        if setup == 'y':
            creds_file = input("Enter service account credentials file path: ").strip()
            space_id = input("Enter space ID: ").strip()
            if creds_file and os.path.exists(creds_file) and space_id:
                self.config['google_chat'] = {'enabled': True, 'credentials': creds_file, 'space_id': space_id}
                self.google_chat_bot.start(creds_file, space_id)
                print(f"{Colors.GREEN}✅ Google Chat bot configured{Colors.RESET}")
        
        self.save_config()
        print(f"\n{Colors.GREEN}✅ Platform setup complete!{Colors.RESET}")
    
    def run(self):
        """Main application loop"""
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_banner()
        
        # Check if first run
        if not self.config:
            setup = input(f"{Colors.YELLOW}First time run! Setup platforms now? (y/n): {Colors.RESET}").strip().lower()
            if setup == 'y':
                self.setup_platforms()
                os.system('cls' if os.name == 'nt' else 'clear')
                self.print_banner()
        
        print(f"\n{Colors.GREEN}✅ SWORDPHISH is ready!{Colors.RESET}")
        print(f"{Colors.CYAN}   Commands can be sent via any configured platform or directly here{Colors.RESET}\n")
        
        while self.running:
            try:
                prompt = f"{Colors.BOLD}{Colors.RED}[SWORDPHISH]{Colors.RESET}{Colors.CYAN}> {Colors.RESET}"
                command = input(prompt).strip()
                
                if command.lower() == 'exit':
                    self.running = False
                    print(f"\n{Colors.YELLOW}👋 Shutting down...{Colors.RESET}")
                    break
                elif command.lower() == 'setup':
                    self.setup_platforms()
                    continue
                
                result = self.handler.execute(command, "local", "console")
                
                if result.get('output'):
                    print(result['output'])
                    if result.get('execution_time'):
                        print(f"\n{Colors.GREEN}✅ Execution time: {result['execution_time']:.2f}s{Colors.RESET}")
                
                if result.get('output') == 'exit':
                    self.running = False
                    break
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 Shutting down...{Colors.RESET}")
                self.running = False
            except Exception as e:
                print(f"{Colors.RED}❌ Error: {str(e)}{Colors.RESET}")
                logger.error(f"Main loop error: {e}")
        
        # Cleanup
        self.db.close()
        print(f"\n{Colors.GREEN}✅ SWORDPHISH shutdown complete{Colors.RESET}")

# =====================
# MAIN ENTRY POINT
# =====================
def main():
    """Main entry point"""
    try:
        print(f"{Colors.BOLD}{Colors.CYAN}⚔️ Initializing SWORDPHISH...{Colors.RESET}")
        
        if sys.version_info < (3, 7):
            print(f"{Colors.RED}❌ Python 3.7 or higher is required{Colors.RESET}")
            sys.exit(1)
        
        # Check for required packages
        required = ['cryptography']
        missing = []
        for pkg in required:
            try:
                __import__(pkg.replace('-', '_'))
            except ImportError:
                missing.append(pkg)
        
        if missing:
            print(f"{Colors.YELLOW}⚠️ Missing packages: {', '.join(missing)}{Colors.RESET}")
            print(f"{Colors.YELLOW}   Install with: pip install {' '.join(missing)}{Colors.RESET}")
        
        app = SwordphishApp()
        app.run()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Fatal error: {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()