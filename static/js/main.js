/**
 * AGENCEI - Sistema de Gerenciamento de Eventos
 * Arquivo JavaScript Principal
 */

// ==========================================
// 1. INICIALIZAÇÃO
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 AGENCEI inicializado');
    
    // Inicializar funcionalidades
    initFormValidation();
    initAlerts();
    initCPFMask();
    initDateTimeValidation();
});

// ==========================================
// 2. VALIDAÇÃO DE FORMULÁRIOS
// ==========================================

function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            showFieldError(field, 'Este campo é obrigatório');
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    let errorDiv = field.parentElement.querySelector('.field-error');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        field.parentElement.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentElement.querySelector('.field-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// ==========================================
// 3. MÁSCARA DE CPF
// ==========================================

function initCPFMask() {
    const cpfInputs = document.querySelectorAll('input[name="cpf"]');
    
    cpfInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            // Limitar a 11 dígitos
            if (value.length > 11) {
                value = value.slice(0, 11);
            }
            
            // Aplicar máscara: XXX.XXX.XXX-XX
            if (value.length > 9) {
                value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
            } else if (value.length > 6) {
                value = value.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
            } else if (value.length > 3) {
                value = value.replace(/(\d{3})(\d{1,3})/, '$1.$2');
            }
            
            e.target.value = value;
        });
        
        // Validar CPF ao sair do campo
        input.addEventListener('blur', function(e) {
            const cpf = e.target.value.replace(/\D/g, '');
            
            if (cpf && !validarCPF(cpf)) {
                showFieldError(e.target, 'CPF inválido');
            } else {
                clearFieldError(e.target);
            }
        });
    });
}

function validarCPF(cpf) {
    if (cpf.length !== 11) return false;
    
    // Verificar se todos os dígitos são iguais
    if (/^(\d)\1{10}$/.test(cpf)) return false;
    
    // Validar dígitos verificadores
    let soma = 0;
    let resto;
    
    for (let i = 1; i <= 9; i++) {
        soma += parseInt(cpf.substring(i - 1, i)) * (11 - i);
    }
    
    resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf.substring(9, 10))) return false;
    
    soma = 0;
    for (let i = 1; i <= 10; i++) {
        soma += parseInt(cpf.substring(i - 1, i)) * (12 - i);
    }
    
    resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf.substring(10, 11))) return false;
    
    return true;
}

// ==========================================
// 4. ALERTAS AUTOMÁTICOS
// ==========================================

function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Auto-fechar após 5 segundos
        setTimeout(() => {
            fadeOut(alert);
        }, 5000);
        
        // Botão de fechar
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                fadeOut(alert);
            });
        }
    });
}

function fadeOut(element) {
    element.style.transition = 'opacity 0.3s ease';
    element.style.opacity = '0';
    
    setTimeout(() => {
        element.remove();
    }, 300);
}

// ==========================================
// 5. VALIDAÇÃO DE DATA/HORA
// ==========================================

function initDateTimeValidation() {
    const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
    
    dateInputs.forEach(input => {
        // Definir data mínima como agora
        const now = new Date();
        const minDate = formatDateTimeLocal(now);
        input.min = minDate;
        
        input.addEventListener('change', function(e) {
            const selectedDate = new Date(e.target.value);
            const currentDate = new Date();
            
            if (selectedDate < currentDate) {
                showFieldError(e.target, 'A data não pode ser no passado');
                e.target.value = '';
            } else {
                clearFieldError(e.target);
            }
        });
    });
}

function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// ==========================================
// 6. CONFIRMAÇÕES DE AÇÕES
// ==========================================

function confirmarAcao(mensagem) {
    return confirm(mensagem);
}

// Adicionar confirmação a formulários de exclusão
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'Tem certeza que deseja realizar esta ação?';
            
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});

// ==========================================
// 7. LOADING STATES
// ==========================================

function showLoading(button) {
    button.disabled = true;
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = '<span>Carregando...</span>';
}

function hideLoading(button) {
    button.disabled = false;
    button.innerHTML = button.dataset.originalText;
}

// ==========================================
// 8. COPIAR PARA ÁREA DE TRANSFERÊNCIA
// ==========================================

function copiarParaClipboard(texto) {
    navigator.clipboard.writeText(texto).then(
        () => {
            mostrarNotificacao('Copiado para área de transferência!', 'success');
        },
        () => {
            mostrarNotificacao('Erro ao copiar', 'error');
        }
    );
}

function mostrarNotificacao(mensagem, tipo = 'info') {
    const alertClass = tipo === 'success' ? 'alert-success' : 
                       tipo === 'error' ? 'alert-danger' : 'alert-info';
    
    const alertHTML = `
        <div class="alert ${alertClass}" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <span class="alert-message">${mensagem}</span>
            <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHTML);
    
    // Auto-remover após 3 segundos
    setTimeout(() => {
        const alert = document.querySelector('.alert:last-child');
        if (alert) fadeOut(alert);
    }, 3000);
}

// ==========================================
// 9. FORMATAÇÃO DE DATAS
// ==========================================

function formatarData(dataString) {
    const data = new Date(dataString);
    const dia = String(data.getDate()).padStart(2, '0');
    const mes = String(data.getMonth() + 1).padStart(2, '0');
    const ano = data.getFullYear();
    const horas = String(data.getHours()).padStart(2, '0');
    const minutos = String(data.getMinutes()).padStart(2, '0');
    
    return `${dia}/${mes}/${ano} às ${horas}:${minutos}`;
}

// ==========================================
// 10. UTILS GLOBAIS
// ==========================================

window.AGENCEI = {
    copiarParaClipboard,
    mostrarNotificacao,
    formatarData,
    validarCPF,
    confirmarAcao,
    showLoading,
    hideLoading
};

console.log('✅ AGENCEI carregado com sucesso');