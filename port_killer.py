#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════╗
║         PORT SCANNER & KILLER  —  Day 6/30            ║
║         30-Day GitHub Roadmap                         ║
╚═══════════════════════════════════════════════════════╝

Find which process is hogging a port and kill it in one command.

Usage:
  python port_killer.py scan                  # Scan common ports
  python port_killer.py scan --range 1-1024   # Scan port range
  python port_killer.py find 3000             # Find process on port 3000
  python port_killer.py kill 3000             # Kill process on port 3000
  python port_killer.py kill 3000 8080 5432   # Kill multiple ports
  python port_killer.py watch 3000            # Watch a port (live)
"""

import socket
import sys
import os
import argparse
import time
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Colour helpers (no deps) ──────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
GRAY   = "\033[90m"

IS_WINDOWS = platform.system() == "Windows"

def c(text, *codes): return "".join(codes) + str(text) + RESET
def ok(msg):   print(c("  ✔ ", GREEN, BOLD) + msg)
def err(msg):  print(c("  ✘ ", RED,   BOLD) + msg)
def info(msg): print(c("  ℹ ", CYAN,  BOLD) + msg)
def warn(msg): print(c("  ⚠ ", YELLOW,BOLD) + msg)

# ── Common ports dictionary ───────────────────────────────────────────────────
KNOWN_PORTS = {
    20: "FTP Data",       21: "FTP Control",    22: "SSH",
    23: "Telnet",         25: "SMTP",            53: "DNS",
    80: "HTTP",           110: "POP3",           143: "IMAP",
    443: "HTTPS",         465: "SMTPS",          587: "SMTP TLS",
    993: "IMAPS",         995: "POP3S",          1433: "MSSQL",
    1521: "Oracle DB",    2181: "Zookeeper",     2375: "Docker",
    3000: "Dev Server",   3001: "Dev Server Alt",3306: "MySQL",
    3389: "RDP",          4200: "Angular Dev",   4443: "HTTPS Alt",
    5000: "Flask/Dev",    5173: "Vite Dev",      5432: "PostgreSQL",
    5900: "VNC",          6379: "Redis",         6443: "Kubernetes",
    7474: "Neo4j",        8000: "HTTP Alt",      8080: "HTTP Proxy",
    8081: "HTTP Alt 2",   8443: "HTTPS Alt",     8888: "Jupyter",
    9000: "Portainer",    9090: "Prometheus",    9200: "Elasticsearch",
    9300: "ES Transport", 27017: "MongoDB",      27018: "MongoDB Alt",
}

# ── Port probing ──────────────────────────────────────────────────────────────
def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False

def get_process_on_port(port: int):
    """Returns (pid, name, command) or None. Uses psutil if available, else falls back to OS commands."""
    try:
        import psutil
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port and conn.status in ("LISTEN", "ESTABLISHED"):
                try:
                    proc = psutil.Process(conn.pid)
                    return conn.pid, proc.name(), " ".join(proc.cmdline())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return conn.pid, "unknown", ""
        return None
    except ImportError:
        return _get_process_fallback(port)

def _get_process_fallback(port: int):
    """Fallback using system commands when psutil is not installed."""
    import subprocess
    try:
        if IS_WINDOWS:
            cmd = f'netstat -ano | findstr ":{port} "'
            result = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in result.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5:
                    pid = int(parts[-1])
                    name_cmd = f'tasklist /FI "PID eq {pid}" /FO CSV /NH'
                    name_res = subprocess.check_output(name_cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                    name = name_res.strip().split(",")[0].strip('"') if name_res.strip() else "unknown"
                    return pid, name, ""
        else:
            # lsof approach
            result = subprocess.check_output(
                ["lsof", "-i", f":{port}", "-sTCP:LISTEN", "-n", "-P"],
                text=True, stderr=subprocess.DEVNULL
            )
            lines = result.strip().splitlines()
            if len(lines) > 1:
                parts = lines[1].split()
                name = parts[0]
                pid  = int(parts[1])
                return pid, name, " ".join(parts[8:]) if len(parts) > 8 else ""
    except Exception:
        pass
    return None

def kill_process(pid: int, force: bool = False) -> bool:
    try:
        import psutil
        proc = psutil.Process(pid)
        if force:
            proc.kill()
        else:
            proc.terminate()
            proc.wait(timeout=3)
        return True
    except ImportError:
        return _kill_fallback(pid, force)
    except Exception as e:
        err(f"Failed to kill PID {pid}: {e}")
        return False

def _kill_fallback(pid: int, force: bool = False) -> bool:
    import subprocess
    try:
        if IS_WINDOWS:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True, capture_output=True)
        else:
            sig = "-9" if force else "-15"
            subprocess.run(["kill", sig, str(pid)], check=True, capture_output=True)
        return True
    except Exception as e:
        err(f"Failed to kill PID {pid}: {e}")
        return False

# ── Banner ────────────────────────────────────────────────────────────────────
def banner():
    print(c("""
 ██████╗  ██████╗ ██████╗ ████████╗    ██╗  ██╗██╗██╗     ██╗     ███████╗██████╗
 ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝    ██║ ██╔╝██║██║     ██║     ██╔════╝██╔══██╗
 ██████╔╝██║   ██║██████╔╝   ██║       █████╔╝ ██║██║     ██║     █████╗  ██████╔╝
 ██╔═══╝ ██║   ██║██╔══██╗   ██║       ██╔═██╗ ██║██║     ██║     ██╔══╝  ██╔══██╗
 ██║     ╚██████╔╝██║  ██║   ██║       ██║  ██╗██║███████╗███████╗███████╗██║  ██║
 ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝       ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝
""", CYAN, BOLD))
    print(c("  Day 06/30 · 30-Day GitHub Roadmap", GRAY))
    print(c("  Find & kill processes hogging your ports.\n", GRAY))

# ── Commands ──────────────────────────────────────────────────────────────────
def cmd_scan(port_range: str = None, host: str = "127.0.0.1"):
    """Scan ports for open connections."""
    if port_range:
        try:
            start, end = map(int, port_range.split("-"))
            ports = list(range(start, end + 1))
            info(f"Scanning ports {start}–{end} on {host} ...")
        except ValueError:
            err("Invalid range format. Use: --range 1-1024")
            sys.exit(1)
    else:
        ports = list(KNOWN_PORTS.keys())
        info(f"Scanning {len(ports)} common ports on {host} ...")

    print()
    open_ports = []

    with ThreadPoolExecutor(max_workers=100) as ex:
        futures = {ex.submit(is_port_open, p, host): p for p in ports}
        for future in as_completed(futures):
            port = futures[future]
            if future.result():
                open_ports.append(port)

    if not open_ports:
        warn("No open ports found.")
        return

    open_ports.sort()
    print(f"  {'PORT':<8} {'SERVICE':<22} {'PID':<8} {'PROCESS'}")
    print(f"  {'─'*8} {'─'*22} {'─'*8} {'─'*28}")

    for port in open_ports:
        service = KNOWN_PORTS.get(port, "Unknown")
        proc    = get_process_on_port(port)
        if proc:
            pid, name, _ = proc
            print(f"  {c(port, GREEN, BOLD):<17} {c(service, CYAN):<31} {c(pid, YELLOW):<17} {name}")
        else:
            print(f"  {c(port, GREEN, BOLD):<17} {c(service, CYAN):<31} {'—':<8} {'—'}")

    print(f"\n  {c(len(open_ports), GREEN, BOLD)} open port(s) found.\n")


def cmd_find(port: int, host: str = "127.0.0.1"):
    """Find the process using a specific port."""
    info(f"Looking up port {c(port, CYAN, BOLD)} on {host} ...\n")

    if not is_port_open(port, host):
        warn(f"Port {port} appears to be closed or not listening.")
        return

    proc = get_process_on_port(port)
    if not proc:
        warn(f"Port {port} is open but couldn't identify the process.")
        warn("Try running with sudo/administrator privileges.")
        return

    pid, name, cmd = proc
    print(f"  {c('PORT', BOLD)}     {c(port, GREEN, BOLD)}")
    print(f"  {c('PID', BOLD)}      {c(pid, YELLOW, BOLD)}")
    print(f"  {c('PROCESS', BOLD)}  {c(name, CYAN)}")
    if cmd:
        print(f"  {c('COMMAND', BOLD)}  {c(cmd[:80] + ('...' if len(cmd) > 80 else ''), GRAY)}")
    print()
    info(f"To kill it: {c(f'python port_killer.py kill {port}', WHITE)}\n")


def cmd_kill(ports: list, host: str = "127.0.0.1", force: bool = False):
    """Kill processes on given ports."""
    for port in ports:
        print()
        info(f"Targeting port {c(port, CYAN, BOLD)} ...")

        if not is_port_open(port, host):
            warn(f"Port {port} is not open. Nothing to kill.")
            continue

        proc = get_process_on_port(port)
        if not proc:
            warn(f"Couldn't identify process on port {port}. Try with sudo.")
            continue

        pid, name, cmd = proc
        print(f"  {c('Found:', BOLD)} {c(name, CYAN)} (PID {c(pid, YELLOW)})")

        confirm = input(f"  {c('Kill this process?', WHITE)} {c('[y/N]', GRAY)} ").strip().lower()
        if confirm not in ("y", "yes"):
            warn("Skipped.")
            continue

        if kill_process(pid, force=force):
            ok(f"Process {c(name, CYAN)} (PID {c(pid, YELLOW)}) terminated.")
            # verify
            time.sleep(0.5)
            if not is_port_open(port, host):
                ok(f"Port {c(port, GREEN)} is now free! 🎉")
            else:
                warn(f"Port {port} still appears open. Try with --force.")
        else:
            err(f"Failed to kill PID {pid}.")

    print()


def cmd_watch(port: int, host: str = "127.0.0.1", interval: float = 2.0):
    """Live-watch a port and show status changes."""
    info(f"Watching port {c(port, CYAN, BOLD)} every {interval}s. Press Ctrl+C to stop.\n")
    last_state = None

    try:
        while True:
            open_now = is_port_open(port, host)
            ts = time.strftime("%H:%M:%S")

            if open_now != last_state:
                if open_now:
                    proc = get_process_on_port(port)
                    detail = f"(PID {proc[1]})" if proc else ""
                    print(f"  {c(ts, GRAY)}  {c('OPEN  ▲', GREEN, BOLD)}  {detail}")
                else:
                    print(f"  {c(ts, GRAY)}  {c('CLOSED ▼', RED, BOLD)}")
                last_state = open_now
            else:
                state_str = c("OPEN  ●", GREEN) if open_now else c("CLOSED ●", RED)
                print(f"  {c(ts, GRAY)}  {state_str}", end="\r")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n  {c('Watch stopped.', GRAY)}\n")


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    banner()

    parser = argparse.ArgumentParser(
        description="Port Scanner & Killer — find and kill processes hogging ports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python port_killer.py scan
  python port_killer.py scan --range 3000-9000
  python port_killer.py find 8080
  python port_killer.py kill 3000
  python port_killer.py kill 3000 8080 5432
  python port_killer.py watch 5000
        """
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = sub.add_parser("scan", help="Scan common (or ranged) ports")
    p_scan.add_argument("--range", dest="range", help="Port range e.g. 1-1024")
    p_scan.add_argument("--host", default="127.0.0.1", help="Host to scan (default: 127.0.0.1)")

    # find
    p_find = sub.add_parser("find", help="Find process on a specific port")
    p_find.add_argument("port", type=int, help="Port number")
    p_find.add_argument("--host", default="127.0.0.1")

    # kill
    p_kill = sub.add_parser("kill", help="Kill process(es) on port(s)")
    p_kill.add_argument("ports", type=int, nargs="+", help="One or more port numbers")
    p_kill.add_argument("--host", default="127.0.0.1")
    p_kill.add_argument("--force", action="store_true", help="Force kill (SIGKILL)")

    # watch
    p_watch = sub.add_parser("watch", help="Live-watch a port for state changes")
    p_watch.add_argument("port", type=int, help="Port number")
    p_watch.add_argument("--host", default="127.0.0.1")
    p_watch.add_argument("--interval", type=float, default=2.0, help="Poll interval seconds (default: 2)")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(port_range=args.range, host=args.host)
    elif args.command == "find":
        cmd_find(port=args.port, host=args.host)
    elif args.command == "kill":
        cmd_kill(ports=args.ports, host=args.host, force=args.force)
    elif args.command == "watch":
        cmd_watch(port=args.port, host=args.host, interval=args.interval)


if __name__ == "__main__":
    main()
