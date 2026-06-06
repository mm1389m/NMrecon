#!/usr/bin/env bash
# NightMare Recon — setup.sh
# Automated setup for Debian/Ubuntu/Kali/Parrot/Arch/Fedora
# Developed by mm1389m  |  v1.0.0

set -euo pipefail

RED='\033[0;31m'   GREEN='\033[0;32m'   YELLOW='\033[1;33m'
BOLD='\033[1m'     DIM='\033[2m'         NC='\033[0m'
BGREEN='\033[1;92m'

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORDLIST_DIR="$TOOL_DIR/wordlists"

banner() {
    echo -e "${BGREEN}"
    cat << 'ART'
 ███╗   ██╗███╗   ███╗██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ████╗  ██║████╗ ████║██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██╔██╗ ██║██╔████╔██║██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██║╚██╗██║██║╚██╔╝██║██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║ ╚████║██║ ╚═╝ ██║██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═══╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
ART
    echo -e "${NC}"
    echo -e "  ${BOLD}NightMare Recon — Setup Script${NC}"
    echo -e "  ${DIM}Developed by mm1389m  |  v1.0.0${NC}"
    echo -e "  ${DIM}$(printf '─%.0s' {1..50})${NC}"
    echo
}

log_ok()   { echo -e "  ${BGREEN}✔${NC}  $1"; }
log_warn() { echo -e "  ${YELLOW}!${NC}  $1"; }
log_err()  { echo -e "  ${RED}✘${NC}  $1"; }
log_info() { echo -e "  ${DIM}▶${NC}  $1"; }
section()  { echo; echo -e "  ${BGREEN}▶  $1${NC}"; echo -e "  ${DIM}$(printf '─%.0s' {1..46})${NC}"; }

detect_os() {
    if   [ -f /etc/debian_version ];  then echo "debian"
    elif [ -f /etc/arch-release ];    then echo "arch"
    elif [ -f /etc/fedora-release ];  then echo "fedora"
    elif [ -f /etc/redhat-release ];  then echo "redhat"
    elif [[ "$OSTYPE" == "darwin"* ]]; then echo "macos"
    else echo "unknown"
    fi
}

install_system_pkg() {
    local pkg="$1"
    local os
    os=$(detect_os)
    log_info "Installing $pkg..."
    case "$os" in
        debian)  sudo apt-get install -y -q "$pkg" 2>/dev/null ;;
        arch)    sudo pacman -S --noconfirm --quiet "$pkg" 2>/dev/null ;;
        fedora)  sudo dnf install -y -q "$pkg" 2>/dev/null ;;
        redhat)  sudo yum install -y -q "$pkg" 2>/dev/null ;;
        macos)   brew install "$pkg" 2>/dev/null ;;
        *)       log_warn "Unknown OS — install $pkg manually." ;;
    esac
}

check_python() {
    section "Python Environment"
    if ! command -v python3 &>/dev/null; then
        log_err "python3 not found."
        install_system_pkg python3
    else
        local ver
        ver=$(python3 --version 2>&1 | awk '{print $2}')
        log_ok "python3 $ver"
    fi

    local req_minor=9
    local actual
    actual=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [ "$actual" -lt "$req_minor" ]; then
        log_warn "Python 3.$req_minor+ recommended. You have 3.$actual."
    fi

    if ! command -v pip3 &>/dev/null; then
        log_warn "pip3 not found — installing..."
        install_system_pkg python3-pip
    else
        log_ok "pip3 found"
    fi
}

install_python_deps() {
    section "Python Dependencies"
    local requirements="$TOOL_DIR/requirements.txt"
    if [ ! -f "$requirements" ]; then
        log_err "requirements.txt not found at $requirements"
        return 1
    fi
    log_info "Installing from requirements.txt..."
    if pip3 install -q -r "$requirements" --break-system-packages 2>/dev/null \
       || pip3 install -q -r "$requirements" 2>/dev/null; then
        log_ok "Python dependencies installed."
    else
        log_err "pip3 install failed. Try: pip3 install -r requirements.txt"
    fi
}

check_system_tools() {
    section "System Tools"
    local tools=("nmap" "whois" "dig" "curl" "git")
    for tool in "${tools[@]}"; do
        if command -v "$tool" &>/dev/null; then
            local ver
            ver=$("$tool" --version 2>&1 | head -1 | awk '{print $NF}' | tr -d 'v')
            log_ok "$tool  (found)"
        else
            log_warn "$tool not found — installing..."
            case "$tool" in
                dig)   install_system_pkg dnsutils ;;
                *)     install_system_pkg "$tool" ;;
            esac
            if command -v "$tool" &>/dev/null; then
                log_ok "$tool installed."
            else
                log_err "$tool installation failed — install manually."
            fi
        fi
    done
}

check_optional_tools() {
    section "Optional Go-based Tools"
    echo -e "  ${DIM}These improve results significantly but aren't required.${NC}"
    echo

    local go_tools=(
        "subfinder:go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
        "httpx:go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest"
        "waybackurls:go install -v github.com/tomnomnom/waybackurls@latest"
        "ffuf:go install -v github.com/ffuf/ffuf/v2@latest"
        "nuclei:go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
        "naabu:go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"
    )

    local has_go=false
    if command -v go &>/dev/null; then
        has_go=true
        log_ok "Go runtime found — $(go version | awk '{print $3}')"
    else
        log_warn "Go not found — optional tools will be skipped."
        log_warn "Install Go: https://go.dev/doc/install"
    fi

    for entry in "${go_tools[@]}"; do
        local name="${entry%%:*}"
        local cmd="${entry#*:}"
        if command -v "$name" &>/dev/null; then
            log_ok "$name  (already installed)"
        elif [ "$has_go" = true ]; then
            log_info "Installing $name..."
            if eval "$cmd" &>/dev/null; then
                log_ok "$name installed."
            else
                log_warn "$name failed — install manually."
            fi
        else
            log_warn "$name  (skipped — Go not found)"
        fi
    done
}

build_wordlists() {
    section "Wordlists"
    mkdir -p "$WORDLIST_DIR"

    local sub_wl="$WORDLIST_DIR/subdomains.txt"
    if [ ! -f "$sub_wl" ] || [ "$(wc -l < "$sub_wl")" -lt 1000 ]; then
        log_info "Building subdomain wordlist..."

        cat > "$sub_wl" << 'WORDS'
www
mail
ftp
ssh
vpn
api
dev
staging
test
beta
admin
app
portal
login
auth
secure
static
cdn
media
img
images
assets
files
upload
download
blog
forum
shop
store
support
help
docs
wiki
git
gitlab
github
jenkins
jira
confluence
kibana
grafana
prometheus
monitoring
status
health
mx
smtp
pop
imap
webmail
owa
outlook
exchange
ns1
ns2
ns3
dns
dns1
dns2
cpanel
whm
plesk
webdisk
autodiscover
autoconfig
remote
vpn2
vpnssl
fw
firewall
proxy
waf
lb
lb1
lb2
web
web1
web2
web3
db
db1
db2
database
mysql
postgres
redis
mongo
elastic
solr
kafka
rabbit
queue
cache
memcache
s3
backup
bak
old
new
internal
intranet
extranet
corp
office
hr
crm
erp
bi
analytics
data
devel
qa
uat
prod
production
preprod
pre-prod
sandbox
lab
ops
devops
cloud
k8s
docker
registry
ci
cd
deploy
release
build
repo
svn
hg
puppet
ansible
chef
salt
nagios
zabbix
splunk
elk
logstash
siem
waf2
ids
ips
scanner
pentest
bugbounty
WORDS
        log_ok "Subdomain wordlist: $(wc -l < "$sub_wl") entries"
    else
        log_ok "Subdomain wordlist already exists ($(wc -l < "$sub_wl") entries)"
    fi

    if command -v git &>/dev/null; then
        local seclists_sub="$WORDLIST_DIR/seclists_subdomains.txt"
        if [ ! -f "$seclists_sub" ]; then
            log_info "Fetching SecLists subdomain wordlist..."
            local url="https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/subdomains-top1million-5000.txt"
            if curl -s --max-time 15 -o "$seclists_sub" "$url" 2>/dev/null && [ -s "$seclists_sub" ]; then
                log_ok "SecLists wordlist: $(wc -l < "$seclists_sub") entries"
                cat "$seclists_sub" >> "$sub_wl"
                sort -u "$sub_wl" -o "$sub_wl"
                log_ok "Merged — total: $(wc -l < "$sub_wl") unique entries"
            else
                rm -f "$seclists_sub"
                log_warn "Could not fetch SecLists — using built-in wordlist."
            fi
        fi
    fi
}

create_symlink() {
    section "Symlink (optional)"
    local target="/usr/local/bin/NMrecon"
    local src="$TOOL_DIR/NMrecon.py"

    if command -v sudo &>/dev/null && [ -w /usr/local/bin ]; then
        if sudo ln -sf "$src" "$target" 2>/dev/null; then
            sudo chmod +x "$target"
            log_ok "Symlink created: $target  →  $src"
            log_ok "You can now run: NMrecon"
        else
            log_warn "Could not create symlink. Run manually: python3 NMrecon.py"
        fi
    else
        log_warn "Skipping symlink (no sudo / /usr/local/bin not writable)"
        log_info "Add to your .bashrc:  alias NMrecon='python3 $src'"
    fi

    chmod +x "$src"
}

verify_install() {
    section "Verification"
    local ok=true

    if python3 -c "import rich, requests" &>/dev/null; then
        log_ok "Core Python packages: OK"
    else
        log_err "Core Python packages missing — check pip3 output above."
        ok=false
    fi

    if python3 -c "
import sys
sys.path.insert(0, '$TOOL_DIR')
from core.banner  import console, VERSION
from core.config  import sanitize_domain
from utils.ui     import make_spinner
print('modules: OK')
" 2>/dev/null; then
        log_ok "NMrecon modules: OK"
    else
        log_err "Module import failed — check errors above."
        ok=false
    fi

    if [ "$ok" = true ]; then
        echo
        echo -e "  ${BGREEN}${BOLD}Setup complete!${NC}"
        echo -e "  ${DIM}Run the tool:${NC}  python3 $TOOL_DIR/NMrecon.py"
    else
        echo
        log_err "Setup completed with errors. Review the output above."
    fi
}

main() {
    banner
    check_python
    install_python_deps
    check_system_tools
    check_optional_tools
    build_wordlists
    create_symlink
    verify_install
    echo
}

main "$@"
