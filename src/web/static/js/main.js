/**
 * 主脚本
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('页面已加载');
    
    SocketManager.init();
    
    SocketManager.on('connected', () => {
        updateConnectionStatus(true);
    });
    
    SocketManager.on('disconnected', () => {
        updateConnectionStatus(false);
    });
});

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (!statusEl) return;
    
    if (connected) {
        statusEl.innerHTML = '<span class="w-2 h-2 bg-green-400 rounded-full mr-1.5"></span>已连接';
        statusEl.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800';
    } else {
        statusEl.innerHTML = '<span class="w-2 h-2 bg-gray-400 rounded-full mr-1.5"></span>未连接';
        statusEl.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800';
    }
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="flex items-center justify-center">
                <div class="loading"></div>
                <span class="ml-2 text-gray-500">加载中...</span>
            </div>
        `;
    }
}

function hideLoading(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}

function formatPercent(value) {
    if (value === null || value === undefined) return '-';
    return value.toFixed(2) + '%';
}

function formatNumber(value) {
    if (value === null || value === undefined) return '-';
    return value.toFixed(2);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

window.updateConnectionStatus = updateConnectionStatus;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.formatDateTime = formatDateTime;
window.formatPercent = formatPercent;
window.formatNumber = formatNumber;
window.debounce = debounce;
window.throttle = throttle;