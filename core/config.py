"""
NightMare Recon — core/config.py
Global config, paths, nmap profiles, tech/WAF signatures.
Developed by mm1389m  |  v1.0.0
"""

import re
from pathlib import Path

_BASE_DIR    = Path(__file__).resolve().parent.parent
OUTPUT_DIR   = _BASE_DIR / "output"
WORDLIST_DIR = _BASE_DIR / "wordlists"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUBDOMAIN_WORDLIST = WORDLIST_DIR / "subdomains.txt"
DIRECTORY_WORDLIST = WORDLIST_DIR / "directories.txt"

VERSION = "1.0.0"
AUTHOR  = "mm1389m"

NMAP_PROFILES: dict[str, list[str]] = {
    "quick": ["-T4", "--open", "-F", "--min-rate=1000", "--max-retries=1"],
    "standard": ["-T4", "--open", "-sV", "-sC", "-p-", "--min-rate=500"],
    "stealth": [
        "-T2", "--open", "-sS",
        "-p", "21,22,23,25,53,80,110,143,443,445,3306,3389,8080,8443,8888",
        "-f", "--data-length", "15",
    ],
    "udp": ["-sU", "-T4", "--open", "-p", "53,67,68,69,111,123,137,138,161,162,500", "--max-retries=1"],
    "vuln": ["-T4", "--open", "-sV", "-sC", "--script=vuln,auth", "-p", "21,22,23,25,53,80,443,445,3306,3389,8080,8443"],
}

NMAP_TIMEOUT: dict[str, int] = {
    "quick": 90, "standard": 600, "stealth": 300, "udp": 240, "vuln": 420,
}

DEFAULT_TIMEOUT    = 10
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"

DNS_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "CAA"]

TECH_SIGNATURES: dict[str, list[str]] = {
    "WordPress":         ["wp-content", "wp-includes", "wp-json", "WordPress"],
    "Drupal":            ["Drupal", "X-Generator: Drupal", "/sites/default/"],
    "Joomla":            ["/components/com_", "Joomla!"],
    "Laravel":           ["laravel_session", "XSRF-TOKEN"],
    "Django":            ["csrfmiddlewaretoken", "django"],
    "React":             ["__REACT_DEVTOOLS", "_reactRootContainer", "__NEXT_DATA__"],
    "Vue.js":            ["__vue__", "vue.min.js", "__VUE__"],
    "Angular":           ["ng-version", "angular.min.js", "ng-app"],
    "jQuery":            ["jquery.min.js", "jquery-", "jQuery.fn"],
    "Bootstrap":         ["bootstrap.min.css", "bootstrap.min.js"],
    "Nginx":             ["nginx"],
    "Apache":            ["Apache", "Server: Apache"],
    "IIS":               ["Microsoft-IIS", "X-Powered-By: ASP.NET"],
    "PHP":               ["X-Powered-By: PHP", "PHPSESSID", ".php?"],
    "ASP.NET":           ["ASP.NET", "__VIEWSTATE"],
    "Node.js":           ["X-Powered-By: Express", "connect.sid"],
    "Ruby on Rails":     ["X-Powered-By: Phusion", "_rails_session"],
    "Magento":           ["Magento", "mage-", "MAGE_SESSID"],
    "Shopify":           ["Shopify", "myshopify.com"],
    "CloudFlare":        ["cf-ray", "__cf_bm", "cloudflare"],
    "AWS CloudFront":    ["X-Amz-Cf-Id", "CloudFront"],
    "Fastly":            ["X-Fastly-Request-ID"],
    "Varnish":           ["X-Varnish", "Via: varnish"],
    "Netlify":           ["x-nf-request-id"],
    "Vercel":            ["x-vercel-id", "x-vercel-cache"],
}

WAF_SIGNATURES: dict[str, list[str]] = {
    "Cloudflare":          ["cloudflare", "__cfduid", "cf-ray", "__cf_bm"],
    "AWS WAF":             ["x-amzn-requestid", "x-amz-cf-id"],
    "Akamai":              ["akamai", "ak-bmsc", "bm_sz"],
    "Imperva / Incapsula": ["incap_ses", "visid_incap", "X-Iinfo"],
    "F5 BIG-IP ASM":       ["BigIP", "X-Cnection", "TS01"],
    "ModSecurity":         ["ModSecurity", "Mod_Security"],
    "Sucuri":              ["sucuri-cache", "X-Sucuri-ID"],
    "Barracuda":           ["barra_counter_session", "BNI__BARRACUDA"],
    "Wordfence":           ["wordfence_logHuman", "wfvt_"],
    "DDoS-Guard":          ["__ddg1", "__ddg2", "ddos-guard"],
    "Wallarm":             ["wallarm-waf"],
}

SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy",
    "X-XSS-Protection",
    "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
    "Cross-Origin-Embedder-Policy",
    "Cache-Control",
]

SENSITIVE_PATHS = [
    "/.env", "/.git/config", "/.git/HEAD", "/wp-config.php",
    "/config.php", "/configuration.php", "/settings.php",
    "/phpinfo.php", "/info.php", "/.htaccess",
    "/server-status", "/server-info",
    "/api/swagger.json", "/swagger.json", "/swagger-ui.html",
    "/api-docs", "/openapi.json", "/graphql",
    "/backup.zip", "/db.sql", "/dump.sql", "/database.sql",
    "/robots.txt", "/sitemap.xml",
    "/web.config", "/.npmrc", "/.DS_Store",
]

_DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)
_IP_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)


def sanitize_domain(raw: str) -> str:
    """Strip protocol, path, port from raw input. Returns clean hostname/IP."""
    s = raw.strip().lower()
    s = re.sub(r"^https?://", "", s)
    s = s.split("/")[0]
    s = re.sub(r":\d+$", "", s)
    return s.strip(".")


def is_valid_target(target: str) -> bool:
    return bool(_DOMAIN_RE.match(target)) or bool(_IP_RE.match(target))
