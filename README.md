# swordphish

<img width="936" height="524" alt="swordphish" src="https://github.com/user-attachments/assets/b9db61e1-e8b7-4d25-95d6-98e722538a80" />

[![GitHub stars](https://img.shields.io/github/stars/Iankulani/swordphish?style=for-the-badge&logo=github)](https://github.com/Iankulani/swordphish/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Iankulani/swordphish?style=for-the-badge&logo=github)](https://github.com/Iankulani/swordphish/network)
[![GitHub watchers](https://img.shields.io/github/watchers/Iankulani/swordphish?style=for-the-badge&logo=github)](https://github.com/Iankulani/swordphish/watchers)
[![GitHub contributors](https://img.shields.io/github/contributors/Iankulani/swordphish?style=for-the-badge&logo=github)](https://github.com/Iankulani/swordphish/graphs/contributors)
[![GitHub last commit](https://img.shields.io/github/last-commit/Iankulani/swordphish?style=for-the-badge&logo=git)](https://github.com/Iankulani/swordphish/commits/main)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-blue?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/Iankulani/swordphish)
[![Python](https://img.shields.io/badge/python-3.x-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-supported-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

Swordfish is a powerful cybersecurity tool designed to support security awareness training, authorized security assessments, and cyber defense exercises. The tool enables security professionals, trainers, and organizations to manage and coordinate cybersecurity activities through multiple communication channels, including Telegram, Slack, Discord, iMessage, web applications, and other messaging platforms.

Built to simplify cybersecurity operations, Swordfish allows users to send commands, automate training scenarios, monitor engagement, and collect actionable security metrics from a centralized interface. The tool helps organizations evaluate their security posture by conducting controlled security awareness campaigns, phishing simulations, and social engineering assessments within authorized environments.

Swordfish is designed for use in red team, blue team, and purple team exercises, providing realistic scenarios that help security professionals understand modern attack techniques and improve defensive capabilities. Security teams can use the tool to test employee awareness, measure organizational readiness, and strengthen incident response procedures.

The tool features automation, reporting, campaign management, user tracking, and real-time monitoring capabilities, allowing security teams to efficiently manage large-scale cybersecurity training initiatives. Detailed analytics and reporting functions provide valuable insights that help organizations identify weaknesses and improve security practices.

Swordfish is suitable for cybersecurity consultants, managed security providers, educational institutions, corporate security teams, and professional training organizations. By integrating multiple communication platforms into a single tool, Swordfish streamlines security operations and improves the effectiveness of cybersecurity awareness programs.

Developed with security, flexibility, and scalability in mind, Swordfish supports organizations of all sizes, from small businesses to large enterprises. The tool is intended exclusively for authorized cybersecurity testing, security awareness training, and defensive security activities, helping organizations build stronger security cultures and improve resilience against evolving cyber threats.

# How ti clone the repo
```bash
git clone https://github.com/Iankulani/swordphish.git
cd swordphish
```


# How to run

```bash
python swordphish.py
```
   


# Run as Administrator
install.bat
Docker
bash
# Build and run with Docker
```bash
docker build -t swordphish .
docker run -it --rm --cap-add=NET_ADMIN swordphish
```
# Or use docker-compose
```bash
docker-compose up -d
```
# 🔧 Configuration
First run will prompt for platform setup

Configuration saved in .swordphish/config.json

Database stored in .swordphish/swordphish.db

Platform Setup

# Interactive setup
 ```bash     
python3 swordphish.py
```
> setup

# Or edit config directly
nano .swordphish/config.json
# 📝 Usage

# Basic Commands
# System commands
```bash
help                    # Show all commands
status                  # System status
system                  # System information
```
# Network analysis
```bash
analyze 192.168.1.1    # Complete IP analysis
scan 192.168.1.1       # Port scan
ping 8.8.8.8          # Ping test
```
# Security
```bash
block 192.168.1.100    # Block IP
threats                # View threats
report                 # Generate report
```
# Traffic generation
```bash
traffic icmp 8.8.8.8 10   # ICMP flood
traffic tcp 192.168.1.1 5  # TCP connection test
```
# Platform commands (when configured)
```bash
!analyze 8.8.8.8      # via Discord
/scan 192.168.1.1     # via Telegram
```
# 🐳 Docker Deployment
Production Setup
yaml
# docker-compose.yml
version: '3.8'
services:
  swordphish:
    image: swordphish:latest
    container_name: swordphish
    restart: always
    volumes:
      - ./data:/app/.swordphish
      - ./reports:/app/swordphish_reports
    cap_add:
      - NET_ADMIN
      - NET_RAW
🧪 Testing

# Run all tests

```bash
make test
```
# Quick tests
```bash
python3 test_commands.py
```
# Check requirements
```bash
python3 requirements_check.py
```
# 📊 CI/CD Pipeline

# GitLab CI/CD included:

* SAST security scanning

* Dependency scanning

* Secret detection

* Unit & integration tests

* Docker build & push

* Staging/Production deployment

# Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Iankulani/swordphish&type=Date)](https://star-history.com/#Iankulani/swordphish&Date)
  
