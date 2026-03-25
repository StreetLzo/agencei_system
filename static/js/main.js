/* ==========================================
   AGENCEI · main.js
   Dark Violet · Brand Edition · v5.1
   ========================================== */

'use strict';

/* ============================================================
   1. RIPPLE — efeito de onda em botões ao clicar
   ============================================================ */
(function initRipple() {
    function createRipple(e) {
        const btn = e.currentTarget;
        const existing = btn.querySelector('.agencei-ripple');
        if (existing) existing.remove();

        const rect   = btn.getBoundingClientRect();
        const size   = Math.max(rect.width, rect.height) * 2;
        const x      = e.clientX - rect.left - size / 2;
        const y      = e.clientY - rect.top  - size / 2;

        const ripple = document.createElement('span');
        ripple.classList.add('agencei-ripple');
        Object.assign(ripple.style, {
            position:     'absolute',
            borderRadius: '50%',
            width:        size + 'px',
            height:       size + 'px',
            left:         x    + 'px',
            top:          y    + 'px',
            background:   'rgba(167, 139, 250, 0.18)',
            transform:    'scale(0)',
            animation:    'agenceiRipple 550ms ease-out forwards',
            pointerEvents:'none',
            zIndex:       '0',
        });

        btn.appendChild(ripple);
        ripple.addEventListener('animationend', () => ripple.remove());
    }

    function attachRipple() {
        document.querySelectorAll('.btn').forEach(btn => {
            if (!btn.dataset.ripple) {
                btn.dataset.ripple = '1';
                btn.addEventListener('click', createRipple);
            }
        });
    }

    // Injeta keyframes uma só vez
    if (!document.getElementById('agencei-ripple-style')) {
        const style = document.createElement('style');
        style.id = 'agencei-ripple-style';
        style.textContent = `
            @keyframes agenceiRipple {
                to { transform: scale(1); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }

    attachRipple();

    // Reaplicar em botões criados dinamicamente
    const mo = new MutationObserver(attachRipple);
    mo.observe(document.body, { childList: true, subtree: true });
})();


/* ============================================================
   2. ALERTS — fechar + auto-dismiss + criação programática
   ============================================================ */
const Alerts = (function () {
    function close(alert) {
        alert.style.transition = 'opacity 200ms ease, transform 200ms ease';
        alert.style.opacity    = '0';
        alert.style.transform  = 'translateY(-6px)';
        setTimeout(() => alert.remove(), 210);
    }

    function init() {
        document.addEventListener('click', e => {
            const btn = e.target.closest('.alert-close');
            if (btn) close(btn.closest('.alert'));
        });
    }

    /**
     * Cria e injeta um alert dinamicamente.
     * @param {string} type    - 'success' | 'danger' | 'warning' | 'info'
     * @param {string} message - Texto do alerta
     * @param {Element|string} container - Seletor ou elemento onde inserir
     * @param {number} [duration] - ms para auto-fechar (0 = manual)
     */
    function show(type, message, container, duration = 4000) {
        const icons = { success: '✓', danger: '✕', warning: '⚠', info: 'ℹ' };
        const wrap   = typeof container === 'string'
            ? document.querySelector(container)
            : container;
        if (!wrap) return;

        const el = document.createElement('div');
        el.className = `alert alert-${type}`;
        el.innerHTML = `
            <span class="alert-icon">${icons[type] ?? 'ℹ'}</span>
            <span>${message}</span>
            <button class="alert-close" aria-label="Fechar">✕</button>
        `;
        wrap.prepend(el);

        if (duration > 0) setTimeout(() => el.isConnected && close(el), duration);
        return el;
    }

    init();
    return { show, close };
})();


/* ============================================================
   3. NAVBAR — scroll shadow + active link
   ============================================================ */
(function initNavbar() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    // Realce ao rolar
    const onScroll = () => {
        const scrolled = window.scrollY > 12;
        navbar.style.background     = scrolled
            ? 'rgba(7, 6, 15, 0.92)'
            : 'rgba(12, 11, 26, 0.82)';
        navbar.style.boxShadow      = scrolled
            ? '0 4px 24px rgba(0,0,0,0.5), 0 0 40px rgba(124,58,237,0.08)'
            : '';
    };

    window.addEventListener('scroll', onScroll, { passive: true });

    // Marcar link ativo pela URL
    const path = location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href') || '';
        if (href && path.startsWith(href) && href !== '/') {
            link.style.color      = 'var(--violet-light)';
            link.style.background = 'var(--violet-faint)';
        }
    });
})();


/* ============================================================
   4. TABLES — ordenação client-side + highlight da célula clicada
   ============================================================ */
(function initTables() {
    document.querySelectorAll('.table').forEach(table => {
        const headers = table.querySelectorAll('thead th');

        headers.forEach((th, colIndex) => {
            th.style.cursor = 'pointer';
            th.title = 'Clique para ordenar';
            let asc = true;

            th.addEventListener('click', () => {
                const tbody = table.querySelector('tbody');
                if (!tbody) return;

                const rows = [...tbody.querySelectorAll('tr')];

                rows.sort((a, b) => {
                    const ta = a.cells[colIndex]?.textContent.trim() ?? '';
                    const tb = b.cells[colIndex]?.textContent.trim() ?? '';
                    const na = parseFloat(ta.replace(/[^\d.-]/g, ''));
                    const nb = parseFloat(tb.replace(/[^\d.-]/g, ''));
                    if (!isNaN(na) && !isNaN(nb)) return asc ? na - nb : nb - na;
                    return asc ? ta.localeCompare(tb, 'pt-BR') : tb.localeCompare(ta, 'pt-BR');
                });

                asc = !asc;

                // ícone de seta
                headers.forEach(h => { h.dataset.sort = ''; });
                th.dataset.sort = asc ? 'desc' : 'asc';

                rows.forEach(r => tbody.appendChild(r));

                // flash roxo nas células da coluna
                rows.forEach(r => {
                    const cell = r.cells[colIndex];
                    if (!cell) return;
                    cell.style.transition = 'background 0ms';
                    cell.style.background = 'rgba(124,58,237,0.12)';
                    requestAnimationFrame(() => {
                        cell.style.transition = 'background 500ms ease';
                        cell.style.background = '';
                    });
                });
            });
        });

        // Injetar indicadores via CSS uma vez
        if (!document.getElementById('agencei-table-sort-style')) {
            const s = document.createElement('style');
            s.id = 'agencei-table-sort-style';
            s.textContent = `
                .table th[data-sort="asc"]::after  { content: ' ↑'; color: var(--violet-light); }
                .table th[data-sort="desc"]::after { content: ' ↓'; color: var(--violet-light); }
            `;
            document.head.appendChild(s);
        }
    });
})();


/* ============================================================
   5. PROGRESS BARS — animar ao entrar na viewport
   ============================================================ */
(function initProgressBars() {
    const bars = document.querySelectorAll('.progress-bar');
    if (!bars.length) return;

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const bar = entry.target;
            // Resetar e re-disparar
            bar.style.animation = 'none';
            void bar.offsetWidth; // reflow
            bar.style.animation = '';
            bar.classList.add('animated-progress');
            observer.unobserve(bar);
        });
    }, { threshold: 0.2 });

    bars.forEach(bar => observer.observe(bar));
})();


/* ============================================================
   6. FORM VALIDATION — feedback visual inline
   ============================================================ */
(function initForms() {
    // Injeta estilos de estado uma vez
    if (!document.getElementById('agencei-form-style')) {
        const s = document.createElement('style');
        s.id = 'agencei-form-style';
        s.textContent = `
            .form-control.is-invalid {
                border-color: var(--danger) !important;
                box-shadow: 0 0 0 3px var(--danger-bg) !important;
            }
            .form-control.is-valid {
                border-color: var(--success) !important;
                box-shadow: 0 0 0 3px var(--success-bg) !important;
            }
            .field-msg {
                font-size: 0.75rem;
                margin-top: 0.3rem;
                font-weight: 500;
                opacity: 0;
                transform: translateY(-4px);
                transition: opacity 180ms ease, transform 180ms ease;
            }
            .field-msg.visible { opacity: 1; transform: translateY(0); }
            .field-msg.error   { color: var(--danger); }
            .field-msg.ok      { color: var(--success); }
        `;
        document.head.appendChild(s);
    }

    function getOrCreateMsg(input) {
        let msg = input.parentElement.querySelector('.field-msg');
        if (!msg) {
            msg = document.createElement('p');
            msg.className = 'field-msg';
            input.after(msg);
        }
        return msg;
    }

    function validate(input) {
        const msg = getOrCreateMsg(input);
        input.classList.remove('is-invalid', 'is-valid');
        msg.classList.remove('visible', 'error', 'ok');

        if (!input.value.trim() && input.required) {
            input.classList.add('is-invalid');
            msg.textContent = 'Este campo é obrigatório.';
            msg.classList.add('visible', 'error');
            return false;
        }

        if (input.type === 'email' && input.value) {
            const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value);
            if (!valid) {
                input.classList.add('is-invalid');
                msg.textContent = 'Informe um e-mail válido.';
                msg.classList.add('visible', 'error');
                return false;
            }
        }

        if (input.value.trim()) {
            input.classList.add('is-valid');
            msg.textContent = '✓';
            msg.classList.add('visible', 'ok');
        }

        return true;
    }

    document.addEventListener('blur', e => {
        if (e.target.matches('.form-control')) validate(e.target);
    }, true);

    document.addEventListener('input', e => {
        if (e.target.matches('.form-control.is-invalid')) validate(e.target);
    });
})();


/* ============================================================
   7. TOAST NOTIFICATIONS — sistema global window.toast
   ============================================================ */
(function initToast() {
    const COLORS = {
        success: { bg: 'var(--success-bg)',  border: 'var(--success)',       icon: '✓', glow: 'rgba(52,211,153,0.2)' },
        error:   { bg: 'var(--danger-bg)',   border: 'var(--danger)',        icon: '✕', glow: 'rgba(248,113,113,0.2)' },
        warning: { bg: 'var(--warning-bg)',  border: 'var(--warning)',       icon: '⚠', glow: 'rgba(251,191,36,0.2)' },
        info:    { bg: 'var(--violet-faint)',border: 'var(--violet)',        icon: 'ℹ', glow: 'rgba(124,58,237,0.22)' },
    };

    // Injetar estilos
    if (!document.getElementById('agencei-toast-style')) {
        const s = document.createElement('style');
        s.id = 'agencei-toast-style';
        s.textContent = `
            #agencei-toaster {
                position: fixed;
                bottom: 1.5rem;
                right: 1.5rem;
                display: flex;
                flex-direction: column;
                gap: 0.6rem;
                z-index: 9999;
                pointer-events: none;
            }
            .agencei-toast {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.75rem 1.1rem;
                border-radius: 12px;
                border: 1px solid;
                font-family: var(--font-body, sans-serif);
                font-size: 0.875rem;
                font-weight: 500;
                min-width: 240px;
                max-width: 360px;
                pointer-events: all;
                backdrop-filter: blur(12px);
                transform: translateX(110%);
                opacity: 0;
                transition: transform 300ms cubic-bezier(0.22,1,0.36,1),
                            opacity 300ms ease;
                cursor: default;
            }
            .agencei-toast.show { transform: translateX(0); opacity: 1; }
            .agencei-toast.hide { transform: translateX(110%); opacity: 0; }
            .agencei-toast-icon { font-size: 1rem; flex-shrink: 0; }
            .agencei-toast-msg  { flex: 1; }
            .agencei-toast-close {
                background: none; border: none; cursor: pointer;
                color: inherit; opacity: 0.45; font-size: 0.9rem;
                padding: 0 2px; transition: opacity 120ms;
                flex-shrink: 0;
            }
            .agencei-toast-close:hover { opacity: 1; }
            .agencei-toast-bar {
                position: absolute; bottom: 0; left: 0;
                height: 2px; border-radius: 0 0 12px 12px;
                animation: toastBar linear forwards;
            }
            @keyframes toastBar { from { width: 100%; } to { width: 0%; } }
        `;
        document.head.appendChild(s);
    }

    let toaster = document.getElementById('agencei-toaster');
    if (!toaster) {
        toaster = document.createElement('div');
        toaster.id = 'agencei-toaster';
        document.body.appendChild(toaster);
    }

    /**
     * Dispara um toast.
     * @param {string} message
     * @param {'success'|'error'|'warning'|'info'} [type='info']
     * @param {number} [duration=3500]
     */
    function toast(message, type = 'info', duration = 3500) {
        const cfg = COLORS[type] ?? COLORS.info;

        const el = document.createElement('div');
        el.className = 'agencei-toast';
        Object.assign(el.style, {
            background:  cfg.bg,
            borderColor: cfg.border,
            color:       type === 'warning' ? '#fff' : '',
            boxShadow:   `0 4px 24px ${cfg.glow}, 0 2px 8px rgba(0,0,0,0.4)`,
            position:    'relative',
            overflow:    'hidden',
        });
        el.innerHTML = `
            <span class="agencei-toast-icon">${cfg.icon}</span>
            <span class="agencei-toast-msg">${message}</span>
            <button class="agencei-toast-close" aria-label="Fechar">✕</button>
            <div class="agencei-toast-bar" style="background:${cfg.border}; animation-duration:${duration}ms;"></div>
        `;

        toaster.appendChild(el);
        requestAnimationFrame(() => {
            requestAnimationFrame(() => el.classList.add('show'));
        });

        const dismiss = () => {
            el.classList.add('hide');
            setTimeout(() => el.remove(), 320);
        };

        el.querySelector('.agencei-toast-close').addEventListener('click', dismiss);
        if (duration > 0) setTimeout(dismiss, duration);
    }

    window.toast = toast;
})();


/* ============================================================
   8. MODAL — abrir/fechar com animação + foco preso
   ============================================================ */
const Modal = (function () {
    if (!document.getElementById('agencei-modal-style')) {
        const s = document.createElement('style');
        s.id = 'agencei-modal-style';
        s.textContent = `
            .agencei-overlay {
                position: fixed; inset: 0; z-index: 1000;
                background: rgba(7,6,15,0.75);
                backdrop-filter: blur(6px);
                display: flex; align-items: center; justify-content: center;
                padding: 1.5rem;
                opacity: 0;
                transition: opacity 260ms ease;
            }
            .agencei-overlay.open { opacity: 1; }
            .agencei-modal {
                background: var(--surface);
                border: 1px solid var(--rim-2);
                border-radius: var(--r-2xl, 32px);
                box-shadow: 0 20px 70px rgba(0,0,0,0.75), 0 0 40px rgba(124,58,237,0.15);
                padding: 2rem;
                width: 100%; max-width: 520px; max-height: 90vh;
                overflow-y: auto;
                position: relative;
                transform: translateY(20px) scale(0.97);
                transition: transform 280ms cubic-bezier(0.22,1,0.36,1);
            }
            .agencei-modal::before {
                content: '';
                position: absolute; top: 0; left: 0; right: 0; height: 1px;
                background: linear-gradient(135deg, #6D28D9 0%, #7C3AED 45%, #D946EF 100%);
                border-radius: var(--r-2xl, 32px) var(--r-2xl, 32px) 0 0;
                opacity: 0.65;
            }
            .agencei-overlay.open .agencei-modal { transform: translateY(0) scale(1); }
            .agencei-modal-header {
                display: flex; align-items: center;
                justify-content: space-between; margin-bottom: 1.25rem;
            }
            .agencei-modal-title {
                font-family: var(--font-display, sans-serif);
                font-weight: 800; font-size: 1.1rem;
                color: var(--text-primary, #EDE9FF);
                letter-spacing: -0.03em;
            }
            .agencei-modal-close {
                background: none; border: none; cursor: pointer;
                color: var(--text-muted, #5C5480); font-size: 1.2rem;
                width: 32px; height: 32px;
                display: flex; align-items: center; justify-content: center;
                border-radius: 8px;
                transition: background 150ms, color 150ms, transform 150ms;
            }
            .agencei-modal-close:hover {
                background: rgba(124,58,237,0.1);
                color: var(--violet-light, #A78BFA);
                transform: rotate(90deg);
            }
        `;
        document.head.appendChild(s);
    }

    let activeOverlay = null;

    function open({ title = '', content = '', onConfirm = null, confirmText = 'Confirmar', confirmType = 'primary' } = {}) {
        if (activeOverlay) close();

        const overlay = document.createElement('div');
        overlay.className = 'agencei-overlay';
        overlay.innerHTML = `
            <div class="agencei-modal" role="dialog" aria-modal="true" aria-label="${title}">
                <div class="agencei-modal-header">
                    <span class="agencei-modal-title">${title}</span>
                    <button class="agencei-modal-close" aria-label="Fechar">✕</button>
                </div>
                <div class="agencei-modal-body">${content}</div>
                ${onConfirm ? `
                <div style="display:flex;gap:.75rem;justify-content:flex-end;margin-top:1.5rem">
                    <button class="btn btn-outline agencei-modal-cancel">Cancelar</button>
                    <button class="btn btn-${confirmType} agencei-modal-confirm">${confirmText}</button>
                </div>` : ''}
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.style.overflow = 'hidden';
        activeOverlay = overlay;

        requestAnimationFrame(() => {
            requestAnimationFrame(() => overlay.classList.add('open'));
        });

        // Fechar no X
        overlay.querySelector('.agencei-modal-close')
            .addEventListener('click', close);

        // Fechar no overlay
        overlay.addEventListener('click', e => {
            if (e.target === overlay) close();
        });

        // Cancelar
        overlay.querySelector('.agencei-modal-cancel')
            ?.addEventListener('click', close);

        // Confirmar
        overlay.querySelector('.agencei-modal-confirm')
            ?.addEventListener('click', () => { onConfirm?.(); close(); });

        // ESC
        const onKey = e => { if (e.key === 'Escape') close(); };
        document.addEventListener('keydown', onKey);
        overlay._removeKey = () => document.removeEventListener('keydown', onKey);

        return overlay;
    }

    function close() {
        if (!activeOverlay) return;
        activeOverlay.classList.remove('open');
        activeOverlay._removeKey?.();
        const el = activeOverlay;
        activeOverlay = null;
        document.body.style.overflow = '';
        setTimeout(() => el.remove(), 280);
    }

    return { open, close };
})();


/* ============================================================
   9. GLOW CURSOR — rastro roxo sutil no mouse
   ============================================================ */
(function initGlowCursor() {
    const isMobile = window.matchMedia('(pointer: coarse)').matches;
    if (isMobile) return;

    const dot = document.createElement('div');
    Object.assign(dot.style, {
        position:        'fixed',
        width:           '10px',
        height:          '10px',
        borderRadius:    '50%',
        background:      'rgba(124,58,237,0.7)',
        boxShadow:       '0 0 12px 4px rgba(124,58,237,0.35)',
        pointerEvents:   'none',
        zIndex:          '99999',
        transform:       'translate(-50%,-50%)',
        transition:      'width 150ms ease, height 150ms ease, opacity 150ms ease',
        mixBlendMode:    'screen',
    });

    document.body.appendChild(dot);

    let cx = 0, cy = 0, tx = 0, ty = 0;
    let raf;

    window.addEventListener('mousemove', e => { tx = e.clientX; ty = e.clientY; });

    function loop() {
        cx += (tx - cx) * 0.18;
        cy += (ty - cy) * 0.18;
        dot.style.left = cx + 'px';
        dot.style.top  = cy + 'px';
        raf = requestAnimationFrame(loop);
    }

    loop();

    // Engrandecer ao passar em elementos interativos
    document.addEventListener('mouseover', e => {
        if (e.target.closest('a, button, .btn, .nav-link, .card, input, select, textarea')) {
            Object.assign(dot.style, { width: '20px', height: '20px', opacity: '0.5' });
        } else {
            Object.assign(dot.style, { width: '10px', height: '10px', opacity: '1' });
        }
    });

    // Sumir quando sair da janela
    document.addEventListener('mouseleave', () => { dot.style.opacity = '0'; });
    document.addEventListener('mouseenter', () => { dot.style.opacity = '1'; });
})();


/* ============================================================
   10. SCROLL REVEAL — animar elementos ao entrar na tela
   ============================================================ */
(function initScrollReveal() {
    if (!document.getElementById('agencei-reveal-style')) {
        const s = document.createElement('style');
        s.id = 'agencei-reveal-style';
        s.textContent = `
            [data-reveal] {
                opacity: 0;
                transform: translateY(20px);
                transition: opacity 500ms ease, transform 500ms cubic-bezier(0.22,1,0.36,1);
            }
            [data-reveal].revealed {
                opacity: 1;
                transform: translateY(0);
            }
        `;
        document.head.appendChild(s);
    }

    const io = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el    = entry.target;
            const delay = el.dataset.revealDelay || '0';
            el.style.transitionDelay = delay + 'ms';
            el.classList.add('revealed');
            io.unobserve(el);
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('[data-reveal]').forEach(el => io.observe(el));
})();


/* ============================================================
   11. CONFIRM DELETE — intercepta botões .btn-danger com data-confirm
   ============================================================ */
(function initConfirmDelete() {
    document.addEventListener('click', e => {
        const btn = e.target.closest('[data-confirm]');
        if (!btn) return;
        e.preventDefault();
        e.stopPropagation();

        const msg  = btn.dataset.confirm || 'Tem certeza que deseja continuar?';
        const form = btn.closest('form');

        Modal.open({
            title:       'Confirmar ação',
            content:     `<p style="color:var(--text-secondary);line-height:1.6">${msg}</p>`,
            confirmText: 'Confirmar',
            confirmType: 'danger',
            onConfirm:   () => {
                if (form) { form.submit(); return; }
                const href = btn.getAttribute('href');
                if (href) location.href = href;
            },
        });
    });
})();


/* ============================================================
   12. COPY TO CLIPBOARD — data-copy="texto"
   ============================================================ */
(function initCopy() {
    document.addEventListener('click', async e => {
        const el = e.target.closest('[data-copy]');
        if (!el) return;

        const text = el.dataset.copy || el.textContent.trim();
        try {
            await navigator.clipboard.writeText(text);
            window.toast?.('Copiado!', 'success', 2000);
        } catch {
            window.toast?.('Não foi possível copiar.', 'error', 2500);
        }
    });
})();


/* ============================================================
   EXPORTS — API pública
   ============================================================ */
window.AGENCEI = {
    Alerts,
    Modal,
    toast: window.toast,
};

/*
   ┌─────────────────────────────────────────────┐
   │  USO RÁPIDO                                 │
   │                                             │
   │  // Toast                                   │
   │  toast('Evento criado!', 'success');         │
   │                                             │
   │  // Modal de confirmação                    │
   │  AGENCEI.Modal.open({                       │
   │    title: 'Excluir evento',                 │
   │    content: 'Isso não pode ser desfeito.',  │
   │    confirmText: 'Excluir',                  │
   │    confirmType: 'danger',                   │
   │    onConfirm: () => { ... }                 │
   │  });                                        │
   │                                             │
   │  // Confirm automático via HTML:            │
   │  <button data-confirm="Excluir evento?">   │
   │                                             │
   │  // Copy via HTML:                          │
   │  <span data-copy="texto-a-copiar">          │
   │                                             │
   │  // Scroll reveal via HTML:                 │
   │  <div data-reveal data-reveal-delay="100">  │
   └─────────────────────────────────────────────┘
*/