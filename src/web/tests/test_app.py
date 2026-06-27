# -*- coding: utf-8 -*-
"""
Web应用测试
"""
import pytest
from flask import Flask
from flask_socketio import SocketIO


def test_app_creation():
    """测试应用创建"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    assert app is not None
    assert isinstance(app, Flask)
    assert app.config['TESTING'] is True


def test_socketio_initialization():
    """测试SocketIO初始化"""
    from src.web.app import create_app, socketio
    
    app = create_app('testing')
    
    assert socketio is not None
    assert isinstance(socketio, SocketIO)


def test_blueprints_registered():
    """测试蓝图注册"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    assert 'main' in app.blueprints
    assert 'api' in app.blueprints


def test_main_routes():
    """测试主路由"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        
        response = client.get('/analysis')
        assert response.status_code == 200
        
        response = client.get('/history')
        assert response.status_code == 200


def test_api_routes():
    """测试API路由"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/api/industries')
        assert response.status_code == 200
        
        response = client.get('/api/stats')
        assert response.status_code == 200
        
        response = client.get('/api/system')
        assert response.status_code == 200


def test_api_analyze():
    """测试分析API"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.post('/api/analyze', 
                              json={'mode': 'all'},
                              content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'task_id' in data


def test_error_handlers():
    """测试错误处理器"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/nonexistent')
        assert response.status_code == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v'])