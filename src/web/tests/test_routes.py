# -*- coding: utf-8 -*-
"""
路由测试
"""
import pytest


def test_main_index():
    """测试首页"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        assert '逆向周期行业投资分析系统' in response.data.decode('utf-8')


def test_main_analysis():
    """测试分析页面"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/analysis')
        assert response.status_code == 200


def test_main_history():
    """测试历史页面"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/history')
        assert response.status_code == 200


def test_api_industries():
    """测试行业列表API"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/api/industries')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert isinstance(data['data'], list)


def test_api_stats():
    """测试统计数据API"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/api/stats')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data


def test_api_history():
    """测试历史记录API"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/api/history')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data


def test_api_system():
    """测试系统状态API"""
    from src.web.app import create_app
    
    app = create_app('testing')
    
    with app.test_client() as client:
        response = client.get('/api/system')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])