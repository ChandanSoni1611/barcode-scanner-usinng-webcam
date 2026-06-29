const socket = io();

let rowCount = 0;
let dupCount = 0;
let sessionSecs = 0;

let sessionTimer = null;
let ackTimer = null;

let camRunning = false;

/* ADD THIS */
let scanningLocked = false;

const seenCodes = new Set();

// ── SocketIO listeners ───────────────────────────────────────────────────────
socket.on("connect", () => setStatus(true));
socket.on("disconnect", () => setStatus(false));

socket.on("scanner_status", ({ status }) => {
  if (status === "started") setCamState(true);
  if (status === "stopped") setCamState(false);
});

socket.on("scan_result", (data) => addRow(data));

socket.on("duplicate_scan", ({ barcode }) => {
  dupCount++;
  el("footerDups").textContent = dupCount;
  showAck(`⚠️ Already scanned: ${barcode}`, false);
});

socket.on("scanner_error", ({ message }) => showAck("❌ " + message, false));

// ── QuaggaJS (browser-side decode → POST to Flask) ───────────────────────────
function startCamera() {
  el("scanner").innerHTML = "";
  Quagga.init(
    {
      inputStream: {
        name: "Live",
        type: "LiveStream",
        target: el("scanner"),
        constraints: {
          width: 1280,
          height: 720,
          facingMode: "environment",
        },
      },

      locator: {
        patchSize: "medium",
        halfSample: false,
      },

      numOfWorkers: navigator.hardwareConcurrency || 4,

      frequency: 20,

      decoder: {
        readers: [
          "ean_reader",
          "ean_8_reader",
          "upc_reader",
          "code_128_reader",
        ],
      },

      locate: true,
    },
    (err) => {
      if (err) {
        showAck("❌ Camera error: " + err.message, false);
        return;
      }

      Quagga.start();
      camRunning = true;
      setCamState(true);

      if (!sessionTimer) startSession();
    },
  );

  Quagga.onDetected(async ({ codeResult }) => {
    if (scanningLocked) return;

    const code = codeResult?.code;

    if (!code) return;

    scanningLocked = true;

    setTimeout(() => {
      scanningLocked = false;
    }, 2000);

    if (seenCodes.has(code)) {
      dupCount++;
      el("footerDups").textContent = dupCount;
      showAck(`⚠️ Already scanned: ${code}`, false);
      return;
    }

    seenCodes.add(code);

    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ barcode: code }),
      });

      const data = await res.json();

      addRow(data);
    } catch (e) {
      showAck("❌ Server error", false);
    }
  });
}

function stopCamera() {
  Quagga.stop();
  camRunning = false;
  setCamState(false);
  socket.emit("stop_scanner");
  clearInterval(sessionTimer);
  sessionTimer = null;
  showAck("📷 Camera stopped. Click Start Camera to resume.", false);
}

// ── Table ────────────────────────────────────────────────────────────────────
function addRow(data) {
  rowCount++;
  el("emptyState").style.display = "none";
  el("productTable").classList.remove("hidden");
  el("countBadge").textContent =
    rowCount + (rowCount === 1 ? " item" : " items");
  el("footerCount").textContent = rowCount;
  showAck(`✅ Scanned: ${data.name}`, true);

  const today = new Date();
  const expired = data.exp_date !== "N/A" && new Date(data.exp_date) < today;
  const badge =
    data.exp_date === "N/A"
      ? `<span class="valid">Unknown</span>`
      : expired
        ? `<span class="expired">Expired</span>`
        : `<span class="valid">Valid</span>`;

  const tr = document.createElement("tr");
  tr.className = "new";
  tr.innerHTML = `
    <td>${rowCount}</td>
    <td class="barcode">${data.barcode}</td>
    <td>${data.name}</td>
    <td>${data.price}</td>
    <td>${data.mfg_date}</td>
    <td>${data.exp_date}</td>
    <td>${data.hsn_code}</td>
    <td>${badge}</td>
    <td>${data.scanned_at || "--"}</td>
  `;
  el("tableBody").prepend(tr);
}

async function clearTable() {
  await fetch("/api/clear", { method: "POST" });
  el("tableBody").innerHTML = "";
  el("productTable").classList.add("hidden");
  el("emptyState").style.display = "block";
  rowCount = 0;
  dupCount = 0;
  seenCodes.clear();
  el("countBadge").textContent = "0 items";
  el("footerCount").textContent = "0";
  el("footerDups").textContent = "0";
}

// ── UI helpers ───────────────────────────────────────────────────────────────
function showAck(msg, ok) {
  clearTimeout(ackTimer);
  const a = el("ack");
  a.textContent = msg;
  a.className = ok ? "success" : "error";
  ackTimer = setTimeout(() => {
    a.className = "";
    a.textContent = "";
  }, 3500);
}

function setCamState(on) {
  el("liveDot").className = "live-dot" + (on ? "" : " off");
  el("camLabel").textContent = on ? "LIVE CAMERA" : "CAMERA OFF";
  el("camOff").className = "cam-off" + (on ? "" : " show");
  el("btnEnd").disabled = !on;
  el("btnStart").classList.toggle("hidden", on);
}

function setStatus(connected) {
  el("statusDot").className = "dot" + (connected ? " live" : " off");
  el("statusText").textContent = connected ? "Connected" : "Disconnected";
}

function startSession() {
  sessionSecs = 0;
  sessionTimer = setInterval(() => {
    sessionSecs++;
    const m = String(Math.floor(sessionSecs / 60)).padStart(2, "0");
    const s = String(sessionSecs % 60).padStart(2, "0");
    el("footerTimer").textContent = `${m}:${s}`;
  }, 1000);
}

async function manualScan() {
  const code = el("manualBarcode").value.trim();

  if (!code) {
    showAck("❌ Please enter barcode number", false);
    return;
  }

  if (seenCodes.has(code)) {
    showAck(`⚠️ Barcode already scanned: ${code}`, false);
    return;
  }

  seenCodes.add(code);

  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ barcode: code }),
    });

    const data = await res.json();

    if (data.duplicate) {
      showAck(`⚠️ Already exists in database: ${code}`, false);
      return;
    }

    addRow(data);
    el("manualBarcode").value = "";
  } catch (e) {
    showAck("❌ Server error while searching barcode", false);
  }
}

const el = (id) => document.getElementById(id);

// ── Auto-start on page load ──────────────────────────────────────────────────
window.addEventListener("load", () => setTimeout(startCamera, 500));
