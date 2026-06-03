#!/bin/bash
# SWORDPHISH - Automated Installation Script
# Supports: Debian/Ubuntu, RHEL/CentOS, Alpine, macOS

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
SWORDPHISH_DIR="/opt/swordphish"
SWORDPHISH_USER="swordphish"
PYTHON_VERSION="3.11"
INSTALL_TYPE="${1:-full}"  # full, minimal, docker

print_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║      ⚔️ SWORDPHISH - Advanced C2 Installation Script ⚔️      ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    EOF
    echo -e "${NC}"
}

detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        VER=$(sw_vers -productVersion)
    else
        OS="unknown"
    fi
    
    echo -e "${GREEN}✓ Detected OS: $OS $VER${NC}"
}

install_dependencies_debian() {
    echo -e "${YELLOW}Installing dependencies for Debian/Ubuntu...${NC}"
    apt-get update
    apt-get install -y \
        python3 python3-pip python3-venv \
        git curl wget \
        build-essential libssl-dev libffi-dev \
        nmap whois traceroute \
        iptables openssh-client \
        chromium chromium-driver \
        postgresql-client redis-tools \
        jq
}

install_dependencies_rhel() {
    echo -e "${YELLOW}Installing dependencies for RHEL/CentOS...${NC}"
    yum install -y epel-release
    yum install -y \
        python3 python3-pip \
        git curl wget \
        gcc openssl-devel libffi-devel \
        nmap whois traceroute \
        iptables openssh-clients \
        chromium chromium-headless \
        jq
}

install_dependencies_alpine() {
    echo -e "${YELLOW}Installing dependencies for Alpine...${NC}"
    apk add --no-cache \
        python3 py3-pip \
        git curl wget \
        gcc musl-dev libffi-dev openssl-dev \
        nmap whois traceroute \
        iptables openssh-client \
        chromium chromium-chromedriver \
        jq
}

install_dependencies_macos() {
    echo -e "${YELLOW}Installing dependencies for macOS...${NC}"
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install \
        python3 \
        git \
        nmap \
        whois \
        traceroute \
        chromedriver \
        jq
}

install_python_packages() {
    echo -e "${YELLOW}Installing Python packages...${NC}"
    
    # Create virtual environment
    python3 -m venv "$SWORDPHISH_DIR/venv"
    source "$SWORDPHISH_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install requirements based on type
    if [[ "$INSTALL_TYPE" == "minimal" ]]; then
        pip install -r "$SWORDPHISH_DIR/requirements_minimal.txt"
    else
        pip install -r "$SWORDPHISH_DIR/requirements.txt"
    fi
    
    deactivate
    echo -e "${GREEN}✓ Python packages installed${NC}"
}

create_user() {
    if ! id -u "$SWORDPHISH_USER" &>/dev/null; then
        echo -e "${YELLOW}Creating user: $SWORDPHISH_USER${NC}"
        useradd -r -s /bin/bash -d "$SWORDPHISH_DIR" "$SWORDPHISH_USER"
    fi
}

setup_directories() {
    echo -e "${YELLOW}Setting up directories...${NC}"
    
    mkdir -p "$SWORDPHISH_DIR"/{.swordphish,reports,logs,config}
    mkdir -p "$SWORDPHISH_DIR/data"/{database,phishing_pages,cache}
    
    chown -R "$SWORDPHISH_USER":"$SWORDPHISH_USER" "$SWORDPHISH_DIR"
    chmod 750 "$SWORDPHISH_DIR"
}

create_config() {
    echo -e "${YELLOW}Creating default configuration...${NC}"
    
    cat > "$SWORDPHISH_DIR/config/config.json" << EOF
{
    "version": "1.0.0",
    "install_type": "$INSTALL_TYPE",
    "install_date": "$(date -Iseconds)",
    "database": {
        "type": "sqlite",
        "path": "$SWORDPHISH_DIR/.swordphish/swordphish.db"
    },
    "logging": {
        "level": "INFO",
        "file": "$SWORDPHISH_DIR/logs/swordphish.log"
    },
    "platforms": {
        "discord": {"enabled": false},
        "telegram": {"enabled": false},
        "slack": {"enabled": false},
        "whatsapp": {"enabled": false},
        "signal": {"enabled": false},
        "imessage": {"enabled": false},
        "google_chat": {"enabled": false}
    }
}
EOF
    
    chown "$SWORDPHISH_USER":"$SWORDPHISH_USER" "$SWORDPHISH_DIR/config/config.json"
}

create_systemd_service() {
    if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]] || [[ "$OS" == "rhel" ]] || [[ "$OS" == "centos" ]]; then
        echo -e "${YELLOW}Creating systemd service...${NC}"
        
        cat > /etc/systemd/system/swordphish.service << EOF
[Unit]
Description=SWORDPHISH Command & Control Tool
After=network.target

[Service]
Type=simple
User=$SWORDPHISH_USER
Group=$SWORDPHISH_USER
WorkingDirectory=$SWORDPHISH_DIR
Environment="PATH=$SWORDPHISH_DIR/venv/bin"
ExecStart=$SWORDPHISH_DIR/venv/bin/python3 $SWORDPHISH_DIR/swordphish.py --daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        echo -e "${GREEN}✓ Created systemd service${NC}"
        echo -e "  Start with: ${BLUE}systemctl start swordphish${NC}"
        echo -e "  Enable at boot: ${BLUE}systemctl enable swordphish${NC}"
    fi
}

create_launcher_script() {
    echo -e "${YELLOW}Creating launcher script...${NC}"
    
    cat > /usr/local/bin/swordphish << EOF
#!/bin/bash
# SWORDPHISH Launcher

source $SWORDPHISH_DIR/venv/bin/activate
python3 $SWORDPHISH_DIR/swordphish.py "\$@"
EOF
    
    chmod +x /usr/local/bin/swordphish
}

run_verification() {
    echo -e "${YELLOW}Verifying installation...${NC}"
    
    source "$SWORDPHISH_DIR/venv/bin/activate"
    python3 "$SWORDPHISH_DIR/requirements_check.py"
    deactivate
}

main() {
    print_banner
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}This script must be run as root!${NC}"
        exit 1
    fi
    
    detect_os
    
    # Create installation directory
    mkdir -p "$SWORDPHISH_DIR"
    
    # Copy files
    echo -e "${YELLOW}Copying files to $SWORDPHISH_DIR...${NC}"
    cp -r ./* "$SWORDPHISH_DIR/" 2>/dev/null || true
    
    # Install dependencies based on OS
    case "$OS" in
        ubuntu|debian)
            install_dependencies_debian
            ;;
        rhel|centos|fedora)
            install_dependencies_rhel
            ;;
        alpine)
            install_dependencies_alpine
            ;;
        macos)
            install_dependencies_macos
            ;;
        *)
            echo -e "${RED}Unsupported OS: $OS${NC}"
            exit 1
            ;;
    esac
    
    # Install Python packages
    install_python_packages
    
    # Setup user and directories
    create_user
    setup_directories
    create_config
    
    # Create service and launcher
    create_systemd_service
    create_launcher_script
    
    # Verify installation
    run_verification
    
    echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ SWORDPHISH Installation Complete!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e ""
    echo -e "Installation Directory: ${BLUE}$SWORDPHISH_DIR${NC}"
    echo -e ""
    echo -e "Quick Start:"
    echo -e "  ${BLUE}sudo -u $SWORDPHISH_USER $SWORDPHISH_DIR/venv/bin/python3 $SWORDPHISH_DIR/swordphish.py${NC}"
    echo -e "  ${BLUE}swordphish${NC}  (if launcher was created)"
    echo -e ""
    echo -e "Run as service:"
    echo -e "  ${BLUE}systemctl start swordphish${NC}"
    echo -e "  ${BLUE}journalctl -u swordphish -f${NC}"
    echo -e ""
    echo -e "Documentation: ${BLUE}$SWORDPHISH_DIR/README.md${NC}"
}

main "$@"