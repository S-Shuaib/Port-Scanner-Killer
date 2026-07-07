// ── Data ──────────────────────────────────────────────────────────────────
  const KNOWN_PORTS = {
    20:"FTP Data",21:"FTP Control",22:"SSH",23:"Telnet",25:"SMTP",
    53:"DNS",80:"HTTP",110:"POP3",143:"IMAP",443:"HTTPS",
    465:"SMTPS",587:"SMTP TLS",993:"IMAPS",995:"POP3S",1433:"MSSQL",
    1521:"Oracle DB",2181:"Zookeeper",2375:"Docker",3000:"Dev Server",
    3001:"Dev Server Alt",3306:"MySQL",3389:"RDP",4200:"Angular Dev",
    4443:"HTTPS Alt",5000:"Flask/Dev",5173:"Vite Dev",5432:"PostgreSQL",
    5900:"VNC",6379:"Redis",6443:"Kubernetes",7474:"Neo4j",
    8000:"HTTP Alt",8080:"HTTP Proxy",8081:"HTTP Alt 2",8443:"HTTPS Alt",
    8888:"Jupyter",9000:"Portainer",9090:"Prometheus",9200:"Elasticsearch",
    9300:"ES Transport",27017:"MongoDB",27018:"MongoDB Alt"
  };

  // Simulated open ports for demo purposes
  const DEMO_OPEN = {
    3000: { pid: 48231, name: "node",          cmd: "node server.js" },
    5432: { pid: 1042,  name: "postgres",      cmd: "postgres -D /usr/local/var/postgres" },
    6379: { pid: 892,   name: "redis-server",  cmd: "redis-server 127.0.0.1:6379" },
    8080: { pid: 50341, name: "python",        cmd: "python -m http.server 8080" },
    27017:{ pid: 2203,  name: "mongod",        cmd: "mongod --config /etc/mongod.conf" },
    5173: { pid: 61022, name: "node (vite)",   cmd: "vite --port 5173" },
  };

  // Render the ports reference on the about page
  document.getElementById('tab-about').innerHTML = document.getElementById('tab-about').innerHTML.replace(
    '${Object.entries(KNOWN_PORTS_HTML).map(([p,s]) => `<div style="display:flex;gap:8px;align-items:center;padding:5px 8px;background:var(--card);border-radius:4px;border:1px solid var(--border)"><span style="color:var(--green);font-weight:700;min-width:40px">${p}</span><span style="color:var(--muted)">${s}</span></div>`).join(\'\')}',
    Object.entries(KNOWN_PORTS).map(([p,s]) =>
      `<div style="display:flex;gap:8px;align-items:center;padding:5px 8px;background:var(--card);border-radius:4px;border:1px solid var(--border)">
        <span style="color:var(--green);font-weight:700;min-width:40px">${p}</span>
        <span style="color:var(--muted)">${s}</span>
       </div>`
    ).join('')
  );

  // ── Tab switching ─────────────────────────────────────────────────────────
  function switchTab(name, btn) {
    document.querySelectorAll('.tab-pane').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    btn.classList.add('active');
    if (name !== 'watch') stopWatch();
  }

  // ── Terminal log ──────────────────────────────────────────────────────────
  function addLog(el, text, cls = '') {
    const line = document.createElement('div');
    line.className = 'log-line ' + cls;
    line.textContent = text;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
  }

  // ── SCAN ──────────────────────────────────────────────────────────────────
  let scanTimer = null;

  function setScanState(state, status, count = '') {
    const dot  = document.getElementById('scanDot');
    const txt  = document.getElementById('scanStatus');
    const cnt  = document.getElementById('scanCount');
    dot.className = 'status-dot ' + state;
    txt.textContent = status;
    cnt.textContent = count;
  }

  function clearResults() {
    document.getElementById('resultsBody').innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔌</div>
        <div class="empty-text">No scan results yet.<br>Run a scan to see open ports.</div>
      </div>`;
    setScanState('', 'Ready. Select a range and run scan.', '');
    const log = document.getElementById('termLog');
    log.innerHTML = '';
    addLog(log, '$ port_killer.py scan', 'log-cmd');
    addLog(log, 'Results cleared.', 'log-warn');
  }

  function quickScan() {
    document.getElementById('rangeStart').value = 1;
    document.getElementById('rangeEnd').value = 9999;
    runScan();
  }

  function runScan() {
    const start = parseInt(document.getElementById('rangeStart').value);
    const end   = parseInt(document.getElementById('rangeEnd').value);
    const host  = document.getElementById('hostInput').value || '127.0.0.1';
    const log   = document.getElementById('termLog');
    const body  = document.getElementById('resultsBody');

    if (start > end) { setScanState('error', 'Error: start must be ≤ end.'); return; }

    log.innerHTML = '';
    addLog(log, `$ port_killer.py scan --range ${start}-${end} --host ${host}`, 'log-cmd');
    addLog(log, `[INFO] Scanning ${end - start + 1} ports on ${host}...`, 'log-info');

    body.innerHTML = '';
    setScanState('scanning', `Scanning ports ${start}–${end} on ${host}…`);

    let found = 0;
    const openPorts = Object.keys(DEMO_OPEN)
      .map(Number)
      .filter(p => p >= start && p <= end);

    let i = 0;
    const total = openPorts.length;

    function step() {
      if (i >= total) {
        setScanState('done', `Scan complete.`, `${found} open`);
        addLog(log, `[OK] Scan finished. ${found} open port(s) found.`, 'log-ok');
        if (found === 0) {
          body.innerHTML = `<div class="empty-state"><div class="empty-icon">✅</div><div class="empty-text">No open ports found in range ${start}–${end}.</div></div>`;
        }
        return;
      }
      const port = openPorts[i++];
      const info = DEMO_OPEN[port];
      const service = KNOWN_PORTS[port] || 'Unknown';
      addLog(log, `[OPEN] Port ${port} → ${info.name} (PID ${info.pid})`, 'log-ok');
      found++;
      setScanState('scanning', `Scanning… found ${found} open port(s)`, `${found} open`);

      const row = document.createElement('div');
      row.className = 'result-row';
      row.style.animationDelay = (i * 60) + 'ms';
      row.innerHTML = `
        <div class="port-num">${port}</div>
        <div class="service-name">${service}</div>
        <div class="proc-name">${info.name}</div>
        <div class="pid-val">${info.pid}</div>
        <div><button class="kill-btn" onclick="quickKill(${port})" title="Kill port ${port}">✕</button></div>
      `;
      body.appendChild(row);
      body.scrollTop = body.scrollHeight;

      setTimeout(step, 180 + Math.random() * 120);
    }

    setTimeout(step, 300);
  }

  function quickKill(port) {
    if (!confirm(`Kill process on port ${port}?`)) return;
    delete DEMO_OPEN[port];
    document.querySelectorAll('.result-row').forEach(row => {
      if (row.querySelector('.port-num')?.textContent == port) {
        row.style.background = 'rgba(248,81,73,0.1)';
        row.style.opacity = '0.4';
        setTimeout(() => row.remove(), 600);
      }
    });
    const log = document.getElementById('termLog');
    addLog(log, `[OK] Process on port ${port} terminated.`, 'log-ok');
    const count = document.getElementById('scanCount');
    const n = parseInt(count.textContent) - 1;
    count.textContent = `${n} open`;
  }

  // ── FIND ──────────────────────────────────────────────────────────────────
  function runFind() {
    const port = parseInt(document.getElementById('findPort').value);
    const host = document.getElementById('hostInput').value || '127.0.0.1';
    const el   = document.getElementById('findResult');
    const info = DEMO_OPEN[port];

    if (!info) {
      el.innerHTML = `
        <div style="background:var(--panel);border:1px solid rgba(248,81,73,0.3);border-radius:8px;padding:24px 28px;color:var(--red);">
          <div style="font-size:13px;font-weight:700;margin-bottom:6px;">⚠ Port ${port} is not open</div>
          <div style="font-size:11px;color:var(--muted);">No process found listening on port ${port} at ${host}.</div>
        </div>`;
      return;
    }

    const service = KNOWN_PORTS[port] || 'Unknown';
    el.innerHTML = `
      <div class="find-result">
        <div class="find-field">
          <div class="find-label">Port</div>
          <div class="find-value" style="color:var(--green)">${port}</div>
        </div>
        <div class="find-field">
          <div class="find-label">Service</div>
          <div class="find-value" style="color:var(--cyan)">${service}</div>
        </div>
        <div class="find-field">
          <div class="find-label">PID</div>
          <div class="find-value" style="color:var(--yellow)">${info.pid}</div>
        </div>
        <div class="find-field">
          <div class="find-label">Process Name</div>
          <div class="find-value" style="color:var(--text)">${info.name}</div>
        </div>
        <div class="find-field" style="grid-column:1/-1">
          <div class="find-label">Command</div>
          <div class="find-value" style="font-size:11px;color:var(--muted);font-weight:400">${info.cmd}</div>
        </div>
        <div class="find-field" style="grid-column:1/-1">
          <div class="find-label">Kill Command</div>
          <div style="background:var(--bg);border:1px solid var(--border2);border-radius:5px;padding:8px 12px;font-size:11px;color:var(--blue)">python port_killer.py kill ${port}</div>
        </div>
      </div>`;
  }

  // ── KILLER ──────────────────────────────────────────────────────────────────
  function runKill() {
    const raw   = document.getElementById('killPorts').value;
    const ports = raw.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    const log   = document.getElementById('killLogBody');
    log.innerHTML = '';

    addLog(log, `$ port_killer.py kill ${ports.join(' ')}`, 'log-cmd');

    ports.forEach((port, idx) => {
      setTimeout(() => {
        const info = DEMO_OPEN[port];
        if (!info) {
          addLog(log, `[WARN] Port ${port}: not open or already free.`, 'log-warn');
          return;
        }
        addLog(log, `[INFO] Port ${port}: found ${info.name} (PID ${info.pid})`, 'log-info');
        setTimeout(() => {
          addLog(log, `[OK]   Port ${port}: process ${info.name} terminated. Port is now free.`, 'log-ok');
          delete DEMO_OPEN[port];
        }, 500);
      }, idx * 700);
    });
  }

  // ── WATCH ─────────────────────────────────────────────────────────────────
  let watchTimer = null;
  let isWatching = false;
  let lastWatchState = null;

  function toggleWatch() {
    if (isWatching) stopWatch();
    else startWatch();
  }

  function startWatch() {
    const port     = parseInt(document.getElementById('watchPort').value);
    const interval = parseFloat(document.getElementById('watchInterval').value) * 1000;
    const btn      = document.getElementById('watchStartBtn');
    const ring     = document.getElementById('watchRing');
    const portDisp = document.getElementById('watchPortDisplay');
    const badge    = document.getElementById('watchStatusBadge');
    const watchLog = document.getElementById('watchLog');

    isWatching = true;
    btn.textContent = '⏹ Stop Watch';
    btn.className = 'btn btn-danger';
    portDisp.textContent = port;
    portDisp.style.fontSize = '72px';
    watchLog.innerHTML = '';

    function check() {
      const isOpen = !!DEMO_OPEN[port];
      const ts = new Date().toLocaleTimeString();

      if (isOpen !== lastWatchState) {
        const line = document.createElement('div');
        line.style.cssText = `color:${isOpen ? 'var(--green)' : 'var(--red)'};`;
        line.textContent = `${ts}  ${isOpen ? '▲ OPEN' : '▼ CLOSED'}`;
        watchLog.appendChild(line);
        watchLog.scrollTop = watchLog.scrollHeight;
        lastWatchState = isOpen;
      }

      ring.className = 'watch-ring ' + (isOpen ? 'open' : 'closed');
      portDisp.style.color = isOpen ? 'var(--green)' : 'var(--red)';
      badge.style.background = isOpen ? 'rgba(61,214,140,0.1)' : 'rgba(248,81,73,0.1)';
      badge.style.color = isOpen ? 'var(--green)' : 'var(--red)';
      badge.style.border = `1px solid ${isOpen ? 'rgba(61,214,140,0.3)' : 'rgba(248,81,73,0.3)'}`;
      badge.textContent = isOpen ? 'OPEN' : 'CLOSED';
    }

    check();
    watchTimer = setInterval(check, interval);
  }

  function stopWatch() {
    clearInterval(watchTimer);
    isWatching = false;
    lastWatchState = null;
    const btn = document.getElementById('watchStartBtn');
    btn.textContent = '▶ Start Watch';
    btn.className = 'btn btn-primary';
    document.getElementById('watchRing').className = 'watch-ring';
    document.getElementById('watchPortDisplay').textContent = '—';
    document.getElementById('watchPortDisplay').style.color = 'var(--muted2)';
    document.getElementById('watchPortDisplay').style.fontSize = '36px';
    document.getElementById('watchStatusBadge').textContent = 'IDLE';
    document.getElementById('watchStatusBadge').style.cssText = 'background:var(--card);color:var(--muted);border:1px solid var(--border2)';
  }
