# -*- coding: utf-8 -*-
"""
Flask主应用
"""
import os
from flask import Flask, render_template
from flask_socketio import SocketIO
from loguru import logger

from .config import config
from .utils.task_manager import task_manager


socketio = SocketIO()


def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称（development/production/testing）
        
    Returns:
        Flask应用实例
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(config[config_name])
    
    socketio.init_app(app, async_mode=app.config['SOCKETIO_ASYNC_MODE'])
    
    register_blueprints(app)
    register_socketio_handlers()
    register_error_handlers(app)
    
    logger.info(f"Flask应用已初始化，配置: {config_name}")
    
    return app


def register_blueprints(app):
    """
    注册蓝图
    
    Args:
        app: Flask应用实例
    """
    from .routes.main import main_bp
    from .routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    logger.info("蓝图已注册")


def register_socketio_handlers():
    """注册SocketIO事件处理器"""
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("客户端已连接")
        socketio.emit('connected', {'data': '连接成功'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("客户端已断开连接")
    
    @socketio.on('request_progress')
    def handle_progress_request(data):
        """处理进度请求"""
        task_id = data.get('task_id')
        if task_id:
            task_status = task_manager.get_task_status(task_id)
            if task_status:
                socketio.emit('progress_update', {
                    'task_id': task_id,
                    'progress': task_status['progress'],
                    'status': task_status['status'],
                    'message': task_status.get('message', ''),
                    'current_item': task_status.get('current_item', '')
                })


def register_error_handlers(app):
    """
    注册错误处理器
    
    Args:
        app: Flask应用实例
    """
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"服务器内部错误: {error}")
        return render_template('500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.exception(f"未处理的异常: {error}")
        return render_template('500.html'), 500


def push_progress(task_id, progress, message='', current_item=''):
    """
    推送进度更新
    
    Args:
        task_id: 任务ID
        progress: 进度百分比
        message: 进度消息
        current_item: 当前处理项
    """
    socketio.emit('progress_update', {
        'task_id': task_id,
        'progress': progress,
        'status': 'running',
        'message': message,
        'current_item': current_item
    })


def push_task_complete(task_id, result):
    """
    推送任务完成通知
    
    Args:
        task_id: 任务ID
        result: 任务结果
    """
    socketio.emit('task_complete', {
        'task_id': task_id,
        'status': 'completed',
        'result': result
    })


def push_task_error(task_id, error):
    """
    推送任务错误通知
    
    Args:
        task_id: 任务ID
        error: 错误信息
    """
    socketio.emit('task_error', {
        'task_id': task_id,
        'status': 'failed',
        'error': error
    })


app = create_app()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)