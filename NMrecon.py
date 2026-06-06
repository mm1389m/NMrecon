#!/usr/bin/env python3
"""
NightMare Recon — NMrecon.py
Professional Recon & Bug Bounty Toolkit
Developed by mm1389m  |  v1.0.0

Usage:
    python3 NMrecon.py                          interactive menu
    python3 NMrecon.py -d example.com           full recon (all modules)
    python3 NMrecon.py -d example.com -m ports  port scan only
    python3 NMrecon.py --check-tools
    python3 NMrecon.py --help
"""

import sys
import argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from core.banner  import print_banner, print_section, print_success
from core.banner  import print_error, print_info, print_warning, console
from core.config  import sanitize_domain, OUTPUT_DIR, VERSION

from utils.menu       import (
    show_main_menu, ask_target, ask_port_profile,
    ask_full_recon_options, confirm_exit, ask_report_format,
)
from utils.reporter   import save_text_report, save_html_report, save_json_report
from utils.tool_check import run_tool_check
from utils.ui         import divider, print_results_table

from modules.dns_whois  import run_whois, run_dns_enum
from modules.subdomain  import run_subdomain_enum, check_live
from modules.portscan   import run_port_scan
from modules.web_recon  import run_web_recon, get_wayback_urls
from modules.geo_ip     import run_geo_ip


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="NMrecon",
        description=f"NightMare Recon v{VERSION}  |  Developed by mm1389m",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 NMrecon.py                                    interactive menu
  python3 NMrecon.py -d example.com                     full recon
  python3 NMrecon.py -d example.com --no-brute          skip DNS brute-force
  python3 NMrecon.py -d example.com -m ports --port-profile stealth
  python3 NMrecon.py -d 1.2.3.4 -m geo                 geolocate IP
  python3 NMrecon.py --check-tools
        """,
    )
    p.add_argument("-d", "--domain",  help="Target domain or IP address")
    p.add_argument(
        "-m", "--module",
        choices=["full", "subdomain", "dns", "whois", "ports", "web", "wayback", "geo"],
        default="full",
        help="Module to run  (default: full)",
    )
    p.add_argument(
        "--port-profile",
        choices=["quick", "standard", "stealth", "udp", "vuln"],
        default="quick",
    )
    p.add_argument("--no-brute",    action="store_true", help="Skip DNS brute-force")
    p.add_argument("--no-wayback",  action="store_true", help="Skip Wayback URL fetch")
    p.add_argument("--no-ports",    action="store_true", help="Skip port scan")
    p.add_argument("--no-ssl",      action="store_true", help="Skip SSL check")
    p.add_argument("--no-report",   action="store_true", help="Do not save report files")
    p.add_argument("--output-dir",  default=str(OUTPUT_DIR), help="Output directory")
    p.add_argument("--report-fmt",  default="all",
                   choices=["html", "json", "text", "all"],
                   help="Report format  (default: all)")
    p.add_argument("--check-tools", action="store_true", help="Show tool availability")
    p.add_argument("--no-banner",   action="store_true", help="Skip ASCII banner")
    return p


def _save_reports(domain: str, results: dict, out_dir: Path, fmt: str) -> None:
    f = fmt.lower().strip()
    saved = []
    if "html" in f or "all" in f:
        p = save_html_report(domain, results, out_dir)
        saved.append(("HTML", p))
    if "json" in f or "all" in f:
        p = save_json_report(domain, results, out_dir)
        saved.append(("JSON", p))
    if "text" in f or "txt" in f or "all" in f:
        p = save_text_report(domain, results, out_dir)
        saved.append(("Text", p))
    for fmt_name, path in saved:
        print_success(f"{fmt_name:<6}  →  {path}")


def run_full_recon(
    domain:       str,
    brute:        bool  = True,
    wayback:      bool  = True,
    ssl_check:    bool  = True,
    port_profile: str   = "quick",
    run_ports:    bool  = True,
    out_dir:      Path  = OUTPUT_DIR,
    save_report:  bool  = True,
    report_fmt:   str   = "all",
) -> None:
    results: dict = {}
    total  = 5 + int(run_ports)

    divider()
    console.print(
        f"\n  [bold bright_green]TARGET[/bold bright_green]  "
        f"[bold white]{domain}[/bold white]  "
        f"[dim green]({total} modules)[/dim green]\n"
    )
    divider()

    step = 1
    print_section(f"{step}/{total}  —  WHOIS")
    results["WHOIS"] = run_whois(domain)
    step += 1

    print_section(f"{step}/{total}  —  DNS Enumeration")
    results["DNS Records"] = run_dns_enum(domain)
    step += 1

    print_section(f"{step}/{total}  —  Subdomain Enumeration")
    subs = run_subdomain_enum(domain, brute=brute, live_check=True)
    results["Subdomains"] = subs
    step += 1

    if run_ports:
        print_section(f"{step}/{total}  —  Port Scanner")
        scan = run_port_scan(domain, profile=port_profile)
        results["Port Scan"] = {
            f"{p['port']}/{p['proto']}": (p["service"] + " " + p["version"]).strip()
            for p in scan.get("ports", [])
        }
        if scan.get("os_guess"):
            results["Port Scan"]["OS Guess"] = scan["os_guess"]
        step += 1
    else:
        print_warning("Port scan skipped  (--no-ports)")

    print_section(f"{step}/{total}  —  Web Reconnaissance")
    web = run_web_recon(domain, wayback=wayback, ssl_check=ssl_check)
    results["Web Info"] = {
        k: v for k, v in web.items()
        if k in ("url", "status_code", "server", "page_title",
                 "waf", "x_powered_by", "content_type")
    }
    results["Technologies"]     = web.get("technologies", [])
    results["Security Headers"] = web.get("security_headers", {})
    results["Crawl Files"]      = web.get("crawl_files", {})
    if web.get("emails"):
        results["Emails Found"] = web["emails"]
    if ssl_check and web.get("ssl"):
        results["SSL Certificate"] = web["ssl"]
    if wayback and web.get("wayback_urls"):
        results["Wayback URLs"] = web["wayback_urls"]
    step += 1

    if save_report:
        print_section(f"{step}/{total}  —  Saving Reports")
        _save_reports(domain, results, out_dir, report_fmt)
    else:
        print_warning("Report saving skipped  (--no-report)")

    divider()
    print_success(
        f"Full recon on [bold white]{domain}[/bold white] complete!"
    )
    console.print()


def interactive_loop() -> None:
    while True:
        choice = show_main_menu()

        if choice == "00":
            if confirm_exit():
                console.print(
                    "\n  [bold bright_green]"
                    "NightMare Recon — Session closed. Stay dark."
                    "[/bold bright_green]\n"
                )
                sys.exit(0)

        elif choice == "01":
            domain  = sanitize_domain(ask_target())
            opts    = ask_full_recon_options()
            from rich.prompt import Prompt
            out_raw = Prompt.ask(
                "  [dim]Output directory[/dim]",
                default=str(OUTPUT_DIR),
            )
            out_dir = Path(out_raw)
            fmt     = ask_report_format() if opts.get("report") else "none"
            run_full_recon(
                domain,
                brute=opts.get("brute", True),
                wayback=opts.get("wayback", True),
                ssl_check=opts.get("ssl", True),
                port_profile=opts.get("port_profile", "quick"),
                run_ports=opts.get("portscan", True),
                out_dir=out_dir,
                save_report=opts.get("report", True),
                report_fmt=fmt,
            )

        elif choice == "02":
            domain = sanitize_domain(ask_target("Enter domain for subdomain enum"))
            run_subdomain_enum(domain, brute=True, live_check=True)

        elif choice == "03":
            domain = sanitize_domain(ask_target("Enter domain for DNS lookup"))
            run_dns_enum(domain)

        elif choice == "04":
            domain = sanitize_domain(ask_target("Enter domain for WHOIS"))
            run_whois(domain)

        elif choice == "05":
            target  = sanitize_domain(ask_target("Enter target for port scan"))
            profile = ask_port_profile()
            run_port_scan(target, profile=profile)

        elif choice == "06":
            domain = sanitize_domain(ask_target("Enter domain for web recon"))
            run_web_recon(domain, wayback=True, ssl_check=True)

        elif choice == "07":
            raw = ask_target("Comma-separated hosts or path to a file")
            if Path(raw).is_file():
                hosts = [
                    h.strip()
                    for h in Path(raw).read_text(errors="replace").splitlines()
                    if h.strip()
                ]
            else:
                hosts = [h.strip() for h in raw.split(",") if h.strip()]

            if not hosts:
                print_error("No valid hosts provided.")
                continue

            alive = check_live(hosts)
            if alive:
                rows = [
                    [h["host"], h["url"], str(h["status"]),
                     str(h.get("title", ""))[:55]]
                    for h in alive
                ]
                print_results_table(
                    f"Live Hosts ({len(alive)})",
                    ["Host", "URL", "Status", "Title"],
                    rows,
                )
            else:
                print_warning("No live hosts found.")

        elif choice == "08":
            domain = sanitize_domain(ask_target("Enter domain for Wayback URLs"))
            urls   = get_wayback_urls(domain, limit=500)
            if urls:
                print_results_table(
                    f"Wayback URLs ({len(urls)})",
                    ["URL"],
                    [[u] for u in urls],
                )
                from rich.prompt import Confirm
                if Confirm.ask("  Save to file?", default=True):
                    out = OUTPUT_DIR / f"{domain.replace('.', '_')}_wayback.txt"
                    out.write_text("\n".join(urls), encoding="utf-8")
                    print_success(f"Saved  →  {out}")
            else:
                print_warning("No Wayback URLs found.")

        elif choice == "09":
            target = ask_target("Enter domain or IP to geolocate")
            run_geo_ip(target)

        elif choice == "10":
            run_tool_check()

        else:
            print_error(f"Unknown option: {choice}")


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    if not args.no_banner:
        print_banner(skip_animation=bool(args.domain or args.check_tools))

    if args.check_tools:
        run_tool_check()
        sys.exit(0)

    if args.domain:
        domain  = sanitize_domain(args.domain)
        out_dir = Path(args.output_dir)
        mod     = args.module

        if mod == "full":
            run_full_recon(
                domain,
                brute=not args.no_brute,
                wayback=not args.no_wayback,
                ssl_check=not args.no_ssl,
                port_profile=args.port_profile,
                run_ports=not args.no_ports,
                out_dir=out_dir,
                save_report=not args.no_report,
                report_fmt=args.report_fmt,
            )
        elif mod == "subdomain":
            run_subdomain_enum(domain, brute=not args.no_brute, live_check=True)
        elif mod == "dns":
            run_dns_enum(domain)
        elif mod == "whois":
            run_whois(domain)
        elif mod == "ports":
            run_port_scan(domain, profile=args.port_profile)
        elif mod == "web":
            run_web_recon(domain, wayback=not args.no_wayback, ssl_check=not args.no_ssl)
        elif mod == "wayback":
            urls = get_wayback_urls(domain, limit=500)
            for u in urls:
                console.print(f"  [bright_green]{u}[/bright_green]")
        elif mod == "geo":
            run_geo_ip(domain)
    else:
        interactive_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n  [bold red]Interrupted — exiting.[/bold red]\n")
        sys.exit(0)
