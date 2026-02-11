(function initQrScannerModule() {
    function setStatus(statusEl, message, kind) {
        if (!statusEl) {
            return;
        }
        statusEl.textContent = message;
        statusEl.classList.remove('ok', 'error');
        if (kind === 'ok' || kind === 'error') {
            statusEl.classList.add(kind);
        }
    }

    function normalizeCode(value) {
        return String(value || '').trim();
    }

    window.SteppeQrScanner = {
        init: function init(options) {
            var cfg = options || {};
            var inputEl = document.getElementById(cfg.inputId);
            var readerEl = document.getElementById(cfg.readerId);
            var startBtn = document.getElementById(cfg.startButtonId);
            var stopBtn = document.getElementById(cfg.stopButtonId);
            var imageInput = document.getElementById(cfg.imageInputId);
            var statusEl = document.getElementById(cfg.statusId);

            if (!inputEl || !readerEl || !startBtn || !stopBtn || !imageInput || !statusEl) {
                return;
            }

            if (!window.Html5Qrcode) {
                setStatus(
                    statusEl,
                    'Сканер не загрузился. Проверьте подключение к интернету или введите номер вручную.',
                    'error'
                );
                startBtn.disabled = true;
                return;
            }

            var scanner = new window.Html5Qrcode(readerEl.id);
            var isRunning = false;
            var shellEl = readerEl.closest('.qr-viewfinder-shell');

            function setIdleUi() {
                readerEl.classList.add('d-none');
                startBtn.classList.remove('d-none');
                stopBtn.classList.add('d-none');
                startBtn.disabled = false;
                if (shellEl) {
                    shellEl.classList.remove('is-scanning');
                }
            }

            function setScanningUi() {
                readerEl.classList.remove('d-none');
                startBtn.classList.add('d-none');
                stopBtn.classList.remove('d-none');
                if (shellEl) {
                    shellEl.classList.add('is-scanning');
                }
            }

            function applyCode(raw) {
                var code = normalizeCode(raw);
                if (!code) {
                    return;
                }
                inputEl.value = code;
                inputEl.dispatchEvent(new Event('input', { bubbles: true }));
                inputEl.dispatchEvent(new Event('change', { bubbles: true }));
                inputEl.focus();
                setStatus(statusEl, 'QR найден: ' + code, 'ok');
            }

            function stopScanner() {
                if (!isRunning) {
                    setIdleUi();
                    return Promise.resolve();
                }
                return scanner.stop().then(function () {
                    isRunning = false;
                    setIdleUi();
                    setStatus(statusEl, 'Камера остановлена.', null);
                }).catch(function () {
                    isRunning = false;
                    setIdleUi();
                });
            }

            startBtn.addEventListener('click', function () {
                if (isRunning) {
                    return;
                }
                setStatus(statusEl, 'Запрос доступа к камере...', null);
                setScanningUi();

                scanner.start(
                    { facingMode: 'environment' },
                    { fps: 10, qrbox: { width: 250, height: 250 } },
                    function onScanSuccess(decodedText) {
                        applyCode(decodedText);
                        stopScanner();
                    },
                    function onScanError() {
                        // Ignored: frequent callback while scanning.
                    }
                ).then(function () {
                    isRunning = true;
                    setStatus(statusEl, 'Наведите камеру на QR-код.', null);
                }).catch(function (err) {
                    setIdleUi();
                    setStatus(
                        statusEl,
                        'Не удалось запустить камеру: ' + (err && err.message ? err.message : err),
                        'error'
                    );
                });
            });

            stopBtn.addEventListener('click', function () {
                stopScanner();
            });

            imageInput.addEventListener('change', function (event) {
                var file = event.target.files && event.target.files[0];
                if (!file) {
                    return;
                }
                setStatus(statusEl, 'Распознаю QR на изображении...', null);
                stopScanner().then(function () {
                    scanner.scanFile(file, true).then(function (decodedText) {
                        applyCode(decodedText);
                    }).catch(function (err) {
                        setStatus(
                            statusEl,
                            'QR на изображении не найден: ' + (err && err.message ? err.message : err),
                            'error'
                        );
                    }).finally(function () {
                        imageInput.value = '';
                    });
                });
            });

            setIdleUi();
        }
    };
})();
