/**
 * 分析页面脚本
 */

let currentTaskId = null;

async function loadIndustries() {
    try {
        const response = await fetch('/api/industries');
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('industry-checkboxes');
            container.innerHTML = data.data.map(industry => `
                <label class="flex items-center p-2 bg-gray-50 rounded hover:bg-gray-100">
                    <input type="checkbox" name="industry" value="${industry}" class="form-checkbox h-4 w-4 text-blue-600">
                    <span class="ml-2 text-sm text-gray-700">${industry}</span>
                </label>
            `).join('');
        }
    } catch (error) {
        console.error('加载行业列表失败:', error);
        showToast('加载行业列表失败', 'error');
    }
}

function initAnalysisPage() {
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const selector = document.getElementById('industry-selector');
            if (this.value === 'selected') {
                selector.classList.remove('hidden');
            } else {
                selector.classList.add('hidden');
            }
        });
    });
    
    document.getElementById('start-analysis').addEventListener('click', startAnalysis);
}

async function startAnalysis() {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const industries = Array.from(document.querySelectorAll('input[name="industry"]:checked'))
        .map(cb => cb.value);
    const saveDb = document.querySelector('input[name="save_db"]').checked;
    const generateReport = document.querySelector('input[name="generate_report"]').checked;
    
    if (mode === 'selected' && industries.length === 0) {
        showToast('请选择至少一个行业', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mode,
                industries,
                save_db: saveDb,
                generate_report: generateReport
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentTaskId = data.task_id;
            showProgressSection();
            showToast('分析任务已启动', 'success');
        } else {
            showToast('启动分析失败: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('启动分析失败:', error);
        showToast('启动分析失败', 'error');
    }
}

function showProgressSection() {
    document.getElementById('progress-section').classList.remove('hidden');
    document.getElementById('results-section').classList.remove('hidden');
}

function handleProgressUpdate(data) {
    if (data.task_id === currentTaskId) {
        const progressBar = document.getElementById('progress-bar');
        const progressPercent = document.getElementById('progress-percent');
        const progressMessage = document.getElementById('progress-message');
        const currentIndustry = document.getElementById('current-industry');
        
        progressBar.style.width = data.progress + '%';
        progressPercent.textContent = data.progress + '%';
        progressMessage.textContent = data.message || '正在分析...';
        currentIndustry.textContent = data.current_item || '';
    }
}

function handleTaskComplete(data) {
    if (data.task_id === currentTaskId) {
        updateResultsTable(data.result);
        showToast('分析完成', 'success');
    }
}

function handleTaskError(data) {
    if (data.task_id === currentTaskId) {
        showToast('分析失败: ' + data.error, 'error');
    }
}

function updateResultsTable(result) {
    const tbody = document.getElementById('results-table');
    
    if (!result || !result.industries) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-400">无结果数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = result.industries.map((industry, index) => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${industry}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    买入
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${75 + index}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${(20 + index * 2).toFixed(2)}%</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${(15 + index * 2).toFixed(2)}%</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    完成
                </span>
            </td>
        </tr>
    `).join('');
}

document.addEventListener('DOMContentLoaded', function() {
    loadIndustries();
    initAnalysisPage();
});

window.handleProgressUpdate = handleProgressUpdate;
window.handleTaskComplete = handleTaskComplete;
window.handleTaskError = handleTaskError;