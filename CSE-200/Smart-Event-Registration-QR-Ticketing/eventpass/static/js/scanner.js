(() => {
  const root = document.querySelector('.scanner-page');
  if (!root) return;

  const endpoint = root.dataset.checkinUrl;
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const startButton = document.getElementById('start-camera');
  const stopButton = document.getElementById('stop-camera');
  const manualButton = document.getElementById('manual-submit');
  const manualInput = document.getElementById('manual-payload');
  const gateInput = document.getElementById('gate-name');
  const resultBox = document.getElementById('scan-result');
  const cameraBox = document.getElementById('qr-reader');

  let scanner = null;
  let cameraRunning = false;
  let processing = false;
  let feedbackTimer = null;
  let lastDecodedPayload = null;
  let lastDecodedAt = 0;

  function displayResult(result) {
    const state = result?.status || 'invalid';
    const classes = {
      valid: ['scan-valid', '✓', 'Entry approved'],
      duplicate: ['scan-duplicate', '↻', 'Duplicate ticket'],
      invalid: ['scan-invalid', '×', 'Invalid ticket'],
      closed: ['scan-closed', '⏸', 'Gate is closed'],
    };
    const [className, icon, heading] = classes[state] || classes.invalid;
    resultBox.className = `scan-result ${className}`;
    const participant = result?.participant ? `<div class="scan-detail">${escapeHtml(result.participant)} · ${escapeHtml(result.ticket_code || '')}</div>` : '';
    const checked = result?.checked_in_at ? `<div class="scan-detail">Previous check-in: ${escapeHtml(result.checked_in_at)}</div>` : '';
    resultBox.innerHTML = `<div class="result-icon">${icon}</div><h3>${heading}</h3><p>${escapeHtml(result?.message || 'Unable to validate this ticket.')}</p>${participant}${checked}`;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    }[char]));
  }

  async function validatePayload(payload) {
    if (processing) return;
    const clean = String(payload || '').trim();
    if (!clean) {
      displayResult({status: 'invalid', message: 'No QR data was received.'});
      return;
    }
    processing = true;
    if (feedbackTimer) window.clearTimeout(feedbackTimer);
    resultBox.className = 'scan-result scan-idle';
    resultBox.innerHTML = '<div class="result-icon">…</div><h3>Validating ticket</h3><p>Checking ticket status with the event database.</p>';
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
        body: JSON.stringify({qr_payload: clean, gate: gateInput.value.trim() || 'Main Gate'})
      });
      const data = await response.json();
      displayResult(data);
      if (data.status === 'valid') manualInput.value = '';
    } catch (error) {
      displayResult({status: 'invalid', message: 'Could not reach the server. Check the network and try again.'});
    } finally {
      feedbackTimer = window.setTimeout(() => {
        processing = false;
      }, 1700);
    }
  }

  async function stopCamera() {
    if (!scanner || !cameraRunning) return;
    try { await scanner.stop(); } catch (_error) { /* camera may already be stopped */ }
    try { await scanner.clear(); } catch (_error) { /* ignore cleanup errors */ }
    scanner = null;
    cameraRunning = false;
    startButton.disabled = false;
    stopButton.disabled = true;
  }

  async function startCamera() {
    if (cameraRunning) return;
    if (!window.Html5Qrcode) {
      displayResult({status: 'invalid', message: 'Scanner library could not load. Use manual scan or check your internet connection.'});
      return;
    }
    startButton.disabled = true;
    try {
      scanner = new Html5Qrcode('qr-reader');
      const cameras = await Html5Qrcode.getCameras();
      if (!cameras || cameras.length === 0) throw new Error('No camera was found.');
      const preferred = cameras.find((item) => /back|rear|environment/i.test(item.label)) || cameras[0];
      await scanner.start(
        {deviceId: {exact: preferred.id}},
        {fps: 10, qrbox: {width: 245, height: 245}, aspectRatio: 1.0},
        (decodedText) => {
          const now = Date.now();
          if (decodedText === lastDecodedPayload) return;
          lastDecodedPayload = decodedText;
          lastDecodedAt = now;
          validatePayload(decodedText);
        },
        () => {
          if (lastDecodedPayload && Date.now() - lastDecodedAt > 1200) {
            lastDecodedPayload = null;
          }
        }
      );
      cameraRunning = true;
      startButton.disabled = true;
      stopButton.disabled = false;
    } catch (error) {
      scanner = null;
      cameraRunning = false;
      startButton.disabled = false;
      stopButton.disabled = true;
      displayResult({status: 'invalid', message: `${error.message || 'Camera could not start.'} Check browser permission and camera availability.`});
    }
  }

  startButton?.addEventListener('click', startCamera);
  stopButton?.addEventListener('click', stopCamera);
  manualButton?.addEventListener('click', () => validatePayload(manualInput.value));
  manualInput?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) validatePayload(manualInput.value);
  });
  window.addEventListener('beforeunload', () => {
    if (scanner && cameraRunning) scanner.stop().catch(() => {});
  });
})();
