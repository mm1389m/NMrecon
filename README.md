<div align="center" dir="ltr">

```
███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗███╗   ███╗ █████╗ ██████╗ ███████╗
████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝████╗ ████║██╔══██╗██╔══██╗██╔════╝
██╔██╗ ██║██║██║  ███╗███████║   ██║   ██╔████╔██║███████║██████╔╝█████╗
██║╚██╗██║██║██║   ██║██╔══██║   ██║   ██║╚██╔╝██║██╔══██║██╔══██╗██╔══╝
██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██║ ╚═╝ ██║██║  ██║██║  ██║███████╗
╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝

 ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
```

**Professional Recon & Bug Bounty Toolkit**

`Developed by mm1389m` &nbsp;|&nbsp; `v1.0.0` &nbsp;|&nbsp; `Python 3.9+` &nbsp;|&nbsp; `Linux`

---

## فارسی | Persian

### درباره ابزار

**NightMare Recon** یک ابزار حرفه‌ای و ماژولار برای Recon و Bug Bounty است که توسط `mm1389m` توسعه داده شده.
این ابزار مراحل اطلاعات‌یابی اولیه (reconnaissance) را به صورت کاملاً خودکار انجام می‌دهد.

### قابلیت‌ها

| ماژول | توضیح |
|---|---|
| **Full Recon** | اجرای همه ماژول‌ها روی یک دامنه |
| **Subdomain Enum** | کشف subdomain از crt.sh + subfinder + DNS brute-force |
| **DNS Lookup** | دریافت رکوردهای A/AAAA/MX/NS/TXT/SOA/CAA + تلاش AXFR |
| **WHOIS** | اطلاعات ثبت دامنه، registrar، تاریخ‌ها |
| **Port Scanner** | اسکن با nmap و ۵ پروفایل مختلف |
| **Web Recon** | تکنولوژی، هدرهای امنیتی، SSL، WAF، ایمیل، robots.txt |
| **Live Host Check** | بررسی موازی host های زنده |
| **Wayback URLs** | آرشیو URL از Wayback Machine |
| **IP Geolocation** | موقعیت جغرافیایی IP/دامنه |

### نصب سریع

```bash
git clone https://github.com/mm1389m/NMrecon.git
cd NMrecon
chmod +x setup.sh
bash setup.sh
```

### اجرا

```bash
python3 NMrecon.py                          # منوی تعاملی
python3 NMrecon.py -d example.com           # recon کامل
python3 NMrecon.py -d example.com -m ports  # فقط port scan
python3 NMrecon.py --check-tools            # بررسی ابزارها
```

---

## English

### Overview

**NightMare Recon** (`NMrecon`) is a modular, terminal-native reconnaissance framework for bug bounty hunters and security researchers. It chains WHOIS, DNS, subdomain discovery, port scanning, web fingerprinting, SSL inspection, and Wayback URL harvesting into a single automated pipeline — with clean HTML, JSON, and text reports.

### Features

| Module | Description |
|---|---|
| **Full Recon** | Runs all modules in sequence, saves combined report |
| **Subdomain Enum** | crt.sh (passive) + subfinder + DNS brute-force |
| **Live Check** | Concurrent HTTP/HTTPS probing with title & status |
| **DNS Lookup** | A, AAAA, MX, NS, TXT, CNAME, SOA, CAA + AXFR probe |
| **WHOIS** | Registrar, dates, name servers, status flags |
| **Port Scanner** | Nmap with 5 profiles: quick / standard / stealth / udp / vuln |
| **Web Recon** | Tech stack, security headers, WAF, SSL, email harvest, robots.txt |
| **IP Geolocation** | Country, city, ISP, ASN via ip-api.com |
| **Wayback URLs** | Historical URL harvest from Wayback Machine CDX API |
| **Reports** | Dark-green HTML, structured JSON, plain-text |

### Requirements,(installed by setup.sh)

**System tools**:
```
nmap  whois  dig  curl  git
```

**Python packages**:
```
rich>=13.7.0  requests>=2.31.0  urllib3>=2.2.0  dnspython>=2.4.0
```

**Optional Go tools** (improve results significantly):
```bash
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/tomnomnom/waybackurls@latest
go install github.com/ffuf/ffuf/v2@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```

### Installation

```bash
git clone https://github.com/mm1389m/NMrecon.git
cd NMrecon
chmod +x setup.sh
bash setup.sh
python3 NMrecon.py
```

### Usage

**Interactive menu** (recommended):
```bash
python3 NMrecon.py
```

**CLI flags**:
```bash
python3 NMrecon.py -d example.com
python3 NMrecon.py -d example.com --no-brute --no-wayback
python3 NMrecon.py -d example.com -m ports --port-profile stealth
python3 NMrecon.py -d example.com -m subdomain
python3 NMrecon.py -d example.com -m web
python3 NMrecon.py -d 1.2.3.4 -m geo
python3 NMrecon.py --check-tools
```

### Options

| Flag | Description |
|---|---|
| `-d`, `--domain` | Target domain or IP |
| `-m`, `--module` | `full` `subdomain` `dns` `whois` `ports` `web` `wayback` `geo` |
| `--port-profile` | `quick` `standard` `stealth` `udp` `vuln` |
| `--no-brute` | Skip DNS brute-force |
| `--no-wayback` | Skip Wayback URL fetch |
| `--no-ports` | Skip port scan |
| `--no-ssl` | Skip SSL check |
| `--no-report` | Do not save report files |
| `--output-dir` | Custom report directory (default: `./output/`) |
| `--report-fmt` | `html` `json` `text` `all` (default: `all`) |
| `--check-tools` | Show tool availability table |
| `--no-banner` | Skip ASCII banner |

### Port Scan Profiles

| Profile | Description |
|---|---|
| `quick` | Top 100 ports, fast (`-T4 -F`) |
| `standard` | All ports, version + scripts (`-T4 -p- -sV -sC`) |
| `stealth` | SYN scan, fragmented (`-T2 -sS -f`) — needs root |
| `udp` | Common UDP services (`-sU`) — needs root |
| `vuln` | Vulnerability NSE scripts (`--script=vuln`) |

### wordlists:

```
subdomains.txt  ← DNS brute-force wordlist
    (defult subdomains is subdomains-top1million-20000.txt)
```

### Report Output

Reports are saved to `./output/` with a timestamped filename:

```
output:
example_com_20241215_143022.html   ← HTML report
example_com_20241215_143022.json   ← Structured JSON
example_com_20241215_143022.txt    ← Plain text
```

---

## Legal Disclaimer

> **NightMare Recon is intended strictly for authorized security testing.**
> Only use this tool against systems you own or have explicit written permission to test.
> Unauthorized scanning may be illegal in your jurisdiction.
> The author accepts no liability for misuse.

---

<div align="center">

**NightMare Recon** &nbsp;|&nbsp; Developed by `mm1389m` &nbsp;|&nbsp; v1.0.0

*Stay sharp. Stay authorized.*

</div>

