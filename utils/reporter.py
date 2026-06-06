"""
NightMare Recon — utils/reporter.py
HTML, JSON, and plain-text report generation (green matrix theme).
Developed by mm1389m  |  v1.0.0
"""

import json
import html as _html
from datetime import datetime
from pathlib import Path
from core.banner import VERSION, AUTHOR


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_path(domain: str, ext: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in domain)
    return out_dir / f"{safe}_{_ts()}.{ext}"


def _esc(s: str) -> str:
    return _html.escape(str(s))


def save_text_report(domain: str, results: dict, out_dir: Path) -> Path:
    path = _safe_path(domain, "txt", out_dir)
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = [
        "=" * 72,
        "  NightMare Recon — Scan Report",
        f"  Developed by {AUTHOR}  |  v{VERSION}",
        f"  Target  : {domain}",
        f"  Created : {now}",
        "=" * 72, "",
    ]
    for section, data in results.items():
        lines += [f"{'─' * 72}", f"  {section.upper()}", f"{'─' * 72}"]
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    lines.append(f"  {k}:")
                    for item in v:
                        lines.append(f"      • {item}")
                elif v not in (None, ""):
                    lines.append(f"  {str(k):<30} {v}")
        elif isinstance(data, list):
            for item in data:
                lines.append(f"  • {item}")
        elif data:
            lines.append(f"  {data}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def save_json_report(domain: str, results: dict, out_dir: Path) -> Path:
    path = _safe_path(domain, "json", out_dir)
    payload = {
        "meta": {
            "tool": "NightMare Recon", "author": AUTHOR,
            "version": VERSION, "target": domain,
            "created": datetime.now().isoformat(),
        },
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    return path


_CSS = """
:root{--bg:#030a05;--surf:#071009;--bord:#0d2010;
  --g:#00ff41;--g2:#00cc33;--g3:#008822;--cyan:#00e5ff;
  --txt:#c8ffd4;--muted:#3d7a4a;--red:#ff3333;--yel:#ffcc00;
  --rad:6px;--font:'Cascadia Code','Fira Code','Source Code Pro',monospace}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:var(--font);font-size:13px;line-height:1.6;padding:20px}
header{border:1px solid var(--bord);border-radius:var(--rad);background:var(--surf);padding:20px 28px;
  margin-bottom:24px;display:flex;justify-content:space-between;align-items:center}
header pre.logo{color:var(--g);font-size:9.5px;line-height:1.2;letter-spacing:.02em}
.meta-box{text-align:right}.meta-box .target{font-size:20px;font-weight:700;color:var(--g)}
.meta-box .info{color:var(--muted);font-size:11px;margin-top:5px}
.sections{display:flex;flex-direction:column;gap:14px}
.section{background:var(--surf);border:1px solid var(--bord);border-radius:var(--rad);overflow:hidden}
.sh{background:linear-gradient(90deg,#020d04,var(--surf));border-bottom:1px solid var(--bord);
  padding:9px 18px;display:flex;align-items:center;gap:8px}
.sh .ico{color:var(--g);font-size:12px}
.sh h2{color:var(--g);font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.08em}
.sb{padding:14px 18px}
table.data{width:100%;border-collapse:collapse;font-size:12.5px}
table.data th{color:var(--g);font-weight:600;text-align:left;padding:6px 9px;
  border-bottom:1px solid var(--bord);background:rgba(0,255,65,.04);
  text-transform:uppercase;font-size:11px;letter-spacing:.05em}
table.data td{padding:5px 9px;border-bottom:1px solid rgba(13,32,16,.6);
  color:var(--txt);vertical-align:top;word-break:break-all}
table.data tr:last-child td{border-bottom:none}
table.data tr:nth-child(even) td{background:rgba(255,255,255,.015)}
.ok{color:var(--g);font-weight:600}.bad{color:var(--red);font-weight:600}.warn{color:var(--yel)}
ul.lst{list-style:none;padding:0}
ul.lst li{padding:3px 0;border-bottom:1px solid rgba(13,32,16,.5);word-break:break-all}
ul.lst li::before{content:"▶ ";color:var(--g3);font-size:9px}ul.lst li:last-child{border-bottom:none}
.empty{color:var(--muted);font-style:italic}
footer{margin-top:28px;text-align:center;color:var(--muted);font-size:11px;
  border-top:1px solid var(--bord);padding-top:14px}
footer .brand{color:var(--g);font-weight:700}
"""

_LOGO = r"""
 ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗███╗   ███╗ █████╗ ██████╗ ███████╗
 ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝████╗ ████║██╔══██╗██╔══██╗██╔════╝
 ██╔██╗ ██║██║██║  ███╗███████║   ██║   ██╔████╔██║███████║██████╔╝█████╗
 ██║╚██╗██║██║██║   ██║██╔══██║   ██║   ██║╚██╔╝██║██╔══██║██╔══██╗██╔══╝
 ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██║ ╚═╝ ██║██║  ██║██║  ██║███████╗
 ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝"""


def _section_html(name: str, data) -> str:
    out = [
        '<div class="section"><div class="sh">',
        '<span class="ico">▶</span>',
        f'<h2>{_esc(name)}</h2></div><div class="sb">',
    ]
    if isinstance(data, dict) and data:
        out.append('<table class="data"><thead><tr><th>Field</th><th>Value</th></tr></thead><tbody>')
        for k, v in data.items():
            if isinstance(v, list):
                inner = ("<ul class='lst'>" + "".join(f"<li>{_esc(str(i))}</li>" for i in v) + "</ul>"
                         if v else '<span class="empty">—</span>')
            elif v in (None, ""):
                inner = '<span class="empty">—</span>'
            elif "MISSING" in str(v):
                inner = f'<span class="bad">{_esc(str(v))}</span>'
            elif str(v).startswith("✔"):
                inner = f'<span class="ok">{_esc(str(v))}</span>'
            else:
                inner = _esc(str(v))
            out.append(f"<tr><td>{_esc(str(k))}</td><td>{inner}</td></tr>")
        out.append("</tbody></table>")
    elif isinstance(data, list) and data:
        out.append("<ul class='lst'>" + "".join(f"<li>{_esc(str(i))}</li>" for i in data) + "</ul>")
    elif data:
        out.append(f"<p>{_esc(str(data))}</p>")
    else:
        out.append('<p class="empty">No data collected.</p>')
    out.append("</div></div>")
    return "\n".join(out)


def save_html_report(domain: str, results: dict, out_dir: Path) -> Path:
    path = _safe_path(domain, "html", out_dir)
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = "\n".join(_section_html(k, v) for k, v in results.items())
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>NMrecon — {_esc(domain)}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <pre class="logo">{_esc(_LOGO)}</pre>
  <div class="meta-box">
    <div class="target">▶ {_esc(domain)}</div>
    <div class="info">Generated: {now}<br>NightMare Recon v{VERSION}<br>Developed by {AUTHOR}</div>
  </div>
</header>
<div class="sections">{sections}</div>
<footer>
  <span class="brand">NightMare Recon</span>
  &nbsp;|&nbsp; Developed by {AUTHOR}
  &nbsp;|&nbsp; v{VERSION}
  &nbsp;|&nbsp; {now}
</footer>
</body>
</html>"""
    path.write_text(page, encoding="utf-8")
    return path
