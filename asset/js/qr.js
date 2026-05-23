(function () {
    'use strict';

    var STORE_KEY = 'qr_total_generated';

    function getCount() {
        return parseInt(localStorage.getItem(STORE_KEY) || '0', 10);
    }

    function animateCount(target) {
        var el = document.getElementById('count-total');
        if (target === 0) {
            el.textContent = '0';
            return;
        }
        var dur = 1200, t0 = null;
        function step(ts) {
            if (!t0) t0 = ts;
            var p = Math.min((ts - t0) / dur, 1);
            el.textContent = Math.floor(p * target);
            if (p < 1) requestAnimationFrame(step);
            else el.textContent = target;
        }
        requestAnimationFrame(step);
    }

    function incrementCount() {
        var t = getCount() + 1;
        localStorage.setItem(STORE_KEY, String(t));
        document.getElementById('count-total').textContent = t;
    }

    window.addEventListener('load', function () {
        setTimeout(function () { animateCount(getCount()); }, 700);
    });

    // ── Error helpers ──────────────────────────────────────────────────────────

    function showError(id, msg) {
        var el = document.getElementById(id);
        el.textContent = msg;
        el.classList.add('visible');
    }

    function clearError(id) {
        var el = document.getElementById(id);
        el.textContent = '';
        el.classList.remove('visible');
    }

    // ── Tab switching ──────────────────────────────────────────────────────────

    document.querySelectorAll('.tab-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var tab = this.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(function (x) {
                x.classList.toggle('active', x.dataset.tab === tab);
            });
            document.querySelectorAll('.tab-content').forEach(function (c) {
                c.classList.remove('active');
            });
            document.getElementById('tab-' + tab).classList.add('active');
            hideResult();
        });
    });

    // ── QR generation ─────────────────────────────────────────────────────────

    function generate(payload, btnId, errorId) {
        clearError(errorId);
        var btn = document.getElementById(btnId);
        btn.disabled = true;
        btn.textContent = 'Generating...';

        fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.error) { showError(errorId, data.error); return; }
            showResult(data.image, data.display);
        })
        .catch(function () { showError(errorId, 'Cannot reach server'); })
        .finally(function () {
            btn.disabled = false;
            btn.textContent = 'Generate QR';
        });
    }

    function showResult(imgSrc, metaText) {
        var output = document.getElementById('qr-output');
        output.innerHTML = '';
        var img = document.createElement('img');
        img.src = imgSrc;
        img.width = 300;
        img.height = 300;
        img.alt = 'QR Code';
        output.appendChild(img);

        document.getElementById('qr-meta-value').textContent = metaText;
        incrementCount();

        var result = document.getElementById('qr-result');
        result.style.display = 'block';
        result.classList.add('visible');
        setTimeout(function () {
            result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 120);
    }

    function hideResult() {
        var result = document.getElementById('qr-result');
        result.style.display = 'none';
        result.classList.remove('visible');
        document.getElementById('qr-output').innerHTML = '';
        document.getElementById('qr-meta-value').textContent = '';
    }

    // ── Single Link ────────────────────────────────────────────────────────────

    function generateSingle() {
        var url     = document.getElementById('single-url').value.trim();
        var expires = document.getElementById('single-expires').value || '';
        if (!url) { showError('single-error', 'Please enter a URL.'); return; }
        generate({ mode: 'url', url: url, expires: expires }, 'btn-single', 'single-error');
    }

    document.getElementById('btn-single').addEventListener('click', generateSingle);
    document.getElementById('single-url').addEventListener('keydown', function (e) {
        if (e.key === 'Enter') generateSingle();
    });

    // ── vCard ──────────────────────────────────────────────────────────────────

    function generateVCard() {
        var name    = document.getElementById('vc-name').value.trim();
        var phone   = document.getElementById('vc-phone').value.trim();
        var address = document.getElementById('vc-address').value.trim();
        var website = document.getElementById('vc-website').value.trim();
        var expires = document.getElementById('vcard-expires').value || '';
        if (!name && !phone && !address && !website) {
            showError('vcard-error', 'Please fill in at least one field.');
            return;
        }
        generate(
            { mode: 'vcard', name: name, phone: phone, address: address, website: website, expires: expires },
            'btn-vcard',
            'vcard-error'
        );
    }

    document.getElementById('btn-vcard').addEventListener('click', generateVCard);

    // ── Download PNG ───────────────────────────────────────────────────────────

    document.getElementById('btn-download').addEventListener('click', function () {
        var img = document.querySelector('#qr-output img');
        if (!img) return;
        var a = document.createElement('a');
        a.href = img.src;
        a.download = 'qr-code.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });

})();
