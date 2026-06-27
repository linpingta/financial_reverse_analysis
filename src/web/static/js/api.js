/**
 * API调用模块
 */

const API = {
    baseUrl: '/api',
    
    async request(endpoint, options = {}) {
        const url = this.baseUrl + endpoint;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || '请求失败');
            }
            
            return data;
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    },
    
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },
    
    async getIndustries() {
        return this.get('/industries');
    },
    
    async startAnalyze(mode, industries = [], saveDb = true, generateReport = false) {
        return this.post('/analyze', {
            mode,
            industries,
            save_db: saveDb,
            generate_report: generateReport
        });
    },
    
    async getAnalyzeStatus(taskId) {
        return this.get(`/analyze/status/${taskId}`);
    },
    
    async getAnalyzeResult(taskId) {
        return this.get(`/analyze/result/${taskId}`);
    },
    
    async getHistory(params = {}) {
        const queryString = Object.entries(params)
            .filter(([key, value]) => value !== undefined && value !== null)
            .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
            .join('&');
        
        return this.get(`/history?${queryString}`);
    },
    
    async getHistoryDetail(id) {
        return this.get(`/history/${id}`);
    },
    
    async getStats() {
        return this.get('/stats');
    },
    
    async createExport(format, filters = {}) {
        return this.post('/export', {
            format,
            filters
        });
    },
    
    async getSystemStatus() {
        return this.get('/system');
    }
};

window.API = API;