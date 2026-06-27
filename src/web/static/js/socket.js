/**
 * WebSocket连接模块
 */

const SocketManager = {
    socket: null,
    connected: false,
    listeners: {},
    
    init() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.connected = true;
            console.log('WebSocket已连接');
            this.emit('connected');
        });
        
        this.socket.on('disconnect', () => {
            this.connected = false;
            console.log('WebSocket已断开');
            this.emit('disconnected');
        });
        
        this.socket.on('progress_update', (data) => {
            this.emit('progress', data);
        });
        
        this.socket.on('task_complete', (data) => {
            this.emit('complete', data);
        });
        
        this.socket.on('task_error', (data) => {
            this.emit('error', data);
        });
    },
    
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    },
    
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    },
    
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    },
    
    requestProgress(taskId) {
        if (this.connected) {
            this.socket.emit('request_progress', { task_id: taskId });
        }
    },
    
    isConnected() {
        return this.connected;
    }
};

window.SocketManager = SocketManager;