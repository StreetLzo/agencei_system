/**
 * AGENCEI - QR Code Scanner
 * Utiliza a biblioteca html5-qrcode para leitura de QR Codes
 * 
 * Documentação: https://github.com/mebjas/html5-qrcode
 */

let html5QrcodeScanner = null;
let isScanning = false;

// ==========================================
// 1. INICIALIZAR SCANNER
// ==========================================

function initQRScanner(elementId = 'qr-reader') {
    if (isScanning) {
        console.warn('Scanner já está ativo');
        return;
    }

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
        disableFlip: false,
        videoConstraints: {
            facingMode: "environment" // Câmera traseira
        }
    };

    html5QrcodeScanner = new Html5QrcodeScanner(elementId, config);
    
    html5QrcodeScanner.render(
        onScanSuccess,
        onScanFailure
    );

    isScanning = true;
    console.log('📷 Scanner QR Code inicializado');
}

// ==========================================
// 2. CALLBACKS DE SUCESSO E ERRO
// ==========================================

function onScanSuccess(decodedText, decodedResult) {
    console.log('✅ QR Code detectado:', decodedText);
    
    // Vibrar dispositivo (se suportado)
    if (navigator.vibrate) {
        navigator.vibrate(200);
    }
    
    // Parar scanner
    stopQRScanner();
    
    // Processar QR Code
    processarQRCode(decodedText);
}

function onScanFailure(error) {
    // Não logar erros de "not found" para evitar spam no console
    if (!error.includes('NotFoundException')) {
        console.warn('Scanner:', error);
    }
}

// ==========================================
// 3. PROCESSAR QR CODE
// ==========================================

function processarQRCode(qrCode) {
    // Verificar formato esperado: AGENCEI_XXXXXXXXXXXXXXXX
    if (!qrCode.startsWith('AGENCEI_')) {
        mostrarErro('QR Code inválido. Use apenas QR Codes do sistema AGENCEI.');
        setTimeout(() => {
            initQRScanner();
        }, 3000);
        return;
    }
    
    // Exibir loading
    mostrarLoading('Verificando presença...');
    
    // Enviar para o servidor
    fetch('/aluno/confirmar-presenca-qr', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ qr_code: qrCode })
    })
    .then(response => response.json())
    .then(data => {
        esconderLoading();
        
        if (data.success) {
            mostrarSucesso(data.message);
            
            // Redirecionar após 2 segundos
            setTimeout(() => {
                window.location.href = '/aluno/meus-eventos';
            }, 2000);
        } else {
            mostrarErro(data.message);
            
            // Reiniciar scanner após 3 segundos
            setTimeout(() => {
                initQRScanner();
            }, 3000);
        }
    })
    .catch(error => {
        esconderLoading();
        console.error('Erro:', error);
        mostrarErro('Erro ao processar QR Code. Tente novamente.');
        
        setTimeout(() => {
            initQRScanner();
        }, 3000);
    });
}

// ==========================================
// 4. CONTROLES DO SCANNER
// ==========================================

function stopQRScanner() {
    if (html5QrcodeScanner && isScanning) {
        html5QrcodeScanner.clear().catch(error => {
            console.error('Erro ao parar scanner:', error);
        });
        isScanning = false;
        console.log('🛑 Scanner parado');
    }
}

function pauseQRScanner() {
    if (html5QrcodeScanner && isScanning) {
        html5QrcodeScanner.pause();
        console.log('⏸️ Scanner pausado');
    }
}

function resumeQRScanner() {
    if (html5QrcodeScanner && isScanning) {
        html5QrcodeScanner.resume();
        console.log('▶️ Scanner retomado');
    }
}

// ==========================================
// 5. TROCA DE CÂMERA
// ==========================================

async function trocarCamera() {
    try {
        const cameras = await Html5Qrcode.getCameras();
        
        if (cameras && cameras.length > 1) {
            stopQRScanner();
            
            // Alternar entre frontal e traseira
            const currentMode = html5QrcodeScanner.getState().config.videoConstraints.facingMode;
            const newMode = currentMode === 'environment' ? 'user' : 'environment';
            
            const config = {
                fps: 10,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0,
                disableFlip: false,
                videoConstraints: {
                    facingMode: newMode
                }
            };
            
            html5QrcodeScanner = new Html5QrcodeScanner('qr-reader', config);
            html5QrcodeScanner.render(onScanSuccess, onScanFailure);
            isScanning = true;
            
            mostrarNotificacao('Câmera alternada', 'info');
        } else {
            mostrarNotificacao('Apenas uma câmera disponível', 'warning');
        }
    } catch (error) {
        console.error('Erro ao trocar câmera:', error);
        mostrarErro('Não foi possível alternar a câmera');
    }
}

// ==========================================
// 6. FEEDBACK VISUAL
// ==========================================

function mostrarLoading(mensagem) {
    const loadingDiv = document.getElementById('scan-feedback');
    if (loadingDiv) {
        loadingDiv.innerHTML = `
            <div class="alert alert-info">
                <span class="spinner"></span>
                <span>${mensagem}</span>
            </div>
        `;
    }
}

function esconderLoading() {
    const loadingDiv = document.getElementById('scan-feedback');
    if (loadingDiv) {
        loadingDiv.innerHTML = '';
    }
}

function mostrarSucesso(mensagem) {
    const feedbackDiv = document.getElementById('scan-feedback');
    if (feedbackDiv) {
        feedbackDiv.innerHTML = `
            <div class="alert alert-success">
                <span class="alert-icon">✅</span>
                <span class="alert-message">${mensagem}</span>
            </div>
        `;
    }
}

function mostrarErro(mensagem) {
    const feedbackDiv = document.getElementById('scan-feedback');
    if (feedbackDiv) {
        feedbackDiv.innerHTML = `
            <div class="alert alert-danger">
                <span class="alert-icon">❌</span>
                <span class="alert-message">${mensagem}</span>
            </div>
        `;
    }
}

function mostrarNotificacao(mensagem, tipo) {
    if (window.AGENCEI && window.AGENCEI.mostrarNotificacao) {
        window.AGENCEI.mostrarNotificacao(mensagem, tipo);
    }
}

// ==========================================
// 7. VERIFICAR PERMISSÕES DE CÂMERA
// ==========================================

async function verificarPermissaoCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        stream.getTracks().forEach(track => track.stop());
        return true;
    } catch (error) {
        console.error('Permissão de câmera negada:', error);
        mostrarErro('É necessário permitir o acesso à câmera para escanear QR Codes.');
        return false;
    }
}

// ==========================================
// 8. INICIALIZAÇÃO AUTOMÁTICA
// ==========================================

document.addEventListener('DOMContentLoaded', async function() {
    const qrReaderElement = document.getElementById('qr-reader');
    
    if (qrReaderElement) {
        console.log('📷 Preparando scanner...');
        
        // Verificar permissão
        const temPermissao = await verificarPermissaoCamera();
        
        if (temPermissao) {
            initQRScanner();
        } else {
            // Botão para tentar novamente
            qrReaderElement.innerHTML = `
                <div class="alert alert-warning">
                    <p>Permissão de câmera necessária</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        Tentar Novamente
                    </button>
                </div>
            `;
        }
    }
});

// ==========================================
// 9. CLEANUP AO SAIR DA PÁGINA
// ==========================================

window.addEventListener('beforeunload', function() {
    stopQRScanner();
});

// ==========================================
// 10. EXPORTAR FUNÇÕES GLOBAIS
// ==========================================

window.QRScanner = {
    init: initQRScanner,
    stop: stopQRScanner,
    pause: pauseQRScanner,
    resume: resumeQRScanner,
    trocarCamera: trocarCamera
};

console.log('✅ QR Scanner carregado');