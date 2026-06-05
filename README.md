# ⚡ Port Scanner & Killer

> **Day 06 / 30** — 30-Day GitHub Roadmap  
> Find which process is hogging a port and kill it in one command.

---

## Features

- 🔍 **Scan** — sweep common ports or a custom range simultaneously (multithreaded)
- 🎯 **Find** — identify the exact PID and process name on any port
- 💀 **Kill** — terminate one or multiple port-hogging processes interactively
- 👁️ **Watch** — live-monitor a port and get notified when it opens or closes
- 🖥️ Cross-platform — works on macOS, Linux, and Windows

---

## Installation

```bash
# Clone or download port_killer.py, then:

# Optional but recommended — enables richer process info
pip install psutil

# Without psutil, the tool falls back to lsof (macOS/Linux) or netstat (Windows)
```

No other dependencies needed.

---

## Usage

```bash
# Scan all common ports (Redis, Postgres, MySQL, HTTP, etc.)
python port_killer.py scan

# Scan a custom port range
python port_killer.py scan --range 3000-9000

# Scan a remote host
python port_killer.py scan --host 192.168.1.100

# Find what's on port 8080
python port_killer.py find 8080

# Kill the process on port 3000 (asks for confirmation)
python port_killer.py kill 3000

# Kill multiple ports at once
python port_killer.py kill 3000 8080 5432

# Force kill (SIGKILL — no mercy)
python port_killer.py kill 3000 --force

# Live-watch port 5000 every 2 seconds
python port_killer.py watch 5000

# Watch with custom interval
python port_killer.py watch 5000 --interval 0.5
```

---

## Example Output

```
  PORT     SERVICE                PID      PROCESS
  ──────── ────────────────────── ──────── ────────────────────────────
  3000     Dev Server             48231    node
  5432     PostgreSQL             1042     postgres
  6379     Redis                  892      redis-server
  8080     HTTP Proxy             50341    python

  3 open port(s) found.
```

---

## Common Ports Covered

| Port  | Service        | Port  | Service       |
|-------|----------------|-------|---------------|
| 22    | SSH            | 3306  | MySQL         |
| 80    | HTTP           | 5432  | PostgreSQL    |
| 443   | HTTPS          | 6379  | Redis         |
| 3000  | Dev Server     | 8080  | HTTP Proxy    |
| 5000  | Flask/Dev      | 27017 | MongoDB       |
| 5173  | Vite Dev       | 9200  | Elasticsearch |

And 30+ more.

---

## Notes

- On macOS/Linux you may need `sudo` to see process names for system ports
- `--force` sends `SIGKILL` (Linux/Mac) or `/F` flag (Windows)
- The `watch` command polls every N seconds and prints on state change

---

## License

MIT — free to use, modify, and share.
